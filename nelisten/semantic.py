from __future__ import annotations

from datetime import datetime, timezone
import math
import random
from typing import Any

from .textmining import clean_lyric, song_weights, tokenize


DEFAULT_MODEL = "intfloat/multilingual-e5-small"
DEFAULT_REVISION = "f470c6a1a906014160ece1968c484b275f0396de"


def unavailable(reason: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    return {
        "schemaVersion": "semantic-v1",
        "available": False,
        "reason": reason,
        "model": {"name": model},
        "safety": {
            "containsLyrics": False,
            "containsSongIds": False,
            "containsEmbeddings": False,
        },
    }


def _chunks(text: str, lines_per_chunk: int = 8) -> list[str]:
    lines = [line.strip() for line in clean_lyric(text).splitlines() if line.strip()]
    if not lines:
        return []
    return ["\n".join(lines[i:i + lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]


def _cluster_terms(
    ids: list[str],
    labels: Any,
    docs: dict[str, str],
    weights: dict[str, float],
    k: int,
    limit: int = 8,
) -> list[dict[str, Any]]:
    from collections import Counter

    cluster_tf: list[Counter[str]] = [Counter() for _ in range(k)]
    cluster_docs: list[int] = [0 for _ in range(k)]
    cluster_weight = [0.0 for _ in range(k)]
    df = Counter()

    tokenized: dict[str, list[str]] = {}
    for sid in ids:
        tokens = tokenize(docs[sid])
        tokenized[sid] = tokens
        df.update(set(tokens))

    for sid, label in zip(ids, labels):
        label = int(label)
        tokens = tokenized.get(sid) or []
        if not tokens:
            continue
        cluster_docs[label] += 1
        w = max(0.01, float(weights.get(sid, 1.0)))
        cluster_weight[label] += w
        counts = Counter(tokens)
        for term, count in counts.items():
            cluster_tf[label][term] += count * w

    total_weight = sum(cluster_weight) or 1.0
    rows = []
    for label in range(k):
        total = sum(cluster_tf[label].values()) or 1.0
        scored = []
        for term, count in cluster_tf[label].items():
            if len(term.strip()) < 2:
                continue
            idf = math.log((1 + k) / (1 + sum(1 for c in cluster_tf if term in c))) + 1
            scored.append((term, (count / total) * idf))
        scored.sort(key=lambda x: x[1], reverse=True)
        terms = [term for term, _ in scored[:limit]]
        rows.append({
            "id": label,
            "label": " / ".join(terms[:3]) if terms else f"Cluster {label + 1}",
            "terms": terms,
            "documents": cluster_docs[label],
            "prevalence": round(cluster_weight[label] / total_weight * 100, 1),
        })
    rows.sort(key=lambda x: x["prevalence"], reverse=True)
    return rows


def analyze_semantic(
    data: dict[str, Any],
    model_name: str = DEFAULT_MODEL,
    revision: str = DEFAULT_REVISION,
    min_k: int = 3,
    max_k: int = 9,
) -> dict[str, Any]:
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
        from sklearn.cluster import KMeans
        from sklearn.metrics import adjusted_mutual_info_score, silhouette_score
    except ImportError:
        return unavailable("install ne-listen[semantic] to enable multilingual embedding analysis", model_name)

    lyrics = data.get("lyrics") or {}
    if not isinstance(lyrics, dict):
        return unavailable("no lyric corpus available", model_name)

    docs: dict[str, str] = {}
    chunk_owner: list[str] = []
    chunk_texts: list[str] = []
    for sid, raw in lyrics.items():
        if not isinstance(raw, str):
            continue
        cleaned = clean_lyric(raw)
        if not cleaned:
            continue
        chunks = _chunks(cleaned)
        if not chunks:
            continue
        sid = str(sid)
        docs[sid] = cleaned
        for chunk in chunks:
            chunk_owner.append(sid)
            chunk_texts.append("passage: " + chunk)

    if len(docs) < 30:
        return unavailable("at least 30 usable lyric documents are required", model_name)

    model = SentenceTransformer(model_name, revision=revision)
    chunk_embeddings = model.encode(
        chunk_texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    ids = list(docs)
    by_song: dict[str, list[Any]] = {sid: [] for sid in ids}
    for sid, emb in zip(chunk_owner, chunk_embeddings):
        by_song[sid].append(emb)

    vectors = []
    for sid in ids:
        arr = np.vstack(by_song[sid])
        vec = arr.mean(axis=0)
        norm = np.linalg.norm(vec)
        vectors.append(vec / norm if norm else vec)
    X = np.vstack(vectors)

    upper = min(max_k, max(min_k, len(ids) // 15), len(ids) - 1)
    lower = min(min_k, upper)
    candidates = []
    for k in range(lower, upper + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = km.fit_predict(X)
        score = silhouette_score(X, labels, metric="cosine") if len(set(labels)) > 1 else -1.0
        candidates.append((k, float(score), km, labels))
    k, silhouette, baseline, labels = max(candidates, key=lambda row: row[1])

    seed_scores = []
    n = len(ids)
    sample_n = max(k * 3, int(n * 0.85))
    for seed in (13, 29, 47, 71, 97, 113):
        rng = random.Random(seed)
        chosen = sorted(rng.sample(range(n), min(n, sample_n)))
        km = KMeans(n_clusters=k, random_state=seed, n_init=10)
        km.fit(X[chosen])
        predicted = km.predict(X)
        seed_scores.append(adjusted_mutual_info_score(labels, predicted))
    stability = sum(seed_scores) / len(seed_scores)

    weights = song_weights(data)
    clusters = _cluster_terms(ids, labels, docs, weights, k)

    global_centroid = np.average(
        X,
        axis=0,
        weights=np.array([max(0.01, weights.get(sid, 1.0)) for sid in ids]),
    )
    global_norm = np.linalg.norm(global_centroid)
    if global_norm:
        global_centroid = global_centroid / global_norm
    breadth = 1 - (X @ global_centroid)
    breadth_mean = float(np.mean(breadth))
    breadth_p90 = float(np.quantile(breadth, 0.90))

    id_to_index = {sid: i for i, sid in enumerate(ids)}
    long_ids = {
        str((rec.get("song") or {}).get("id"))
        for rec in (data.get("records") or {}).get("all") or []
    }
    recent_ids = {
        str((item.get("song") or {}).get("id"))
        for item in (data.get("records") or {}).get("recent") or []
    }

    def indices(group: set[str]) -> list[int]:
        return [id_to_index[sid] for sid in group if sid in id_to_index]

    def centroid(rows: list[int]) -> Any:
        if not rows:
            return None
        w = np.array([max(0.01, weights.get(ids[i], 1.0)) for i in rows])
        c = np.average(X[rows], axis=0, weights=w)
        norm = np.linalg.norm(c)
        return c / norm if norm else None

    long_rows = indices(long_ids)
    recent_rows = indices(recent_ids)
    lc = centroid(long_rows)
    rc = centroid(recent_rows)
    drift = None
    if lc is not None and rc is not None:
        drift = 1 - float(np.dot(lc, rc))

    def cluster_profile(rows: list[int]) -> list[float] | None:
        if not rows:
            return None
        totals = [0.0] * k
        for i in rows:
            totals[int(labels[i])] += max(0.01, float(weights.get(ids[i], 1.0)))
        total = sum(totals)
        return [x / total for x in totals] if total else None

    long_profile = cluster_profile(long_rows)
    recent_profile = cluster_profile(recent_rows)
    shifts = []
    cluster_lookup = {row["id"]: row for row in clusters}
    if long_profile and recent_profile:
        for cluster_id in range(k):
            shifts.append({
                "label": cluster_lookup[cluster_id]["label"],
                "delta": round((recent_profile[cluster_id] - long_profile[cluster_id]) * 100, 1),
            })
        shifts.sort(key=lambda row: abs(row["delta"]), reverse=True)

    prevalence = [row["prevalence"] / 100 for row in clusters if row["prevalence"] > 0]
    entropy = -sum(p * math.log(p) for p in prevalence)
    effective = math.exp(entropy) if prevalence else None

    return {
        "schemaVersion": "semantic-v1",
        "available": True,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "model": {
            "name": model_name,
            "revision": revision,
            "dimensions": int(X.shape[1]),
        },
        "corpus": {
            "documents": len(ids),
            "chunks": len(chunk_texts),
        },
        "clustering": {
            "selectedK": int(k),
            "silhouetteCosine": round(float(silhouette), 3),
            "bootstrapStabilityAMI": round(float(stability), 3),
            "effectiveClusters": round(float(effective), 2) if effective is not None else None,
            "clusters": clusters,
            "longRecentShift": shifts[:6],
        },
        "geometry": {
            "semanticBreadthMean": round(breadth_mean, 3),
            "semanticBreadthP90": round(breadth_p90, 3),
            "longTermDocuments": len(long_rows),
            "recentDocuments": len(recent_rows),
            "longRecentCosineDistance": round(float(drift), 3) if drift is not None else None,
        },
        "safety": {
            "containsLyrics": False,
            "containsSongIds": False,
            "containsSongTitles": False,
            "containsEmbeddings": False,
        },
    }
