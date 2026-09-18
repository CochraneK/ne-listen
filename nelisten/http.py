from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class HttpResult:
    ok: bool
    status: int | None
    body: Any
    error: str | None = None


def get_json(base_url: str, path: str, params: dict[str, Any], timeout: int = 20) -> HttpResult:
    base = base_url.rstrip("/")
    clean_params = {k: v for k, v in params.items() if v not in (None, "")}
    url = f"{base}{path}?{urllib.parse.urlencode(clean_params)}" if clean_params else f"{base}{path}"
    request = urllib.request.Request(url, headers={"User-Agent": "ne-listen/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return HttpResult(True, response.status, json.loads(raw))
    except Exception as exc:  # capability probing is intentionally fail-soft
        return HttpResult(False, getattr(exc, "code", None), None, f"{type(exc).__name__}: {exc}")
