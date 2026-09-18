# STATUS

## 2026-09-18 · v0.2 real-data archive operational

- ✅ Real NetEase account pipeline is running on GitHub Actions.
- ✅ GitHub Pages deployment succeeds from the user's private `NETEASE_MUSIC_U` secret.
- ✅ 15/15 V1 data capabilities available in the latest real snapshot.
- ✅ 18 playlists observed; 7,255 / 7,255 declared playlist tracks fetched (100% page coverage).
- ✅ 5,868 liked-song IDs observed.
- ✅ 299 recent-play records normalized.
- ✅ Provider-native footprint layer added: week/month listening blocks, style preference, language, music-age, annual footprint.
- ✅ Long-term provider ranking kept explicitly bounded to Top100.
- ✅ `unknown != 0` audit fixed: removed the misleading exploration proxy and replaced it with Recent outside Top100 share.
- ✅ CI passes on Python 3.10 and 3.13.
- ✅ Lyric text mining: bounded private corpus, TF-IDF, linguistic fields and lexical JSD.
- ✅ Deep text layer: NMF + LSA + KMeans + AMI reliability check.
- ✅ Playlist network: Jaccard overlap, connected components and bridge artists.
- ✅ Public-safe aggregate history persists across GitHub Pages deployments; raw CI snapshots remain ephemeral.\n- ✅ 2026-09-18 visitor-first UI refactor: WeRead-family visual language, fewer primary metrics, methodology collapsed, desktop/mobile screenshot review.

## Current public report

https://cochranek.github.io/ne-listen/

## Latest validated analysis

- Default text corpus: 180 requested lyrics; ~99% usable lyric coverage in the latest run.
- Lexical layer: behavior-weighted TF-IDF + JSD long-term/recent contrast.
- Deep layer: 152 lyric documents modeled; NMF/LSA/KMeans working; AMI is deliberately exposed because topic agreement is exploratory rather than definitive.
- Playlist network: all 18 playlists included; overlap graph and bridge-artist metrics generated.
- Public-safe history: first 2026-09-18 aggregate snapshot published.

## Next research-quality upgrades

- Add multilingual transformer embedding / BERTopic as a **manual deep** mode rather than routine CI.
- Add lyric emotion / VAD content with explicit “lyrics ≠ listener mood” boundary.
- Add comment/reception mining as a separate social-interpretation corpus.
- Parse longitudinal taste drift and change points once multiple daily history points exist.
- Add explicit metric-version metadata to published `metrics.json`.
- Evaluate provider duration units before converting them into human-readable hours.
