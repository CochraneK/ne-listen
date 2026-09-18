import unittest

from nelisten.demo import synthetic_normalized
from nelisten.metrics import analyze


class MetricsTest(unittest.TestCase):
    def test_demo_metrics(self):
        m = analyze(synthetic_normalized())
        self.assertEqual(m["summary"]["knownPlays"], 138)
        self.assertEqual(m["summary"]["uniqueSongs"], 10)
        self.assertGreater(m["indices"]["repeatIndex"], 0)
        self.assertGreater(m["indices"]["tasteDiversityEffectiveArtists"], 1)
        self.assertTrue(any(x["name"] == "一丝不挂" for x in m["hiddenFavorites"]))

    def test_coverage_is_explicit(self):
        m = analyze(synthetic_normalized())
        self.assertIn("listen_total", m["coverage"]["missing"])
        self.assertIn("record_all", m["coverage"]["available"])


if __name__ == "__main__":
    unittest.main()
