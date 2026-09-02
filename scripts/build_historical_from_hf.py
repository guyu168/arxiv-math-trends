from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path

from datasets import load_dataset

from arxiv_math_trends.harvest import (
    AuthorIdentity,
    PRIMARY_ALIASES,
    Paper,
    build_snapshot,
    normalize_author,
    write_metadata,
    write_snapshot,
)


START = date(2010, 1, 1)
HISTORICAL_END = date(2023, 12, 31)
SNAPSHOT_END = date(2026, 8, 31)
OUTPUT_DIR = Path("web/public/data/authors")
METADATA_PATH = Path("web/public/data/author_metadata.json")


def author_name(parts: list[str]) -> str:
    last, first, suffix = (list(parts) + ["", "", ""])[:3]
    return normalize_author(" ".join(piece for piece in (first, last, suffix) if piece))


def main() -> None:
    papers_by_year: dict[int, list[Paper]] = defaultdict(list)
    stream = load_dataset(
        "anuj0456/arxiv-dataset",
        split="train",
        streaming=True,
    ).select_columns(["id", "authors_parsed", "categories", "versions"])

    for record in stream:
        versions = record.get("versions") or []
        if not versions or not versions[0].get("created"):
            continue
        published = parsedate_to_datetime(versions[0]["created"]).date()
        if published < START or published > HISTORICAL_END:
            continue
        category_tokens = (record.get("categories") or "").split()
        if not category_tokens:
            continue
        primary = PRIMARY_ALIASES.get(category_tokens[0], category_tokens[0])
        if not primary.startswith("math."):
            continue
        authors = tuple(
            AuthorIdentity(name)
            for parts in (record.get("authors_parsed") or [])
            for name in [author_name(parts)]
            if name
        )
        if authors:
            papers_by_year[published.year].append(
                Paper(str(record.get("id") or ""), published, primary, authors)
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for year in range(START.year, HISTORICAL_END.year + 1):
        papers = papers_by_year[year]
        snapshot = build_snapshot(papers, date(year, 1, 1), date(year, 12, 31))
        write_snapshot(snapshot, OUTPUT_DIR / f"{year}.json")
        print(f"{year}: {len(papers):,} papers, {len(snapshot['authors']):,} identities")

    all_identities: set[tuple[str, str, str]] = set()
    total_papers = 0
    years = list(range(START.year, SNAPSHOT_END.year + 1))
    for year in years:
        with (OUTPUT_DIR / f"{year}.json").open(encoding="utf-8") as handle:
            snapshot = json.load(handle)
        total_papers += snapshot["paper_count"]
        all_identities.update(
            (
                author["name"],
                author.get("orcid", ""),
                author.get("openalex_id", ""),
            )
            for author in snapshot["authors"]
        )

    write_metadata(
        METADATA_PATH,
        START,
        SNAPSHOT_END,
        total_papers,
        len(all_identities),
        years,
    )
    print(f"snapshot: {total_papers:,} papers, {len(all_identities):,} identities")


if __name__ == "__main__":
    main()

