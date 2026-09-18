# AGENTS.md

## Canonical product definition

ne-listen is a local-first personal listening archive and report generator for NetEase Cloud Music data.

## Non-goals

Do not turn it into a player, downloader, music-unlocking client, social client, recommendation engine, or personality profiler without an explicit product decision.

## Data rules

1. Preserve raw provider responses.
2. Normalize into a provider-independent schema.
3. `unknown != 0`.
4. Derived metrics must have documented formulas.
5. Reports must distinguish observed facts from derived metrics.
6. Never commit real auth cookies or personal raw data.
7. Remote actions remain read-only by default.

## Development loop

implement → test → generate demo → visually inspect → update docs → commit
