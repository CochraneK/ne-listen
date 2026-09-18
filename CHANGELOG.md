# Changelog

## 0.3.0 — text, topic and network analysis

- private bounded lyric corpus (default 180 high-evidence songs)
- lyric cleaning, Chinese segmentation and multilingual script profiling
- behavior-weighted TF-IDF and linguistic-field statistics
- long-term vs recent Jensen–Shannon lexical divergence
- NMF topic model + LSA semantic geometry + KMeans cross-check
- AMI reliability signal to prevent overclaiming unstable topics
- playlist Jaccard network, connected components and bridge artists
- public-safe daily aggregate `history.json`
- provider/production metadata filtering from lyric analysis
- public report never includes lyric strings or login credentials

## 0.2.0 — real personal archive

- real NetEase account workflow via GitHub Actions Secret
- full playlist pagination and 100% declared-track recovery
- nested recent-play parser
- provider-native week/month/year footprint extraction
- style, language and music-age distributions
- safe schema-only provider diagnostics
- corrected `unknown != 0` handling: Recent outside Top100 replaces the misleading exploration proxy
- we-read-style layered HTML report
- CI verified on Python 3.10 and 3.13


## 0.1.0 — bootstrap

- initial local-first architecture
- compatible NetEase HTTP collector
- raw + normalized data layers
- snapshot archive
- Repeat Index, Artist Loyalty, Taste Diversity and Exploration Proxy
- hidden-favorites candidate view
- data-coverage reporting
- responsive HTML report
- demo, doctor, sync, report and import-raw commands
- CI and synthetic Pages workflows
