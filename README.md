# arXiv Mathematics Submission Trends

[![CI](https://github.com/guyu168/arxiv-math-trends/actions/workflows/ci.yml/badge.svg)](https://github.com/guyu168/arxiv-math-trends/actions/workflows/ci.yml)

A compact, auditable study of January-July submission growth across all 32
arXiv mathematics primary categories. The project separates the observed
2025-2026 growth rate from a simple 2024-2025 baseline and makes the limits of
that comparison explicit.

![Growth acceleration by category](figures/growth_acceleration.svg)

## Results

| Metric | Value |
|---|---:|
| 2024 submissions | 25,625 |
| 2025 submissions | 25,863 |
| 2026 submissions | 32,924 |
| 2026 baseline projection | 26,103 |
| Observed minus baseline | 6,821 |
| Aggregate growth acceleration | 26.4 pp |

The break is broad rather than confined to one subject: 31 of 32 categories
grew in 2026, and 30 of 32 accelerated relative to the baseline. This pattern
is consistent with an AI-era increase in visible mathematical output, but the
design is descriptive and does **not** identify AI as the unique cause.

## What this repository demonstrates

- a documented data definition and frozen source snapshot;
- schema, uniqueness, positivity, and aggregate-total validation;
- reproducible rate and acceleration calculations;
- dependency-free SVG reporting;
- automated tests and continuous integration.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e .
arxiv-math-trends
python -m unittest discover -s tests -v
```

Generated category metrics are written to `outputs/category_metrics.csv`.

## Data and limitations

See [`data/METHODOLOGY.md`](data/METHODOLOGY.md) for the counting window,
primary-category rule, source pages, formula, and confounders. Small categories
can show large percentage swings, and a one-year baseline is statistically
fragile. The analysis should therefore be read as exploratory evidence, not a
causal claim.

## Author

Guyu Jin — Graduate School of Mathematical Sciences, The University of Tokyo.

