from __future__ import annotations

import math
from typing import Any

from .textmining import clean_lyric, song_weights, tokenize


def _unavailable(reason: str) -> dict[str, Any]:
    return {
        "available": False,
        "reason": reason,
        "topics": [],
        "topicShift": [],
        "latent": {},
    }


def analyze_deep_text(data: dict[str, Any], requested_topics: int = 8) -> dict[str, Any]:
    try:
        import numpy as np
        from sklearn.cluster import KMeans
        from sklearn.decomposition import NMF, TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics import adjusted_mutual_info_score
        from sklearn.preprocessing import normalize
    except ImportError:
        return _unavailable("install ne-listen[deep] to enable NMF/LSA analysis")

    lyrics = data.get("lyrics") or {}
    docs: list[tuple[str, str]] = []
    for sid, raw in lyrics.items():
        if not isinstance(raw, str):
            continue
        cleaned = clean_lyric(raw)
        tokens = tokenize(cleaned)
        if len(tokens) >= 8:
            docs.append((str(sid), " ".join(tokens)))

    if len(docs) < 20:
        return _unavailable("at least 20 tokenized lyric documents are required")

    ids = [sid for sid, _ in docs]
    texts = [text for _, text in docs]
    vectorizer = TfidfVectorizer(
        tokenizer=str.split,
        preprocessor=None,
        token_pattern=None,
        lowercase=False,
        min_df=2,
        max_df=0.90,
        max_features=6000,
        sublinear_tf=True,
        norm="l2",
    )
    X = vectorizer.fit_transform(texts)
    vocab = vectorizer.get_feature_names_out()

    if X.shape[1] < 10:
        return _unavailable("insufficient shared vocabulary after filtering")

    k = min(max(2, requested_topics), 10, max(2, X.shape[0] // 12), X.shape[1] - 1)
    nmf = NMF(
        n_components=k,
        init="nndsvda",
        random_state=42,
        max_iter=600,
        solver="cd",
    )
    W = nmf.fit_transform(X)
    H = nmf.components_

    weights_map = song_weights(data)
    weights = np.array([max(0.01, float(weights_map.get(sid, 1.0))) for sid in ids], dtype=float)
    weighted_topic = (W * weights[:, None]).sum(axis=0)
    prevalence = weighted_topic / weighted_topic.sum() if weighted_topic.sum() else np.ones(k) / k

    topics = []
    for topic_idx in range(k):
        top_idx = np.argsort(H[topic_idx])[::-1][:8]
        terms = [str(vocab[i]) for i in top_idx]
        topics.append({
            "id": int(topic_idx),
            "label": " / ".join(terms[:3]),
            "terms": terms,
            "prevalence": round(float(prevalence[topic_idx]) * 100, 1),
        })
    topics.sort(key=lambda item: item["prevalence"], reverse=True)

    dims = min(32, X.shape[0] - 1, X.shape[1] - 1)
    if dims < 2:
        return {
            "available": True,
            "documents": len(docs),
            "vocabularySize": int(X.shape[1]),
            "topics": topics,
            "effectiveTopics": None,
            "methodAgreementAMI": None,
            "topicShift": [],
            "latent": {"available": False},
        }

    svd = TruncatedSVD(n_components=dims, random_state=42)
    Z = normalize(svd.fit_transform(X))
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=20)
    cluster_labels = kmeans.fit_predict(Z)
    nmf_labels = W.argmax(axis=1)
    ami = adjusted_mutual_info_score(nmf_labels, cluster_labels)

    id_to_idx = {sid: i for i, sid in enumerate(ids)}
    long_ids = {
        str((rec.get("song") or {}).get("id"))
        for rec in (data.get("records") or {}).get("all") or []
    }
    recent_ids = {
        str((item.get("song") or {}).get("id"))
        for item in (data.get("records") or {}).get("recent") or []
    }

    def group_indices(group: set[str]) -> list[int]:
        return [id_to_idx[sid] for sid in group if sid in id_to_idx]

    def weighted_mean(matrix: Any, indices: list[int]) -> Any:
        if not indices:
            return None
        local_w = weights[indices]
        return np.average(matrix[indices], axis=0, weights=local_w)

    long_idx = group_indices(long_ids)
    recent_idx = group_indices(recent_ids)
    long_centroid = weighted_mean(Z, long_idx)
    recent_centroid = weighted_mean(Z, recent_idx)
    centroid_distance = None
    if long_centroid is not None and recent_centroid is not None:
        ln = np.linalg.norm(long_centroid)
        rn = np.linalg.norm(recent_centroid)
        if ln and rn:
            centroid_distance = 1 - float(np.dot(long_centroid, recent_centroid) / (ln * rn))

    def topic_profile(indices: list[int]) -> Any:
        if not indices:
            return None
        local = (W[indices] * weights[indices, None]).sum(axis=0)
        total = local.sum()
        return local / total if total else None

    lp = topic_profile(long_idx)
    rp = topic_profile(recent_idx)
    shift = []
    if lp is not None and rp is not None:
        topic_lookup = {item["id"]: item for item in topics}
        for topic_idx in range(k):
            delta = float(rp[topic_idx] - lp[topic_idx])
            shift.append({
                "id": topic_idx,
                "label": topic_lookup[topic_idx]["label"],
                "delta": round(delta * 100, 1),
            })
        shift.sort(key=lambda item: abs(item["delta"]), reverse=True)

    entropy = -sum(float(p) * math.log(float(p)) for p in prevalence if p > 0)
    effective_topics = math.exp(entropy)

    cluster_summaries = []
    for cluster_idx in range(k):
        rows = np.where(cluster_labels == cluster_idx)[0]
        if len(rows) == 0:
            continue
        centroid_terms = np.asarray(X[rows].mean(axis=0)).ravel()
        top_idx = centroid_terms.argsort()[::-1][:6]
        terms = [str(vocab[i]) for i in top_idx]
        cluster_summaries.append({
            "id": int(cluster_idx),
            "size": int(len(rows)),
            "label": " / ".join(terms[:3]),
            "terms": terms,
        })
    cluster_summaries.sort(key=lambda item: item["size"], reverse=True)

    return {
        "available": True,
        "documents": len(docs),
        "vocabularySize": int(X.shape[1]),
        "topicCount": int(k),
        "effectiveTopics": round(float(effective_topics), 2),
        "topics": topics,
        "topicShift": shift[:6],
        "methodAgreementAMI": round(float(ami), 3),
        "latent": {
            "available": True,
            "dimensions": int(dims),
            "longTermDocuments": len(long_idx),
            "recentDocuments": len(recent_idx),
            "centroidCosineDistance": round(float(centroid_distance), 3) if centroid_distance is not None else None,
            "clusters": cluster_summaries[:6],
        },
    }
