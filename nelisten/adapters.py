from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .http import get_json


# Read-only endpoints. Missing/unsupported endpoints lower coverage rather than fail the sync.
READ_ENDPOINTS = {
    "account": ("/user/account", {}),
    "user_level": ("/user/level", {}),
    "user_subcount": ("/user/subcount", {}),
    "record_all": ("/user/record", {"type": 0}),
    "record_week": ("/user/record", {"type": 1}),
    "playlists": ("/user/playlist", {"limit": 1000}),
    "liked_ids": ("/likelist", {}),
    "recent_songs": ("/record/recent/song", {"limit": 100}),
    "recent_listen": ("/recent/listen/list", {}),
    "listen_total": ("/listen/data/total", {}),
    "listen_realtime_week": ("/listen/data/realtime/report", {"type": "week"}),
    "listen_realtime_month": ("/listen/data/realtime/report", {"type": "month"}),
    "listen_report_week": ("/listen/data/report", {"type": "week"}),
    "listen_report_month": ("/listen/data/report", {"type": "month"}),
    "listen_report_year": ("/listen/data/report", {"type": "year"}),
    "listen_year": ("/listen/data/year/report", {}),
    "listen_today": ("/listen/data/today/song", {}),
    "style_preference": ("/style/preference", {}),
}


@dataclass
class CompatibleHttpAdapter:
    base_url: str
    cookie: str = ""
    timeout: int = 20
    playlist_track_limit: int = 1000
    max_playlists: int = 100

    def _call(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        merged = dict(params)
        if self.cookie:
            merged["cookie"] = self.cookie
        result = get_json(self.base_url, path, merged, timeout=self.timeout)
        return {
            "ok": result.ok,
            "status": result.status,
            "data": result.body,
            "error": result.error,
            "path": path,
        }

    @staticmethod
    def _find_uid(account_payload: Any) -> str | None:
        if not isinstance(account_payload, dict):
            return None
        candidates = [
            account_payload.get("profile"),
            account_payload.get("account"),
            (account_payload.get("data") or {}).get("profile") if isinstance(account_payload.get("data"), dict) else None,
        ]
        for candidate in candidates:
            if isinstance(candidate, dict):
                uid = candidate.get("userId") or candidate.get("id")
                if uid is not None:
                    return str(uid)
        return None

    @staticmethod
    def _playlist_ids(payload: Any) -> list[str]:
        if not isinstance(payload, dict):
            return []
        playlists = payload.get("playlist")
        if not isinstance(playlists, list):
            return []
        ids: list[str] = []
        for item in playlists:
            if isinstance(item, dict) and item.get("id") is not None:
                ids.append(str(item["id"]))
        return ids

    def collect(self, uid: str | None = None) -> dict[str, Any]:
        collected_at = datetime.now(timezone.utc).isoformat()
        responses: dict[str, Any] = {}

        responses["account"] = self._call("/user/account", {})
        resolved_uid = uid or self._find_uid(responses["account"].get("data"))

        if resolved_uid:
            responses["profile"] = self._call("/user/detail", {"uid": resolved_uid})

        for key, (path, base_params) in READ_ENDPOINTS.items():
            if key == "account":
                continue
            params = dict(base_params)
            if key in {"record_all", "record_week", "playlists", "liked_ids"}:
                if not resolved_uid:
                    responses[key] = {
                        "ok": False,
                        "status": None,
                        "data": None,
                        "error": "uid unavailable",
                        "path": path,
                    }
                    continue
                params["uid"] = resolved_uid
            responses[key] = self._call(path, params)

        # Enrich playlist membership. Each playlist is isolated so one private/deleted
        # playlist cannot break the rest of the archive.
        playlist_tracks: dict[str, Any] = {}
        playlist_payload = responses.get("playlists", {}).get("data")
        for playlist_id in self._playlist_ids(playlist_payload)[: self.max_playlists]:
            playlist_tracks[playlist_id] = self._call(
                "/playlist/track/all",
                {"id": playlist_id, "limit": self.playlist_track_limit, "offset": 0},
            )
        responses["playlist_tracks"] = {
            "ok": bool(playlist_tracks),
            "status": 200 if playlist_tracks else None,
            "data": playlist_tracks,
            "error": None if playlist_tracks else "no playlist tracks collected",
            "path": "/playlist/track/all",
        }

        return {
            "schemaVersion": "raw-v1",
            "source": "netease-compatible-http",
            "baseUrl": self.base_url,
            "collectedAt": collected_at,
            "uid": resolved_uid,
            "responses": responses,
        }
