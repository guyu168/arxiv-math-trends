from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from arxiv_math_trends.harvest import normalize_author_key, write_metadata


DATA_DIR = Path("web/public/data/authors")
OUTPUT = Path("web/public/data/author_metadata.json")
START = date(2010, 1, 1)
END = date(2026, 8, 31)


def identity_key(author: dict[str, str]) -> str:
    return f"name:{normalize_author_key(author['name'])}"


def main() -> None:
    years = list(range(START.year, END.year + 1))
    total_papers = 0
    identities: set[str] = set()
    for year in years:
        snapshot = json.loads((DATA_DIR / f"{year}.json").read_text(encoding="utf-8"))
        total_papers += snapshot["paper_count"]
        identities.update(identity_key(author) for author in snapshot["authors"])
    write_metadata(OUTPUT, START, END, total_papers, len(identities), years)
    print(f"metadata: {total_papers:,} papers, {len(identities):,} author names")


if __name__ == "__main__":
    main()

