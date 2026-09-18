from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any


def _effective_diversity(counter: Counter[str]) -> float | None:
    total = sum(counter.values())
    if total <= 0:
        return None
    entropy = -sum((v / total) * math.log(v / total) for v in counter.values() if v > 0)
    return math.exp(entropy)


def _top_share(values: list[int], fraction: float = 0.1) -> float | None:
    total = sum(values)
    if total <= 0 or not values:
        return None
    k = max(1, math.ceil(len(values) * fraction))
    return sum(sorted(values, reverse=True)[:k]) / total


def _pct(x: float | None) -> float | None:
    return round(x * 100, 1) if x is not None else None


def _record_counters(records: list[dict[str, Any]]) -> tuple[Counter[str], dict[str, str], Counter[str], dict[str, str]]:
    song_plays: Counter[str] = Counter()
    song_names: dict[str, str] = {}
    artist_plays: Counter[str] = Counter()
    artist_names: dict[str, str] = {}
    for rec in records:
        song = rec.get("song") or {}
        sid = str(song.get("id"))
        plays = int(rec.get("playCount") or 0)
        song_plays[sid] += plays
        song_names[sid] = song.get("name") or sid
        artists = song.get("artists") or []
        if not artists:
            continue
        share = plays / len(artists) if plays else 0
        for artist in artists:
            key = str(artist.get("id") or artist.get("name") or "unknown")
            artist_names[key] = artist.get("name") or "Unknown"
            artist_plays[key] += share
    return song_plays, song_names, artist_plays, artist_names


def _decades(songs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for song in songs:
        ts = song.get("publishTime")
        if not isinstance(ts, (int, float)) or ts <= 0:
            continue
        try:
            year = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).year
        except (OSError, OverflowError, ValueError):
            continue
        decade = f"{year // 10 * 10}s"
        counts[decade] += 1
    return [{"name": k, "count": v} for k, v in sorted(counts.items())]


def _shape(value: Any, depth: int = 5) -> Any:
    """Return schema-only diagnostics: keys, container lengths and primitive types, never values."""
    if depth <= 0:
        return type(value).__name__
    if isinstance(value, dict):
        return {
            "type": "object",
            "keys": {str(k): _shape(v, depth - 1) for k, v in value.items()},
        }
    if isinstance(value, list):
        return {
            "type": "array",
            "length": len(value),
            "item": _shape(value[0], depth - 1) if value else None,
        }
    if value is None:
        return "null"
    return type(value).__name__


