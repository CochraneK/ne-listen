# Analysis layers

ne-listen uses multiple analysis layers instead of treating one metric or model as truth.

## 1. Listening behavior

Deterministic statistics from play rankings, recent plays, likes and playlists:

- concentration / Repeat Index;
- artist loyalty;
- effective artist diversity;
- recent-vs-long-term overlap;
- hidden-favorite candidates.

## 2. Lexical lyric mining

Private lyric text is cleaned and converted into public aggregates:

- behavior-weighted TF-IDF;
- lexical diversity;
- script distribution;
- transparent linguistic fields;
- Jensen–Shannon divergence between long-term and recent lexical distributions.

## 3. Deep topic / latent-semantic layer

When the optional `deep` dependency is installed:

### NMF

Non-negative Matrix Factorization discovers interpretable word-based topics. Topic prevalence is weighted by listening evidence.

### LSA

TF-IDF is projected with Truncated SVD into a latent semantic space. ne-listen compares long-term and recent weighted centroids using cosine distance.

### Cross-method reliability

NMF dominant topics are compared with KMeans clusters in the LSA space using Adjusted Mutual Information (AMI). Agreement does not prove a topic is “true”, but low agreement is a warning not to over-interpret a single unsupervised solution.

No per-song topic assignments or lyric strings are published.

## 4. Playlist network

For each pair of accessible playlists, ne-listen computes Jaccard overlap. It also finds:

- songs that appear in multiple playlists;
- the highest-overlap playlist pairs;
- “bridge artists” that occur across many playlist contexts.

This describes how the library is organized, not only what is played most.

## 5. Future layers

Planned but kept separate until validated:

- multilingual transformer embeddings / BERTopic;
- lyric emotion and VAD content (explicitly not the listener's mood);
- comment/reception corpus as a separate social-interpretation layer;
- longitudinal change points once repeated ne-listen snapshots exist;
- audio/acoustic features if a lawful metadata source is available.

## Interpretation rule

Every public statement should remain one of:

**Fact → Pattern → bounded interpretation.**

The system must not jump from lyrical content to claims about the listener's diagnosis, beliefs, personality, or life events.
