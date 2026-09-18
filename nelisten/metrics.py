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

    recent_ids = [str((x.get("song") or {}).get("id")) for x in ((data.get("records") or {}).get("recent") or [])]
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
    }
