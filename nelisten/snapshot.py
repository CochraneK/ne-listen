from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io import write_json


def snapshot(raw: dict[str, Any], normalized: dict[str, Any], data_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    root = data_dir / "snapshots" / stamp
    write_json(root / "raw.json", raw)
    write_json(root / "normalized.json", normalized)
    write_json(data_dir / "raw" / "latest.json", raw)
    write_json(data_dir / "normalized" / "latest.json", normalized)
    return root
