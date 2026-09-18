from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any

try:
    import jieba  # type: ignore
except ImportError:  # deterministic fallback for zero-dependency environments
    jieba = None


_TS_RE = re.compile(r"\[[^\]]*\]")
_LATIN_RE = re.compile(r"[A-Za-z][A-Za-z']{1,}")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
_KANA_RE = re.compile(r"[\u3040-\u30ff]")
_HANGUL_RE = re.compile(r"[\uac00-\ud7af]")
_CYRILLIC_RE = re.compile(r"[\u0400-\u04ff]")

_CREDIT_PREFIXES = (
    "作词", "作曲", "编曲", "制作", "制作人", "混音", "录音", "和声", "吉他", "贝斯",
    "鼓", "母带", "监制", "词：", "曲：", "词:", "曲:", "lyrics by", "composed by",
    "written by", "producer", "produced by", "vocal", "vocals", "arranger", "composer",
    "lyricist", "mastering", "recording", "mix", "mixed by", "演唱", "企划", "出品", "发行",
    "策划", "统筹", "宣传", "文案", "版权", "封面", "录音室", "混音室", "op:", "sp:",
)

_EN_STOP = {
    "the","and","you","that","this","with","for","your","are","but","not","all","can","was","have",
    "from","they","will","just","like","what","when","where","who","why","how","its","our","out",
    "one","two","get","got","let","too","yeah","oh","ooh","ah","la","na","im","i'm","dont","don't",
    "me","my","we","us","it","is","in","on","to","of","a","an","i","be","so","if","as","at",
    "her","hers","him","his","them","their","theirs","there","here","then","up","down","only",
    "even","still","now","gonna","wanna","gotta","baby","know","say","come","make","want",
    "der","die","das","und","ich","du","er","sie","es","wir","ihr","den","dem","des","ein","eine",
    "mit","von","zu","im","auf","fur","für","ist","sind","war","sein","nicht","mein","dein","mich","dich",
    "le","la","les","de","des","du","un","une","et","je","tu","il","elle","nous","vous","ils","elles",
    "mon","ma","mes","ton","ta","tes","son","sa","ses","est","sont","pas","pour","avec","dans","sur",
}

_TERM_BLOCKLIST = {"纯音乐", "欣赏", "every", "vocal", "vocals", "版权", "音乐", "文化", "封面设计", "op", "sp"}

_ZH_STOP = {
    "我们","你们","他们","她们","一个","这样","那么","什么","怎么","还是","只是","不是","没有",
    "可以","因为","所以","已经","如果","时候","这里","那里","自己","然后","真的","知道","就是",
    "我的","你的","他的","她的","这个","那个","不会","不要","不能","一起","一直","还有","为了",
    "只有","有些","一切","所有","多么","多少","才能","是否","为什么","那些","每个",
}

_FIELDS = {
    "自我": ("我","我们","自己","i","me","my","mine","we","our","ours"),
    "他者": ("你","你们","他","她","他们","她们","you","your","he","she","they","them"),
    "过去": ("曾经","从前","过去","昨天","那年","当年","以前","once","yesterday","before","past"),
    "未来": ("未来","明天","以后","将来","终有一天","tomorrow","future","someday"),
    "记忆": ("记得","忘记","遗忘","回忆","记忆","remember","memory","forget"),
    "远方与地点": ("故乡","远方","城市","街道","街","海","山","天空","家乡","home","city","road","street","sea","sky"),
    "否定": ("不","没","无","别","未","not","never","no","without"),
}


def extract_primary_lyric(body: Any) -> str | None:
    if not isinstance(body, dict):
        return None
    for key in ("lrc", "yrc", "klyric"):
        block = body.get(key)
        if isinstance(block, dict):
            text = block.get("lyric")
            if isinstance(text, str) and text.strip():
                return text
    text = body.get("lyric")
    return text if isinstance(text, str) and text.strip() else None


