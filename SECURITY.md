# Security and privacy

The most sensitive values in this project are authentication cookies and personal listening history.

- Keep `NELISTEN_COOKIE` only in local environment variables or a local `.env` that is gitignored.
- Never paste a real cookie into issues, logs, screenshots, Pages, CI variables intended for forks, or committed fixtures.
- `data/raw/`, `data/snapshots/`, `data/normalized/` and `data/report/` are gitignored by default.
- The V1 collector is read-only and intentionally avoids remote write endpoints.
- Pages may publish the derived personal report only when the repository owner intentionally configures `NETEASE_MUSIC_U`; raw/normalized archives and credentials are excluded from the artifact.
