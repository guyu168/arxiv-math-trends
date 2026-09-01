import unittest
from datetime import date

from arxiv_math_trends.harvest import Paper, build_snapshot, month_ranges, parse_atom, query_url


SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <opensearch:totalResults>3</opensearch:totalResults>
  <entry>
    <published>2026-02-03T10:00:00Z</published>
    <arxiv:primary_category term="math.AG"/>
    <author><name>Ada  Lovelace</name></author>
    <author><name>Emmy Noether</name></author>
  </entry>
  <entry>
    <published>2026-02-04T09:00:00Z</published>
    <arxiv:primary_category term="cs.IT"/>
    <author><name>Claude Shannon</name></author>
  </entry>
  <entry>
    <published>2026-02-04T10:00:00Z</published>
    <arxiv:primary_category term="cs.LG"/>
    <author><name>Ignored Crosslist</name></author>
  </entry>
</feed>
"""


class HarvestTests(unittest.TestCase):
    def test_parse_atom_keeps_primary_math_papers(self) -> None:
        total, papers = parse_atom(SAMPLE)
        self.assertEqual(total, 3)
        self.assertEqual(len(papers), 2)
        self.assertEqual(papers[0].authors, ("Ada Lovelace", "Emmy Noether"))
        self.assertEqual(papers[1].primary_category, "math.IT")

    def test_query_contains_date_bounds(self) -> None:
        url = query_url(date(2026, 1, 1), date(2026, 1, 31), 0, 100)
        self.assertIn("submittedDate", url)
        self.assertIn("cs.IT", url)
        self.assertIn("math-ph", url)
        self.assertIn("202601010000", url)
        self.assertIn("202601312359", url)

    def test_month_ranges_cover_interval(self) -> None:
        self.assertEqual(
            month_ranges(date(2026, 1, 15), date(2026, 3, 2)),
            [
                (date(2026, 1, 15), date(2026, 1, 31)),
                (date(2026, 2, 1), date(2026, 2, 28)),
                (date(2026, 3, 1), date(2026, 3, 2)),
            ],
        )

    def test_snapshot_counts_authors_once_per_paper(self) -> None:
        papers = [
            Paper(date(2026, 1, 1), "math.AG", ("Ada", "Ada", "Emmy")),
            Paper(date(2026, 1, 2), "math.AG", ("Ada",)),
        ]
        snapshot = build_snapshot(papers, date(2026, 1, 1), date(2026, 1, 2))
        ada_id = snapshot["authors"].index("Ada")
        self.assertEqual(snapshot["paper_count"], 2)
        self.assertEqual(snapshot["paper_days"], {"2026-01-01": 1, "2026-01-02": 1})
        self.assertEqual(snapshot["days"]["2026-01-01"], [[ada_id, 1], [1, 1]])


if __name__ == "__main__":
    unittest.main()