def clean_lyric(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        line = _TS_RE.sub("", raw).strip()
        if not line:
            continue
        lowered = line.casefold()
        if any(lowered.startswith(prefix.casefold()) for prefix in _CREDIT_PREFIXES):
            continue
        if len(line) > 240:
            continue
        lines.append(line)

    joined = "\n".join(lines).strip()
    compact = re.sub(r"[\s，,。.!！?？、]+", "", joined)
    if compact in {"纯音乐请欣赏", "纯音乐欣赏", "instrumental"}:
        return ""
    return joined


def _fallback_cjk_tokens(segment: str) -> list[str]:
    if len(segment) == 2:
        return [segment] if segment not in _ZH_STOP else []
    grams = []
    for n in (2, 3):
        for i in range(max(0, len(segment) - n + 1)):
            token = segment[i:i+n]
            if token not in _ZH_STOP:
                grams.append(token)
    return grams


def tokenize(text: str) -> list[str]:
    text = clean_lyric(text)
    tokens: list[str] = []

    for word in _LATIN_RE.findall(text.casefold()):
        if word not in _EN_STOP and len(word) > 1:
            tokens.append(word)

    # Jieba is Chinese-specific. If a lyric contains substantial kana, avoid
    # interpreting its kanji as Chinese words; the script profile still records it.
    kana_chars = len(_KANA_RE.findall(text))
    cjk_chars = sum(len(segment) for segment in _CJK_RE.findall(text))
    japanese_dominant = kana_chars >= 8 and kana_chars >= max(1, int(cjk_chars * 0.08))

    if not japanese_dominant:
        for segment in _CJK_RE.findall(text):
            if jieba is not None:
                for token in jieba.cut(segment, cut_all=False):
                    token = token.strip()
                    if len(token) >= 2 and token not in _ZH_STOP:
                        tokens.append(token)
            else:
                tokens.extend(_fallback_cjk_tokens(segment))
    return [token for token in tokens if token not in _TERM_BLOCKLIST]


def select_text_corpus_song_ids(data: dict[str, Any], max_songs: int = 180) -> list[str]:
    if max_songs <= 0:
        return []

    scores: defaultdict[str, float] = defaultdict(float)
    all_records = (data.get("records") or {}).get("all") or []
    week_records = (data.get("records") or {}).get("week") or []
    recent = (data.get("records") or {}).get("recent") or []
    liked = set(data.get("likedSongIds") or [])

    for rank, rec in enumerate(all_records):
        song = rec.get("song") or {}
        sid = song.get("id")
        if sid is None:
            continue
        scores[str(sid)] += 1000 + 20 * math.log1p(float(rec.get("playCount") or 0)) + max(0, 100-rank)

    for rank, rec in enumerate(week_records):
        sid = (rec.get("song") or {}).get("id")
        if sid is not None:
            scores[str(sid)] += 400 + 10 * math.log1p(float(rec.get("playCount") or 0)) + max(0, 50-rank)

    for rank, item in enumerate(recent):
        sid = (item.get("song") or {}).get("id")
        if sid is not None:
            scores[str(sid)] += 250 + max(0, 100-rank) * 0.5

    for song in data.get("songs") or []:
        sid = song.get("id")
        if sid is None:
            continue
        sid = str(sid)
        scores[sid] += 2 if sid in liked else 0.1

    return [sid for sid, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:max_songs]]


def song_weights(data: dict[str, Any]) -> dict[str, float]:
    weights: defaultdict[str, float] = defaultdict(lambda: 0.05)
    for rec in (data.get("records") or {}).get("all") or []:
        sid = str((rec.get("song") or {}).get("id"))
        weights[sid] += 1 + math.log1p(float(rec.get("playCount") or 0))
    for rec in (data.get("records") or {}).get("week") or []:
        sid = str((rec.get("song") or {}).get("id"))
        weights[sid] += 1.5 + 0.7 * math.log1p(float(rec.get("playCount") or 0))
    for item in (data.get("records") or {}).get("recent") or []:
        sid = str((item.get("song") or {}).get("id"))
        weights[sid] += 1.2
    liked = set(data.get("likedSongIds") or [])
    for sid in liked:
        weights[str(sid)] += 0.15
    return dict(weights)


def _script_profile(texts: list[str]) -> list[dict[str, Any]]:
    counts = Counter()
    for text in texts:
        for ch in text:
            if "\u4e00" <= ch <= "\u9fff":
                counts["汉字"] += 1
            elif _KANA_RE.match(ch):
                counts["假名"] += 1
            elif _HANGUL_RE.match(ch):
                counts["韩文"] += 1
            elif _CYRILLIC_RE.match(ch):
                counts["西里尔"] += 1
            elif ch.isascii() and ch.isalpha():
                counts["拉丁字母"] += 1
    total = sum(counts.values())
    if not total:
        return []
    return [
        {"name": name, "share": round(count / total * 100, 1), "chars": count}
        for name, count in counts.most_common()
    ]


def _weighted_tfidf(docs: dict[str, list[str]], weights: dict[str, float], limit: int = 20) -> list[dict[str, Any]]:
    n_docs = len(docs)
    if n_docs == 0:
        return []
    df = Counter()
    for tokens in docs.values():
        df.update(set(tokens))

    scored = Counter()
    song_counts = Counter()
    for sid, tokens in docs.items():
        if not tokens:
            continue
        counts = Counter(tokens)
        total = sum(counts.values())
        weight = weights.get(sid, 1.0)
        for term, count in counts.items():
            idf = math.log((n_docs + 1) / (df[term] + 1)) + 1
            scored[term] += (count / total) * idf * weight
            song_counts[term] += 1

    min_df = max(2, math.ceil(n_docs * 0.02))
    stable = [
        (term, score)
        for term, score in scored.items()
        if len(term.strip()) >= 2 and song_counts[term] >= min_df and term not in _TERM_BLOCKLIST
    ]
    stable.sort(key=lambda item: item[1], reverse=True)
    return [
        {"term": term, "score": round(score, 4), "songCount": song_counts[term]}
        for term, score in stable[:limit]
    ]


