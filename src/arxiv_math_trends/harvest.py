from __future__ import annotations

import argparse
import csv
import json
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


API_URL = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
USER_AGENT = "arxiv-math-trends/2.0 (https://github.com/guyu168/arxiv-math-trends)"
PRIMARY_ALIASES = {"cs.IT": "math.IT", "math-ph": "math.MP"}


@dataclass(frozen=True)
class Paper:
    published: date
    primary_category: str
    authors: tuple[str, ...]


def normalize_author(name: str) -> str:
    return " ".join(unicodedata.normalize("NFC", name).split())


def query_url(start_date: date, end_date: date, offset: int, page_size: int) -> str:
    query = (
        "(cat:math.* OR cat:cs.IT OR cat:math-ph) AND submittedDate:"
        f"[{start_date:%Y%m%d}0000 TO {end_date:%Y%m%d}2359]"
    )
    parameters = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": offset,
            "max_results": page_size,
            "sortBy": "submittedDate",
            "sortOrder": "ascending",
        }
    )
    return f"{API_URL}?{parameters}"


def parse_atom(text: str) -> tuple[int, list[Paper]]:
    root = ET.fromstring(text)
    total_node = root.find(f"{OPENSEARCH}totalResults")
    if total_node is None or total_node.text is None:
        raise ValueError("arXiv response is missing totalResults")
    papers: list[Paper] = []
    for entry in root.findall(f"{ATOM}entry"):
        published_node = entry.find(f"{ATOM}published")
        primary_node = entry.find(f"{ARXIV}primary_category")
        if published_node is None or published_node.text is None or primary_node is None:
            continue
        primary = primary_node.attrib.get("term", "")
        primary = PRIMARY_ALIASES.get(primary, primary)
        if not primary.startswith("math."):
            continue
        authors = tuple(
            name
            for author in entry.findall(f"{ATOM}author")
            for node in [author.find(f"{ATOM}name")]
            if node is not None and node.text
            for name in [normalize_author(node.text)]
            if name
        )
        if not authors:
            continue
        papers.append(
            Paper(
                published=date.fromisoformat(published_node.text[:10]),
                primary_category=primary,
                authors=authors,
            )
        )
    return int(total_node.text), papers


def _download(url: str, retries: int = 6) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == retries - 1:
                raise
            wait = int(error.headers.get("Retry-After", 10 * (attempt + 1)))
            time.sleep(wait)
        except urllib.error.URLError:
            if attempt == retries - 1:
                raise
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("unreachable")


def fetch_range(
    start_date: date,
    end_date: date,
    cache_dir: str | Path,
    *,
    page_size: int = 2_000,
    delay_seconds: float = 5.0,
) -> list[Paper]:
    if end_date < start_date:
        raise ValueError("end date must not precede start date")
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    papers: list[Paper] = []
    offset, total = 0, None
    while total is None or offset < total:
        target = cache / f"v2_{start_date}_{end_date}_{offset:05d}.xml"
        if target.exists():
            text = target.read_text(encoding="utf-8")
        else:
            text = _download(query_url(start_date, end_date, offset, page_size))
            target.write_text(text, encoding="utf-8")
            time.sleep(delay_seconds)
        total, page = parse_atom(text)
        papers.extend(page)
        offset += page_size
    return papers


def half_year_ranges(start_date: date, end_date: date) -> list[tuple[date, date]]:
    ranges = []
    cursor = start_date
    while cursor <= end_date:
        boundary = date(cursor.year, 6, 30) if cursor.month <= 6 else date(cursor.year, 12, 31)
        chunk_end = min(boundary, end_date)
        ranges.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return ranges


def month_ranges(start_date: date, end_date: date) -> list[tuple[date, date]]:
    ranges = []
    cursor = start_date
    while cursor <= end_date:
        next_month = (
            date(cursor.year + 1, 1, 1)
            if cursor.month == 12
            else date(cursor.year, cursor.month + 1, 1)
        )
        chunk_end = min(next_month - timedelta(days=1), end_date)
        ranges.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return ranges


def build_snapshot(papers: list[Paper], start_date: date, end_date: date) -> dict[str, object]:
    filtered = [paper for paper in papers if start_date <= paper.published <= end_date]
    names = sorted({author for paper in filtered for author in paper.authors}, key=str.casefold)
    author_ids = {name: index for index, name in enumerate(names)}
    daily: dict[str, Counter[int]] = defaultdict(Counter)
    paper_days: Counter[str] = Counter()
    for paper in filtered:
        paper_days[paper.published.isoformat()] += 1
        for author in set(paper.authors):
            daily[paper.published.isoformat()][author_ids[author]] += 1
    return {
        "min_date": start_date.isoformat(),
        "max_date": end_date.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paper_count": len(filtered),
        "authors": names,
        "paper_days": dict(sorted(paper_days.items())),
        "days": {
            day: [[author_id, count] for author_id, count in sorted(counts.items())]
            for day, counts in sorted(daily.items())
        },
    }


def write_snapshot(snapshot: dict[str, object], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def write_half_year_counts(
    papers: list[Paper],
    category_source: str | Path,
    path: str | Path,
) -> None:
    with Path(category_source).open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    categories = {row["category"]: row["category_name"] for row in source_rows}
    years = (2024, 2025, 2026)
    counts = {category: Counter() for category in categories}
    for paper in papers:
        if paper.published.year in years and paper.published.month <= 6:
            if paper.primary_category in counts:
                counts[paper.primary_category][paper.published.year] += 1
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["category", "category_name", *years])
        for category, name in categories.items():
            writer.writerow([category, name, *(counts[category][year] for year in years)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a daily arXiv mathematics author snapshot")
    parser.add_argument("--start", type=date.fromisoformat, default=date(2024, 1, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 8, 31))
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/arxiv"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("web/public/data/author_daily.json"),
    )
    parser.add_argument(
        "--category-source",
        type=Path,
        default=Path("data/categories.csv"),
    )
    parser.add_argument(
        "--counts-output",
        type=Path,
        default=Path("data/submissions_h1.csv"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    papers = [
        paper
        for chunk_start, chunk_end in month_ranges(args.start, args.end)
        for paper in fetch_range(chunk_start, chunk_end, args.cache_dir)
    ]
    snapshot = build_snapshot(papers, args.start, args.end)
    write_snapshot(snapshot, args.output)
    write_half_year_counts(papers, args.category_source, args.counts_output)
    print(
        f"snapshot: {snapshot['paper_count']:,} papers, "
        f"{len(snapshot['authors']):,} author names"
    )


if __name__ == "__main__":
    main()
