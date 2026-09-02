from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from arxiv_math_trends.harvest import write_metadata


DATA_DIR = Path("web/public/data/authors")
OUTPUT = Path("web/public/data/author_metadata.json")
START = date(2010, 1, 1)
END = date(2026, 8, 31)


def identity_key(author: dict[str, str]) -> str:
    if author.get("orcid"):
        return f"orcid:{author['orcid']}"
    if author.get("openalex_id"):
        return f"openalex:{author['openalex_id']}"
    return f"name:{author['name'].casefold()}"


def main() -> None:
    years = list(range(START.year, END.year + 1))
    total_papers = 0
    identities: set[str] = set()
    for year in years:
        snapshot = json.loads((DATA_DIR / f"{year}.json").read_text(encoding="utf-8"))
        total_papers += snapshot["paper_count"]
        identities.update(identity_key(author) for author in snapshot["authors"])
    write_metadata(OUTPUT, START, END, total_papers, len(identities), years)
    print(f"metadata: {total_papers:,} papers, {len(identities):,} identities")


if __name__ == "__main__":
    main()

