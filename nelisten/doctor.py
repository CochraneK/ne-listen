from __future__ import annotations

from pathlib import Path
from typing import Any


def inspect(data_dir: Path, normalized: dict[str, Any] | None = None) -> list[tuple[str, bool, str]]:
    checks = []
    checks.append(("data directory", data_dir.exists(), str(data_dir)))
    latest = data_dir / "normalized" / "latest.json"
    checks.append(("normalized latest", latest.exists(), str(latest)))
    if normalized:
        caps = normalized.get("capabilities") or {}
        checks.append(("account data", bool(caps.get("account")), "required to resolve identity automatically"))
        checks.append(("play record", bool(caps.get("record_all")), "core report source"))
        checks.append(("recent songs", bool(caps.get("recent_songs")), "needed for exploration proxy"))
        checks.append(("liked ids", bool(caps.get("liked_ids")), "needed for hidden-favorites comparison"))
    return checks
