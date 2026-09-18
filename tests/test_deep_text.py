import unittest

from nelisten.deep_text import analyze_deep_text


class DeepTextTest(unittest.TestCase):
    def test_nmf_lsa_returns_aggregate_topics_only(self):
        lyrics = {}
        records = []
        recent = []
        for i in range(30):
            sid = str(i)
            if i < 15:
                lyrics[sid] = "城市 夜晚 回忆 月亮 离开 城市 夜晚 回忆"
            else:
                lyrics[sid] = "远方 明天 道路 海洋 未来 远方 明天 道路"
            song = {"id": sid, "name": f"S{i}", "artists": [{"id":"a","name":"A"}], "album": {"id":"x","name":"X"}}
            records.append({"song": song, "playCount": i + 1})
            if i >= 15:
                recent.append({"song": song, "playedAt": None})

        data = {
            "lyrics": lyrics,
            "records": {"all": records, "week": [], "recent": recent},
            "likedSongIds": list(lyrics),
        }
        result = analyze_deep_text(data, requested_topics=4)
        self.assertTrue(result["available"])
        self.assertGreaterEqual(len(result["topics"]), 2)
        self.assertIsNotNone(result["methodAgreementAMI"])
        self.assertNotIn("lyrics", result)
        self.assertIn("centroidCosineDistance", result["latent"])


if __name__ == "__main__":
    unittest.main()
