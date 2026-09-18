# Getting started with a real account

The safest V1 topology is:

```text
NetEase account
  ↓
local compatible API server on 127.0.0.1
  ↓
ne-listen collector
  ↓
private local data/
```

## 1. Run a compatible backend locally

Use a currently maintained compatible server such as NeteaseCloudMusicApi Enhanced or the HTTP server mode of ncm-api-rs. ne-listen does not bundle either dependency.

Keep it bound to localhost where practical.

## 2. Obtain your own login cookie

Set only your own `MUSIC_U` value locally:

```bash
export NELISTEN_COOKIE='MUSIC_U=...'
export NELISTEN_API_BASE='http://127.0.0.1:3000'
```

Never commit the real value.

## 3. Sync

```bash
ne-listen sync
```

The collector first tries `/user/account` to resolve UID. If that endpoint cannot resolve it:

```bash
ne-listen sync --uid YOUR_UID
```

## 4. Review coverage

```bash
ne-listen doctor
```

A partial result is valid. Missing endpoints remain missing instead of becoming fake zeroes.

## 5. Open the report

Open:

```text
data/report/index.html
```

Your raw and normalized personal data remain under gitignored `data/` paths.
