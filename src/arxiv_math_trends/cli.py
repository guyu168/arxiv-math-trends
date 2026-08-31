from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import analyze, load_counts, totals, write_metrics
from .svg import acceleration_chart


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/submissions_jan_jul.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    trends = analyze(load_counts(args.input))
    write_metrics(trends, args.output_dir / "category_metrics.csv")
    acceleration_chart(trends, Path("figures/growth_acceleration.svg"))
    aggregate = totals(trends)
    baseline = aggregate[2025] / aggregate[2024] - 1
    observed = aggregate[2026] / aggregate[2025] - 1
    expected_2026 = round(aggregate[2025] * (1 + baseline))
    print(f"categories: {len(trends)}")
    print(f"totals: {aggregate}")
    print(f"2026 baseline: {expected_2026:,}")
    print(f"2026 observed: {aggregate[2026]:,}")
    print(f"excess over baseline: {aggregate[2026] - expected_2026:,}")
    print(f"growth acceleration: {100 * (observed - baseline):.2f} pp")


if __name__ == "__main__":
    main()

