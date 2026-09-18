# Text mining

ne-listen treats lyrics as a **private analysis corpus**, not as publishable report content.

## Default corpus

The GitHub Actions report fetches lyrics for up to 180 songs selected from:

1. all-time Top100 records;
2. weekly records;
3. recent plays;
4. liked/library songs as lower-priority candidates.

This keeps CI bounded while preserving the strongest behavioral evidence. Local users can raise `--text-max` for a broader corpus.

## Published analyses

The public metrics contain only derived statistics:

- lyric request / usable-text coverage;
- script distribution;
- lexical diversity;
- behavior-weighted TF-IDF terms;
- transparent linguistic-field counts;
- long-term vs recent lexical drift using Jensen–Shannon divergence;
- recent-rising terms.

They do **not** include lyric strings.

## Weighting

Each lyric document receives a deterministic listening-evidence weight based on all-time play rank/count, weekly play evidence, recent appearances, and a small liked-song bonus. TF-IDF is aggregated using those weights, so one obscure liked song does not count the same as a song repeatedly observed in listening records.

## Interpretation boundary

Lyrics describe text the listener repeatedly encounters. They are not direct evidence of the listener's beliefs, mood, personality, diagnosis, or life events.

## Next layer

Semantic embeddings / BERTopic are intentionally separate from the default CI path. They can add semantic clustering and centroid drift later without making the basic archive depend on a large model.
