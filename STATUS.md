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

## Current public report

https://cochranek.github.io/ne-listen/

## Next research-quality upgrades

- Parse longitudinal snapshot-to-snapshot change once enough ne-listen snapshots accumulate.
- Add explicit metric-version metadata to published `metrics.json`.
- Add automated Page contract checks for accidental credential/raw-data leakage.
- Evaluate whether provider `totalDuration` / annual `playDuration` units can be independently verified before human-readable conversion.
