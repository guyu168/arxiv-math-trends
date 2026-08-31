import tempfile
import unittest
from pathlib import Path

from arxiv_math_trends.analysis import analyze, load_counts, totals, write_metrics


ROOT = Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trends = analyze(load_counts(ROOT / "data" / "submissions_jan_jul.csv"))

    def test_snapshot_has_all_categories(self) -> None:
        self.assertEqual(len(self.trends), 32)

    def test_totals_match_source_snapshot(self) -> None:
        self.assertEqual(totals(self.trends), {2024: 25625, 2025: 25863, 2026: 32924})

    def test_sorted_by_acceleration(self) -> None:
        values = [item.acceleration for item in self.trends]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual(self.trends[0].category, "math.GM")

    def test_metrics_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "metrics.csv"
            write_metrics(self.trends, target)
            self.assertIn("acceleration_pp", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

