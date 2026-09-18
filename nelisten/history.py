from __future__ import annotations

from typing import Any


def _safe_snapshot(metrics: dict[str, Any], collected_at: str | None) -> dict[str, Any]:
    summary = metrics.get("summary") or {}
    indices = metrics.get("indices") or {}
    text = metrics.get("text") or {}
    deep = metrics.get("deepText") or {}
    network = metrics.get("network") or {}
    return {
        "date": str(collected_at or "")[:10] or None,
        "summary": {
            "providerListenSongs": summary.get("providerListenSongs"),
            "likedIds": summary.get("likedIds"),
            "playlists": summary.get("playlists"),
            "playlistKnownTracks": summary.get("playlistKnownTracks"),
        },
        "indices": {
            "repeatIndex": indices.get("repeatIndex"),
            "artistLoyalty": indices.get("artistLoyalty"),
            "tasteDiversityEffectiveArtists": indices.get("tasteDiversityEffectiveArtists"),
            "recentOutsideTop100": indices.get("recentOutsideTop100"),
        },
        "text": {
            "coverage": text.get("coverage"),
            "topTerms": [x.get("term") for x in (text.get("topTerms") or [])[:10]],
            "jensenShannon": (text.get("drift") or {}).get("jensenShannon"),
        },
        "deepText": {
            "effectiveTopics": deep.get("effectiveTopics"),
            "methodAgreementAMI": deep.get("methodAgreementAMI"),
            "centroidCosineDistance": (deep.get("latent") or {}).get("centroidCosineDistance"),
        },
        "network": {
            "averageJaccard": network.get("averageJaccard"),
            "multiPlaylistShare": network.get("multiPlaylistShare"),
        },
    }


def merge_history(previous: Any, metrics: dict[str, Any], collected_at: str | None, limit: int = 400) -> dict[str, Any]:
    snapshots = []
    if isinstance(previous, dict) and isinstance(previous.get("snapshots"), list):
        snapshots = [x for x in previous["snapshots"] if isinstance(x, dict)]

    current = _safe_snapshot(metrics, collected_at)
    date = current.get("date")
    if date:
        snapshots = [x for x in snapshots if x.get("date") != date]
    snapshots.append(current)
    snapshots = snapshots[-limit:]
    return {"schemaVersion": "history-v1", "snapshots": snapshots}