def _provider_facts(payloads: dict[str, Any]) -> dict[str, Any]:
    def body(name: str) -> dict[str, Any]:
        root = payloads.get(name)
        if not isinstance(root, dict):
            return {}
        data = root.get("data")
        return data if isinstance(data, dict) else {}

    total = body("listenTotal")
    week_rt = body("listenRealtimeWeek")
    month_rt = body("listenRealtimeMonth")
    week_report = body("listenReportWeek")
    month_report = body("listenReportMonth")
    year = body("listenYear")
    style = body("stylePreference")

    def block(root: dict[str, Any], name: str) -> dict[str, Any]:
        value = root.get(name)
        return value if isinstance(value, dict) else {}

    week_dist = block(week_rt, "listenTimeDistributionBlock")
    month_dist = block(month_rt, "listenTimeDistributionBlock")
    week_time = block(week_report, "listenTimeBlock")
    month_time = block(month_report, "listenTimeBlock")
    month_top_song = block(month_report, "topSongBlock")
    month_top_artist = block(month_report, "topArtistBlock")
    month_top_style = block(month_report, "topStyleBlock")
    month_top_age = block(month_report, "topAgeBlock")

    return {
        "totalDurationRaw": total.get("totalDuration"),
        "weekPlayDurationRaw": week_dist.get("playDuration"),
        "weekListenDays": week_dist.get("listenDays"),
        "weekPlayDurationText": week_time.get("playDurationText"),
        "monthPlayDurationRaw": month_dist.get("playDuration"),
        "monthListenDays": month_dist.get("listenDays"),
        "monthPlayDurationText": month_time.get("playDurationText"),
        "monthTopSong": {
            "name": month_top_song.get("songName"),
            "playCount": month_top_song.get("playCount"),
        },
        "monthTopArtist": {
            "name": month_top_artist.get("artistName"),
            "playCount": month_top_artist.get("playCount"),
        },
        "monthTopStyle": {
            "genre": month_top_style.get("genreName"),
            "secondGenre": month_top_style.get("secondGenreName"),
        },
        "monthTopAge": month_top_age.get("age"),
        "displayYear": year.get("displayYear"),
        "yearItemCount": len(year.get("yearItems") or []) if isinstance(year.get("yearItems"), list) else 0,
        "styleTagCount": len(style.get("tags") or []) if isinstance(style.get("tags"), list) else 0,
    }


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    records = (data.get("records") or {}).get("all") or []
    week_records = (data.get("records") or {}).get("week") or []
    liked = set(data.get("likedSongIds") or [])
    play_by_song: Counter[str] = Counter()
    name_by_song: dict[str, str] = {}
    artist_plays: Counter[str] = Counter()
    artist_names: dict[str, str] = {}
    album_plays: Counter[str] = Counter()
    album_names: dict[str, str] = {}

    for rec in records:
        song = rec.get("song") or {}
        sid = str(song.get("id"))
        plays = int(rec.get("playCount") or 0)
        play_by_song[sid] += plays
        name_by_song[sid] = song.get("name") or sid
        album = song.get("album") or {}
        aid = str(album.get("id") or album.get("name") or "unknown")
        album_names[aid] = album.get("name") or "Unknown"
        album_plays[aid] += plays
        artists = song.get("artists") or []
        if not artists:
            artist_plays["unknown"] += plays
            artist_names["unknown"] = "Unknown"
        else:
            share = plays / len(artists) if plays else 0
            for a in artists:
                key = str(a.get("id") or a.get("name") or "unknown")
                artist_names[key] = a.get("name") or "Unknown"
                artist_plays[key] += share

    total_plays = sum(play_by_song.values())
    repeat_share = _top_share(list(play_by_song.values()), 0.1)
    artist_share = _top_share([int(v) for v in artist_plays.values()], 0.1)
    diversity = _effective_diversity(Counter({k: int(v) for k, v in artist_plays.items()}))

    recent_records = (data.get("records") or {}).get("recent") or []
    recent_ids = [str((x.get("song") or {}).get("id")) for x in recent_records]
    low_history_recent = sum(1 for sid in recent_ids if play_by_song.get(sid, 0) <= 2)
    exploration_proxy = (low_history_recent / len(recent_ids)) if recent_ids else None

    hidden = [
        {"id": sid, "name": name_by_song.get(sid, sid), "playCount": count}
        for sid, count in play_by_song.most_common()
        if sid not in liked and count > 0
    ][:12]

    week_song, week_song_names, week_artist, week_artist_names = _record_counters(week_records)
    playlists = data.get("playlists") or []
    created = [p for p in playlists if not p.get("subscribed")]
    subscribed = [p for p in playlists if p.get("subscribed")]
    playlist_tracks = {str(song.get("id")) for p in playlists for song in (p.get("tracks") or []) if song.get("id") is not None}
    playlist_declared_tracks = sum(int(p.get("trackCount") or 0) for p in playlists)
    playlist_fetched_tracks = sum(len(p.get("tracks") or []) for p in playlists)
    playlist_track_coverage = _pct(playlist_fetched_tracks / playlist_declared_tracks) if playlist_declared_tracks else None
    observed_song_ids = set(play_by_song)
    liked_observed = len(observed_song_ids & liked)

    playlist_rank = sorted(
        [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "trackCount": int(p.get("trackCount") or len(p.get("tracks") or [])),
                "playCount": int(p.get("playCount") or 0),
                "subscribed": bool(p.get("subscribed")),
            }
            for p in playlists
        ],
        key=lambda x: (x["trackCount"], x["playCount"]),
        reverse=True,
    )[:12]

    caps = data.get("capabilities") or {}
    expected = [
        "account", "profile", "user_level", "record_all", "record_week", "playlists",
        "playlist_tracks", "liked_ids", "recent_songs", "listen_total", "listen_realtime_week",
        "listen_realtime_month", "listen_report_year", "listen_year", "style_preference",
    ]
    available = [k for k in expected if caps.get(k)]

    profile = data.get("profile") or {}
    provider_payloads = data.get("providerPayloads") or {}
    return {
        "summary": {
            "knownPlays": total_plays,
            "uniqueSongs": len(play_by_song),
            "uniqueArtists": len(artist_plays),
            "uniqueAlbums": len(album_plays),
            "playlists": len(playlists),
            "createdPlaylists": len(created),
            "subscribedPlaylists": len(subscribed),
            "likedIds": len(liked),
            "likedObserved": liked_observed,
            "playlistKnownTracks": len(playlist_tracks),
            "playlistDeclaredTracks": playlist_declared_tracks,
            "playlistFetchedTracks": playlist_fetched_tracks,
            "playlistTrackCoverage": playlist_track_coverage,
            "recentObserved": len(recent_records),
            "accountLevel": profile.get("level"),
            "providerListenSongs": profile.get("listenSongs"),
            "accountAgeDays": profile.get("createDays"),
        },
        "indices": {
            "repeatIndex": _pct(repeat_share),
            "artistLoyalty": _pct(artist_share),
            "tasteDiversityEffectiveArtists": round(diversity, 1) if diversity is not None else None,
            "explorationProxy": _pct(exploration_proxy),
            "likedShareObserved": _pct(liked_observed / len(observed_song_ids)) if observed_song_ids else None,
        },
        "topSongs": [
            {"id": sid, "name": name_by_song.get(sid, sid), "playCount": count, "liked": sid in liked}
            for sid, count in play_by_song.most_common(12)
        ],
        "topArtists": [
            {"id": aid, "name": artist_names.get(aid, aid), "playCount": round(count, 1)}
            for aid, count in artist_plays.most_common(12)
        ],
        "topAlbums": [
            {"id": aid, "name": album_names.get(aid, aid), "playCount": count}
            for aid, count in album_plays.most_common(12)
        ],
        "weekSongs": [
            {"id": sid, "name": week_song_names.get(sid, sid), "playCount": count, "liked": sid in liked}
            for sid, count in week_song.most_common(10)
        ],
        "weekArtists": [
            {"id": aid, "name": week_artist_names.get(aid, aid), "playCount": round(count, 1)}
            for aid, count in week_artist.most_common(10)
        ],
        "topPlaylists": playlist_rank,
        "releaseDecades": _decades(data.get("songs") or []),
        "hiddenFavorites": hidden,
        "coverage": {
            "available": available,
            "missing": [k for k in expected if k not in available],
            "score": round(len(available) / len(expected) * 100),
        },
        "providerFacts": _provider_facts(provider_payloads),
        "providerShapes": {
            key: _shape(value)
            for key, value in provider_payloads.items()
        },
    }
