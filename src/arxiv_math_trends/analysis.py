from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


EXPECTED_YEARS = (2024, 2025, 2026)


@dataclass(frozen=True)
class CategoryTrend:
    category: str
    name: str
    count_2024: int
    count_2025: int
    count_2026: int
    baseline_growth: float
    current_growth: float
    growth_2026_vs_2024: float
    acceleration: float


def _growth(previous: int, current: int) -> float:
    if previous <= 0:
        raise ValueError("submission counts must be positive")
    return current / previous - 1.0


def load_counts(path: str | Path) -> list[dict[str, str]]:
    source = Path(path)
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"category", "category_name", *(str(y) for y in EXPECTED_YEARS)}
        if set(reader.fieldnames or ()) != required:
            raise ValueError(f"unexpected columns: {reader.fieldnames}")
        rows = list(reader)

    if len(rows) != 32:
        raise ValueError(f"expected 32 mathematics categories, found {len(rows)}")
    if len({row["category"] for row in rows}) != len(rows):
        raise ValueError("duplicate category codes")
    return rows


def analyze(rows: Iterable[dict[str, str]]) -> list[CategoryTrend]:
    trends: list[CategoryTrend] = []
    for row in rows:
        counts = [int(row[str(year)]) for year in EXPECTED_YEARS]
        if any(value <= 0 for value in counts):
            raise ValueError(f"non-positive count for {row['category']}")
        baseline = _growth(counts[0], counts[1])
        current = _growth(counts[1], counts[2])
        trends.append(
            CategoryTrend(
                category=row["category"],
                name=row["category_name"],
                count_2024=counts[0],
                count_2025=counts[1],
                count_2026=counts[2],
                baseline_growth=baseline,
                current_growth=current,
                growth_2026_vs_2024=_growth(counts[0], counts[2]),
                acceleration=current - baseline,
            )
        )
    return sorted(trends, key=lambda item: item.acceleration, reverse=True)


def totals(trends: Iterable[CategoryTrend]) -> dict[int, int]:
    items = list(trends)
    return {
        2024: sum(item.count_2024 for item in items),
        2025: sum(item.count_2025 for item in items),
        2026: sum(item.count_2026 for item in items),
    }


def write_metrics(trends: Iterable[CategoryTrend], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "category",
        "category_name",
        "count_2024",
        "count_2025",
        "count_2026",
        "baseline_growth_pct",
        "current_growth_pct",
        "growth_2026_vs_2024_pct",
        "acceleration_pp",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in trends:
            writer.writerow(
                {
                    "category": item.category,
                    "category_name": item.name,
                    "count_2024": item.count_2024,
                    "count_2025": item.count_2025,
                    "count_2026": item.count_2026,
                    "baseline_growth_pct": f"{100 * item.baseline_growth:.2f}",
                    "current_growth_pct": f"{100 * item.current_growth:.2f}",
                    "growth_2026_vs_2024_pct": f"{100 * item.growth_2026_vs_2024:.2f}",
                    "acceleration_pp": f"{100 * item.acceleration:.2f}",
                }
            )