def _field_profile(texts: list[str], token_count: int) -> list[dict[str, Any]]:
    joined = "\n".join(texts).casefold()
    rows = []
    for name, terms in _FIELDS.items():
        hits = 0
        for term in terms:
            if term.isascii():
                hits += len(re.findall(rf"\b{re.escape(term.casefold())}\b", joined))
            else:
                hits += joined.count(term)
        rate = (hits / token_count * 1000) if token_count else 0
        rows.append({"name": name, "hits": hits, "per1kTokens": round(rate, 1)})
    return sorted(rows, key=lambda x: x["per1kTokens"], reverse=True)


def _term_distribution(song_ids: set[str], docs: dict[str, list[str]], weights: dict[str, float]) -> dict[str, float]:
    counts = Counter()
    for sid in song_ids:
        tokens = docs.get(sid) or []
        if not tokens:
            continue
        local = Counter(tokens)
        w = weights.get(sid, 1.0)
        for term, count in local.items():
            counts[term] += count * w
    total = sum(counts.values())
    return {term: value / total for term, value in counts.items()} if total else {}


def _js_divergence(p: dict[str, float], q: dict[str, float]) -> float | None:
    if not p or not q:
        return None
    keys = set(p) | set(q)
    m = {k: (p.get(k, 0.0) + q.get(k, 0.0)) / 2 for k in keys}

    def kl(a: dict[str, float], b: dict[str, float]) -> float:
        return sum(v * math.log2(v / b[k]) for k, v in a.items() if v > 0 and b.get(k, 0) > 0)

    return (kl(p, m) + kl(q, m)) / 2


def analyze_text(data: dict[str, Any]) -> dict[str, Any]:
    lyrics = data.get("lyrics") or {}
    if not isinstance(lyrics, dict) or not lyrics:
        return {
            "available": False,
            "songsWithLyrics": 0,
            "selectedSongs": int((data.get("textCorpusMeta") or {}).get("selectedSongs") or 0),
            "coverage": None,
            "topTerms": [],
            "scriptProfile": [],
            "linguisticFields": [],
            "lexical": {},
            "drift": {},
        }

    cleaned = {
        str(sid): cleaned_text
        for sid, text in lyrics.items()
        if isinstance(text, str) and text.strip()
        for cleaned_text in [clean_lyric(text)]
        if cleaned_text
    }
    docs = {sid: tokenize(text) for sid, text in cleaned.items()}
    docs = {sid: tokens for sid, tokens in docs.items() if tokens}
    weights = song_weights(data)
    selected = int((data.get("textCorpusMeta") or {}).get("selectedSongs") or len(lyrics))
    successful = len(cleaned)

    all_tokens = [token for tokens in docs.values() for token in tokens]
    unique = len(set(all_tokens))
    lines = [line for text in cleaned.values() for line in text.splitlines() if line.strip()]
    chars = sum(len(line) for line in lines)

    long_ids = {
        str((rec.get("song") or {}).get("id"))
        for rec in (data.get("records") or {}).get("all") or []
    }
    recent_ids = {
        str((item.get("song") or {}).get("id"))
        for item in (data.get("records") or {}).get("recent") or []
    }
    p = _term_distribution(long_ids, docs, weights)
    q = _term_distribution(recent_ids, docs, weights)
    jsd = _js_divergence(p, q)

    doc_freq = Counter()
    for tokens in docs.values():
        doc_freq.update(set(tokens))

    rising = []
    for term in set(p) | set(q):
        diff = q.get(term, 0.0) - p.get(term, 0.0)
        if diff > 0 and doc_freq[term] >= 2 and term not in _TERM_BLOCKLIST:
            rising.append({"term": term, "delta": diff})
    rising.sort(key=lambda x: x["delta"], reverse=True)

    return {
        "available": bool(docs),
        "selectedSongs": selected,
        "providerLyricResponses": int((data.get("textCorpusMeta") or {}).get("successfulResponses") or 0),
        "songsWithLyrics": successful,
        "songsTokenized": len(docs),
        "coverage": round(successful / selected * 100, 1) if selected else None,
        "lines": len(lines),
        "characters": chars,
        "topTerms": _weighted_tfidf(docs, weights, limit=20),
        "scriptProfile": _script_profile(list(cleaned.values())),
        "linguisticFields": _field_profile(list(cleaned.values()), len(all_tokens)),
        "lexical": {
            "tokenCount": len(all_tokens),
            "uniqueTokens": unique,
            "typeTokenRatio": round(unique / len(all_tokens), 4) if all_tokens else None,
            "avgLineChars": round(chars / len(lines), 1) if lines else None,
        },
        "drift": {
            "longTermSongsWithLyrics": len(long_ids & set(docs)),
            "recentSongsWithLyrics": len(recent_ids & set(docs)),
            "jensenShannon": round(jsd, 4) if jsd is not None else None,
            "recentRisingTerms": [
                {"term": x["term"], "delta": round(x["delta"], 6)}
                for x in rising[:12]
            ],
        },
    }
