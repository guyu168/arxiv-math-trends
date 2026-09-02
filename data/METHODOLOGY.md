# Data methodology

## Category comparison

- Window: 1 January through 30 June in 2024, 2025, and 2026.
- Unit: papers whose arXiv **primary category** is one of the 32 `math.*`
  categories. A paper is counted once.
- Source: the official [arXiv API](https://info.arxiv.org/help/api/), queried
  by submission date in calendar-month slices.
- Frozen snapshot: 2 September 2026.

For category \(c\), the tables report:

- 2025 growth: `count(2025 H1) / count(2024 H1) - 1`;
- 2026 growth: `count(2026 H1) / count(2025 H1) - 1`;
- 2026 cumulative change from 2024: `count(2026 H1) / count(2024 H1) - 1`;
- growth acceleration: `2026 growth - 2025 growth`, in percentage points.

The equal six-month windows replace the repository's earlier January–July
comparison. They avoid comparing periods of different lengths and make the
"first half" label exact.

## Author explorer

The browser loads year-partitioned frozen daily snapshots covering 1 January 2010 through
31 August 2026. For a selected interval, each paper contributes one count to
every author identity listed in its arXiv metadata. Repeated identical identities
within one paper are collapsed before counting.

arXiv does not provide a stable person identifier for every author in this
feed, and its API does not expose author email addresses. The explorer therefore
uses the exact display name plus the author-submitted affiliation. Names and
affiliations are normalized only for Unicode form and whitespace. This separates
many common-name collisions, but missing affiliations can still combine people;
affiliation changes and spelling variants can split one person. The table is a
metadata-based activity ranking, not verified individual productivity.

The three field labels after each name are the identity's most frequent primary
mathematics categories inside the selected date range, ordered by paper count
and then category code. `PDE` is the display label for `math.AP`.

The 2010–2023 backfill is derived from the public arXiv OAI metadata snapshot
mirrored on Hugging Face. That mirror exposes author names and categories but
not affiliations, so historical identities in those years use the normalized
display name alone and are explicitly labeled as having no provided affiliation.
The 2024–2026 snapshots use affiliations supplied by the official arXiv API.

The explorer enforces a range longer than 15 days and only accepts dates inside
the frozen snapshot. Rebuild it with `arxiv-math-harvest` to extend the window.

## Interpretation limits

The analysis is descriptive. Classification changes, arXiv adoption,
collaboration size, moderation delays, seasonal submission timing, and author
name ambiguity are possible confounders. Growth acceleration is a two-interval
comparison, not evidence that any particular technology caused the change.
