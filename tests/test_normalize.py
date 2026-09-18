import unittest

from nelisten.normalize import normalize


class NormalizeTest(unittest.TestCase):
    def test_record_and_likes(self):
        raw = {
            "schemaVersion":"raw-v1","source":"test","collectedAt":"x","uid":"42",
            "responses":{
                "profile":{"ok":True,"data":{"profile":{"userId":42,"nickname":"N"}}},
                "record_all":{"ok":True,"data":{"allData":[{"playCount":7,"song":{"id":1,"name":"S","ar":[{"id":2,"name":"A"}],"al":{"id":3,"name":"AL"}}}]}},
                "record_week":{"ok":False},
                "recent_songs":{"ok":False},
                "liked_ids":{"ok":True,"data":{"ids":[1]}},
                "playlists":{"ok":True,"data":{"playlist":[]}},
            }
        }
        d = normalize(raw)
        self.assertEqual(d["profile"]["nickname"], "N")
        self.assertEqual(d["records"]["all"][0]["playCount"], 7)
        self.assertEqual(d["likedSongIds"], ["1"])


if __name__ == "__main__":
    unittest.main()
