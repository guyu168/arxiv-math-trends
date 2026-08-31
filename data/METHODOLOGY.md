# Data methodology

- Window: 1 January through 31 July in each year.
- Unit: arXiv primary-category submissions. A paper is counted once.
- Categories: the 32 `math.*` primary categories in the arXiv taxonomy.
- Sources: annual mathematics listings for [2024](https://arxiv.org/year/math/2024), [2025](https://arxiv.org/year/math/2025), and [2026](https://arxiv.org/year/math/2026).
- Frozen snapshot: 7 August 2026.

The repository deliberately commits a small, auditable snapshot rather than
silently querying a changing page on every run. The analysis validates the
schema and totals before calculating any rates.

For category \(c\), the reported acceleration is

`growth(2025 -> 2026) - growth(2024 -> 2025)`.

This is a descriptive baseline, not a causal estimate of AI's effect on
mathematical research. Classification changes, arXiv adoption, collaboration
patterns, and submission timing are possible confounders.

