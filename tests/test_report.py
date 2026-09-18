import tempfile
import unittest
from pathlib import Path

from nelisten.demo import synthetic_normalized
from nelisten.metrics import analyze
from nelisten.report import render


class ReportTest(unittest.TestCase):
    def test_report_contains_core_sections(self):
        data = synthetic_normalized()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "index.html"
            render(data, analyze(data), out)
            body = out.read_text(encoding="utf-8")
            self.assertIn("Your listening life", body)
            self.assertIn("Data coverage", body)
            self.assertIn("Repeat Index", body)


if __name__ == "__main__":
    unittest.main()
