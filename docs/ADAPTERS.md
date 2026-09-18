# Adapter strategy

V1 uses a `CompatibleHttpAdapter` rather than vendor-specific business logic.

Why:

- NeteaseCloudMusicApi Enhanced and ncm-api-rs expose largely compatible HTTP routes.
- Reverse-engineered endpoints can disappear or change independently.
- ne-listen should survive backend swaps without changing its canonical schema or report.

## Capability probing

Each endpoint is called independently and archived with:

- `ok`
- HTTP `status`
- raw `data`
- `error`
- `path`

Failure is local to that capability.

## Read-only boundary

The adapter intentionally excludes write endpoints such as like, playlist mutation, comments, scrobble, uploads and purchases.

## Candidate backends

- NeteaseCloudMusicApi Enhanced: broad Node.js ecosystem and HTTP API.
- ncm-api-rs: Rust implementation with compatible server mode and listening-footprint endpoints.

ne-listen does not vendor either backend and does not require their source code in this repository.
