from __future__ import annotations

from typing import Any, Iterable


def _response(raw: dict[str, Any], key: str) -> Any:
    r = (raw.get("responses") or {}).get(key) or {}
    return r.get("data") if r.get("ok") else None


def _first_dict(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def _song_from_obj(obj: Any) -> dict[str, Any] | None:
    if not isinstance(obj, dict):
        return None
    song = obj.get("song") if isinstance(obj.get("song"), dict) else obj
    sid = song.get("id")
    if sid is None:
        return None
    artists_raw = song.get("ar") or song.get("artists") or []
    artists = []
    for artist in artists_raw if isinstance(artists_raw, list) else []:
        if isinstance(artist, dict):
            artists.append({"id": artist.get("id"), "name": artist.get("name") or "Unknown"})
    album_raw = _first_dict(song.get("al"), song.get("album"))
    return {
        "id": str(sid),
        "name": song.get("name") or f"Song {sid}",
        "artists": artists,
        "album": {"id": album_raw.get("id"), "name": album_raw.get("name") or "Unknown"},
        "durationMs": song.get("dt") or song.get("duration"),
        "publishTime": album_raw.get("publishTime") or song.get("publishTime"),
    }


def _record_list(payload: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    data = payload.get(key)
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        song = _song_from_obj(item)
        if song:
            out.append({
                "song": song,
                "playCount": int(item.get("playCount") or item.get("score") or 0) if isinstance(item, dict) else 0,
                "score": item.get("score") if isinstance(item, dict) else None,
            })
    return out


def _recent_list(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    candidates: Iterable[Any] = []
    data = payload.get("data")
    if isinstance(data, dict):
        candidates = data.get("list") or data.get("songs") or []
    elif isinstance(data, list):
        candidates = data
    elif isinstance(payload.get("songs"), list):
        candidates = payload["songs"]
    out = []
    for item in candidates:
        song = _song_from_obj(item)
        if song:
            out.append({"song": song, "playedAt": item.get("playTime") if isinstance(item, dict) else None})
    return out


def _extract_liked(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    ids = payload.get("ids")
    if not isinstance(ids, list):
        return []
    return [str(x) for x in ids]


def _extract_playlists(payload: Any, tracks_payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("playlist"), list):
        return []
    tracks_by_id = tracks_payload if isinstance(tracks_payload, dict) else {}
    result = []
    for p in payload["playlist"]:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id")) if p.get("id") is not None else None
        track_response = tracks_by_id.get(pid, {}) if pid else {}
        body = track_response.get("data") if isinstance(track_response, dict) and track_response.get("ok") else None
        candidates = []
        if isinstance(body, dict):
            candidates = body.get("songs") or (body.get("data") or {}).get("songs") if isinstance(body.get("data"), dict) else body.get("songs") or []
        tracks = []
        if isinstance(candidates, list):
            for item in candidates:
                song = _song_from_obj(item)
                if song:
                    tracks.append(song)
        result.append({
            "id": pid,
            "name": p.get("name") or "Untitled",
            "trackCount": p.get("trackCount"),
            "playCount": p.get("playCount"),
            "subscribed": bool(p.get("subscribed")),
            "createTime": p.get("createTime"),
            "updateTime": p.get("updateTime"),
            "tracks": tracks,
        })
    return result


def _extract_profile(raw: dict[str, Any]) -> dict[str, Any]:
    profile_payload = _response(raw, "profile")
    account_payload = _response(raw, "account")
    profile = {}
    root = profile_payload if isinstance(profile_payload, dict) else {}
    if root:
        profile = _first_dict(root.get("profile"), root.get("data"), root)
    if not profile and isinstance(account_payload, dict):
        profile = _first_dict(account_payload.get("profile"), account_payload.get("account"))
    return {
        "userId": str(profile.get("userId") or raw.get("uid") or "") or None,
        "nickname": profile.get("nickname"),
        "avatarUrl": profile.get("avatarUrl"),
        "signature": profile.get("signature"),
        "followeds": profile.get("followeds"),
        "follows": profile.get("follows"),
        "eventCount": profile.get("eventCount"),
        "listenSongs": root.get("listenSongs") if root else None,
        "level": root.get("level") if root else None,
        "createDays": root.get("createDays") if root else None,
        "createTime": profile.get("createTime") or root.get("createTime") if root else profile.get("createTime"),
    }


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    record_payload = _response(raw, "record_all")
    week_payload = _response(raw, "record_week")
    all_records = _record_list(record_payload, "allData")
    if not all_records:
        all_records = _record_list(record_payload, "weekData")
    week_records = _record_list(week_payload, "weekData")
    recent = _recent_list(_response(raw, "recent_songs"))
    liked_ids = _extract_liked(_response(raw, "liked_ids"))
    playlists = _extract_playlists(_response(raw, "playlists"), _response(raw, "playlist_tracks"))

    capability = {}
    for key, response in (raw.get("responses") or {}).items():
        capability[key] = bool(response.get("ok"))

    song_index: dict[str, dict[str, Any]] = {}
    for record in all_records + week_records:
        song_index[record["song"]["id"]] = record["song"]
    for item in recent:
        song_index[item["song"]["id"]] = item["song"]
    for playlist in playlists:
        for song in playlist.get("tracks") or []:
            song_index[song["id"]] = song

    return {
        "schemaVersion": "normalized-v1",
        "source": raw.get("source"),
        "collectedAt": raw.get("collectedAt"),
        "profile": _extract_profile(raw),
        "songs": list(song_index.values()),
        "records": {"all": all_records, "week": week_records, "recent": recent},
        "likedSongIds": liked_ids,
        "playlists": playlists,
        "providerPayloads": {
            "userLevel": _response(raw, "user_level"),
            "userSubcount": _response(raw, "user_subcount"),
            "listenTotal": _response(raw, "listen_total"),
            "listenRealtimeWeek": _response(raw, "listen_realtime_week"),
            "listenRealtimeMonth": _response(raw, "listen_realtime_month"),
            "listenReportWeek": _response(raw, "listen_report_week"),
            "listenReportMonth": _response(raw, "listen_report_month"),
            "listenReportYear": _response(raw, "listen_report_year"),
            "listenYear": _response(raw, "listen_year"),
            "listenToday": _response(raw, "listen_today"),
            "stylePreference": _response(raw, "style_preference"),
            "recentListen": _response(raw, "recent_listen"),
        },
        "capabilities": capability,
    }
