from __future__ import annotations

from datetime import datetime, timezone


def synthetic_normalized() -> dict:
    songs = [
        ("1", "雨下一整晚", "周杰伦", "跨时代", 31),
        ("2", "City of Stars", "Ryan Gosling & Emma Stone", "La La Land", 24),
        ("3", "富士山下", "陈奕迅", "What's Going On...?", 21),
        ("4", "The Less I Know The Better", "Tame Impala", "Currents", 18),
        ("5", "一丝不挂", "陈奕迅", "Time Flies", 15),
        ("6", "Space Song", "Beach House", "Depression Cherry", 11),
        ("7", "春夏秋冬", "张国荣", "陪你倒数", 9),
        ("8", "505", "Arctic Monkeys", "Favourite Worst Nightmare", 6),
        ("9", "Random New Track", "New Artist", "New Album", 2),
        ("10", "Another New Track", "Another Artist", "New Album", 1),
    ]
    records = []
    song_objs = []
    for sid, name, artist, album, count in songs:
        song = {"id": sid, "name": name, "artists": [{"id": artist, "name": artist}], "album": {"id": album, "name": album}}
        song_objs.append(song)
        records.append({"song": song, "playCount": count, "score": None})
    recent = [{"song": song_objs[i], "playedAt": None} for i in [8,9,0,3,5,8,2]]
    return {
        "schemaVersion": "normalized-v1",
        "source": "synthetic-demo",
        "collectedAt": datetime.now(timezone.utc).isoformat(),
        "profile": {"userId": "demo", "nickname": "Demo listener", "avatarUrl": None, "signature": None},
        "songs": song_objs,
        "records": {"all": records, "week": [], "recent": recent},
        "likedSongIds": ["1","2","3","4","6"],
        "playlists": [{"id":"p1","name":"Night","trackCount":35,"subscribed":False},{"id":"p2","name":"Focus","trackCount":52,"subscribed":False},{"id":"p3","name":"Collected","trackCount":120,"subscribed":True}],
        "providerPayloads": {},
        "capabilities": {"account":True,"profile":True,"record_all":True,"playlists":True,"liked_ids":True,"recent_songs":True,"listen_total":False,"listen_realtime":False,"style_preference":False},
    }
