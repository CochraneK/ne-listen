# DECISIONS

## D001 — ne-listen is not an API fork

Use external NetEase API implementations as replaceable backends. Keep canonical schema, snapshots, analytics and report in this repository.

## D002 — compatible HTTP adapter first

Enhanced-style and ncm-api-rs HTTP servers are similar enough to share one V1 adapter. Capabilities are probed independently so one broken endpoint does not invalidate a whole snapshot.

## D003 — snapshot-first

Historical event coverage cannot be assumed. Save repeated point-in-time observations and build longitudinal claims only from evidence ne-listen actually captured.

## D004 — unknown is not zero

An unavailable endpoint or missing historical period is represented as unavailable, not as an observed zero.

## D005 — read-only boundary

Do not call remote mutations. Authentication is used only to retrieve the user's own data.

## D006 — no music-to-personality leap

Behavioral metrics describe listening distributions. They are not automatically translated into personality, diagnosis, mood or psychological traits.

## D007 — Pages may publish a derived real-data report, never credentials/raw archive

If `NETEASE_MUSIC_U` is intentionally configured as a repository secret, the ephemeral runner may build the user's derived HTML report. The cookie, raw responses, normalized archive and snapshots are never included in the Pages artifact. Without the secret, Pages falls back to a synthetic demo.
