import unittest

from nelisten.history import merge_history


class HistoryTest(unittest.TestCase):
    def test_same_day_replaces_snapshot_and_excludes_raw_content(self):
        metrics = {
            "summary": {"likedIds": 10, "playlists": 2},
            "indices": {"repeatIndex": 30.0},
            "text": {"coverage": 90.0, "topTerms": [{"term":"回忆"}], "drift":{"jensenShannon":0.2}},
            "deepText": {"effectiveTopics": 3.0, "methodAgreementAMI":0.3, "latent":{"centroidCosineDistance":0.1}},
            "network": {"averageJaccard":1.0, "multiPlaylistShare":5.0},
        }
        h1 = merge_history({}, metrics, "2026-09-18T01:00:00Z")
        metrics["summary"]["likedIds"] = 11
        h2 = merge_history(h1, metrics, "2026-09-18T12:00:00Z")
        self.assertEqual(len(h2["snapshots"]), 1)
        self.assertEqual(h2["snapshots"][0]["summary"]["likedIds"], 11)
        self.assertNotIn("lyrics", str(h2))


if __name__ == "__main__":
    unittest.main()
