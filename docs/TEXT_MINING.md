# Text mining

ne-listen treats lyrics as a **private analysis corpus**, not as publishable report content.

## Default corpus

The GitHub Actions report requests up to 180 songs selected from all-time Top100, weekly records, recent plays, then liked/library candidates. This is a bounded, high-evidence corpus rather than a full 5,000+ lyric crawl on every deployment.

## Cleaning

- LRC timestamps are removed.
- common production-credit lines are removed.
- provider placeholders such as “纯音乐，请欣赏” are treated as **no usable lyric**, not as text.
- Chinese tokenization uses jieba.
- Japanese-dominant lyrics are excluded from Chinese lexical segmentation rather than mis-tokenizing kanji as Chinese words.
- other scripts remain represented in the script-distribution analysis even when the lexical tokenizer does not model them.

The public metric therefore distinguishes provider lyric responses from **usable lyric documents**.

## Published analyses

Only derived statistics are public:

- usable lyric coverage;
- script distribution;
- lexical diversity;
- behavior-weighted TF-IDF terms with a stability floor (term must occur across multiple lyric documents);
- transparent linguistic-field counts;
- long-term vs recent lexical drift using Jensen–Shannon divergence;
- recent-rising terms.

Lyrics themselves are not included in the Page or `metrics.json`.

## Weighting

Each lyric document receives a deterministic listening-evidence weight based on all-time play evidence, weekly listening, recent appearances, and a small liked-song bonus. This prevents one obscure library item from counting the same as a repeatedly observed song.

## Interpretation boundary

Lyrics describe text the listener repeatedly encounters. They are not direct evidence of the listener's beliefs, mood, personality, diagnosis, or life events.

## Semantic roadmap

The lexical layer is deliberately model-light. The next deep-analysis layer can add multilingual embeddings / BERTopic or LLM-assisted topic induction with reliability checks, but it should remain separable from the fast default Pages build.
