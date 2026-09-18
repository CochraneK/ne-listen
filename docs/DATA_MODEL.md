# Data model

`ne-listen` keeps three layers separate.

## Raw (`raw-v1`)

A loss-minimizing envelope around provider responses:

```json
{
  "schemaVersion": "raw-v1",
  "source": "netease-compatible-http",
  "collectedAt": "...",
  "uid": "...",
  "responses": {
    "record_all": {"ok": true, "status": 200, "data": {}}
  }
}
```

Raw payloads are private and provider-specific.

## Normalized (`normalized-v1`)

Canonical, provider-independent fields used by analytics:

- `profile`
- `songs`
- `records.all`
- `records.week`
- `records.recent`
- `likedSongIds`
- `playlists`
- `providerPayloads`
- `capabilities`

A missing capability remains missing. It is never converted to a zero-valued history.

## Derived metrics

Metrics are regenerated deterministically from normalized data and may change definition across versions. Metric definitions therefore live in `docs/METRICS.md` and should be versioned with code.
