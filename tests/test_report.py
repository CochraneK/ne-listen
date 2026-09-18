import tempfile
import unittest
from pathlib import Path

from nelisten.demo import synthetic_normalized
from nelisten.metrics import analyze
from nelisten.report import render


class ReportTest(unittest.TestCase):
    def test_report_is_visitor_first_and_keeps_methodology_secondary(self):
        data = synthetic_normalized()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "index.html"
            render(data, analyze(data), out)
            body = out.read_text(encoding="utf-8")
            self.assertIn("A PERSONAL LISTENING ARCHIVE", body)
            self.assertIn("最近在听", body)
            self.assertIn("有些声音，会一直回来。", body)
            self.assertIn("我的音乐版图", body)
            self.assertIn("<details>", body)
            self.assertIn("数据说明", body)
            self.assertNotIn("Data coverage</h2>", body)


if __name__ == "__main__":
    unittest.main()
