import unittest

from nelisten.semantic import _chunks, unavailable


class SemanticTest(unittest.TestCase):
    def test_chunks_do_not_expose_timestamps(self):
        chunks = _chunks("[00:01]第一行\n[00:02]第二行\n[00:03]第三行", lines_per_chunk=2)
        self.assertEqual(len(chunks), 2)
        self.assertNotIn("00:01", chunks[0])

    def test_unavailable_schema_is_public_safe(self):
        result = unavailable("missing")
        self.assertFalse(result["available"])
        self.assertFalse(result["safety"]["containsLyrics"])
        self.assertFalse(result["safety"]["containsSongIds"])
        self.assertFalse(result["safety"]["containsEmbeddings"])


if __name__ == "__main__":
    unittest.main()
