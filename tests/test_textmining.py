import unittest

from nelisten.demo import synthetic_normalized
from nelisten.textmining import analyze_text, clean_lyric, select_text_corpus_song_ids, tokenize


class TextMiningTest(unittest.TestCase):
    def test_cleaning_removes_timestamps_and_credits(self):
        text = "[00:01.00]作词：Someone\n[00:02.00]夜色落在旧城\n[00:03.00]明天去远方"
        cleaned = clean_lyric(text)
        self.assertNotIn("00:01", cleaned)
        self.assertNotIn("作词", cleaned)
        self.assertIn("夜色", cleaned)

    def test_synthetic_text_analysis_is_private_and_nonempty(self):
        data = synthetic_normalized()
        result = analyze_text(data)
        self.assertTrue(result["available"])
        self.assertEqual(result["songsWithLyrics"], 7)
        self.assertGreater(len(result["topTerms"]), 0)
        self.assertIn("jensenShannon", result["drift"])
        self.assertNotIn("lyrics", result)

    def test_corpus_selection_prioritizes_behavioral_evidence(self):
        data = synthetic_normalized()
        ids = select_text_corpus_song_ids(data, max_songs=3)
        self.assertEqual(len(ids), 3)
        self.assertIn("1", ids)

    def test_tokenize_handles_mixed_language(self):
        tokens = tokenize("夜色落在城市 city lights future road")
        self.assertTrue(any(token == "city" for token in tokens))
        self.assertTrue(any(len(token) >= 2 for token in tokens))


if __name__ == "__main__":
    unittest.main()
