import unittest

from scripts.enrich_orcid import enrich_snapshot, match_authorships


class OrcidEnrichmentTests(unittest.TestCase):
    def test_matches_reordered_name_tokens(self) -> None:
        authorships = [
            {
                "raw_author_name": "Lovelace, Ada",
                "author": {
                    "display_name": "Ada Lovelace",
                    "id": "https://openalex.org/A1",
                    "orcid": "https://orcid.org/0000-0001-2345-6789",
                },
            }
        ]
        self.assertIs(match_authorships(["Ada Lovelace"], authorships)[0], authorships[0])

    def test_enrichment_separates_same_name_by_orcid(self) -> None:
        snapshot = {
            "min_date": "2026-01-01",
            "max_date": "2026-12-31",
            "paper_count": 2,
            "authors": [{"name": "Wei Wang", "orcid": "", "openalex_id": ""}],
            "categories": ["math.AG", "math.AP"],
            "paper_days": {"2026-01-01": 1, "2026-01-02": 1},
            "days": {},
            "papers": {
                "2026-01-01": [["2601.00001", 0, [0]]],
                "2026-01-02": [["2601.00002", 1, [0]]],
            },
        }
        works = {
            "2601.00001": {
                "authorships": [
                    {
                        "raw_author_name": "Wei Wang",
                        "author": {
                            "display_name": "Wei Wang",
                            "id": "https://openalex.org/A1",
                            "orcid": "https://orcid.org/0000-0001-1111-1111",
                        },
                    }
                ]
            },
            "2601.00002": {
                "authorships": [
                    {
                        "raw_author_name": "Wei Wang",
                        "author": {
                            "display_name": "Wei Wang",
                            "id": "https://openalex.org/A2",
                            "orcid": "https://orcid.org/0000-0002-2222-2222",
                        },
                    }
                ]
            },
        }
        enriched = enrich_snapshot(snapshot, works)
        self.assertNotIn("papers", enriched)
        self.assertEqual(len(enriched["authors"]), 2)
        self.assertEqual(
            {author["orcid"] for author in enriched["authors"]},
            {"0000-0001-1111-1111", "0000-0002-2222-2222"},
        )
        self.assertEqual(enriched["days"]["2026-01-01"], [[0, 0, 1]])
        self.assertEqual(enriched["days"]["2026-01-02"], [[1, 1, 1]])


if __name__ == "__main__":
    unittest.main()

