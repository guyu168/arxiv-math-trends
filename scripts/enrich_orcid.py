from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OPENALEX_URL = "https://api.openalex.org/works"
USER_AGENT = "arxiv-math-trends/3.0 (https://github.com/guyu168/arxiv-math-trends)"
BATCH_SIZE = 100


def normalize_name(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).casefold()
    return " ".join(re.findall(r"[a-z0-9]+", folded))


def name_tokens(value: str) -> tuple[str, ...]:
    return tuple(sorted(normalize_name(value).split()))


def prefix_equivalent(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    if len(left) != len(right):
        return False
    remaining = list(right)
    for token in sorted(left, key=len, reverse=True):
        match = next(
            (
                candidate
                for candidate in remaining
                if token == candidate
                or (len(token) == 1 and candidate.startswith(token))
                or (len(candidate) == 1 and token.startswith(candidate))
            ),
            None,
        )
        if match is None:
            return False
        remaining.remove(match)
    return True


def authorship_names(authorship: dict[str, Any]) -> list[str]:
    author = authorship.get("author") or {}
    return [
        name
        for name in (
            authorship.get("raw_author_name"),
            author.get("display_name"),
        )
        if name
    ]


def match_authorships(
    local_names: list[str], authorships: list[dict[str, Any]]
) -> list[dict[str, Any] | None]:
    matched: list[dict[str, Any] | None] = [None] * len(local_names)
    unused = set(range(len(authorships)))

    for local_index, local_name in enumerate(local_names):
        signature = name_tokens(local_name)
        candidates = [
            index
            for index in unused
            if any(name_tokens(name) == signature for name in authorship_names(authorships[index]))
        ]
        if len(candidates) == 1:
            index = candidates[0]
            matched[local_index] = authorships[index]
            unused.remove(index)

    for local_index, local_name in enumerate(local_names):
        if matched[local_index] is not None:
            continue
        signature = name_tokens(local_name)
        candidates = [
            index
            for index in unused
            if any(
                prefix_equivalent(signature, name_tokens(name))
                for name in authorship_names(authorships[index])
            )
        ]
        if len(candidates) == 1:
            index = candidates[0]
            matched[local_index] = authorships[index]
            unused.remove(index)

    if len(local_names) == len(authorships):
        for index, local_name in enumerate(local_names):
            if matched[index] is not None or index not in unused:
                continue
            local = set(name_tokens(local_name))
            remote = {
                token
                for name in authorship_names(authorships[index])
                for token in name_tokens(name)
            }
            if local & remote:
                matched[index] = authorships[index]
                unused.remove(index)
    return matched


def canonical_orcid(value: str | None) -> str:
    return (value or "").rstrip("/").rsplit("/", 1)[-1]


def canonical_openalex(value: str | None) -> str:
    return (value or "").rstrip("/").rsplit("/", 1)[-1]


def arxiv_id_from_doi(value: str | None) -> str:
    doi = (value or "").lower()
    marker = "10.48550/arxiv."
    if marker not in doi:
        return ""
    return urllib.parse.unquote(doi.split(marker, 1)[1])


def fetch_openalex(arxiv_ids: list[str], delay_seconds: float = 0.12) -> dict[str, Any]:
    works: dict[str, Any] = {}
    identifiers = sorted({identifier.lower() for identifier in arxiv_ids if identifier})
    for offset in range(0, len(identifiers), BATCH_SIZE):
        batch = identifiers[offset : offset + BATCH_SIZE]
        query = urllib.parse.urlencode(
            {
                "filter": "doi:"
                + "|".join(f"10.48550/arxiv.{identifier}" for identifier in batch),
                "per-page": 200,
                "select": "id,doi,authorships",
            }
        )
        request = urllib.request.Request(
            f"{OPENALEX_URL}?{query}", headers={"User-Agent": USER_AGENT}
        )
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    payload = json.load(response)
                break
            except urllib.error.HTTPError as error:
                if error.code not in {429, 500, 502, 503, 504} or attempt == 5:
                    raise
                time.sleep(int(error.headers.get("Retry-After", 5 * (attempt + 1))))
            except urllib.error.URLError:
                if attempt == 5:
                    raise
                time.sleep(5 * (attempt + 1))
        for work in payload.get("results", []):
            identifier = arxiv_id_from_doi(work.get("doi"))
            if identifier:
                works[identifier] = work
        completed = min(offset + BATCH_SIZE, len(identifiers))
        if completed % 5_000 == 0 or completed == len(identifiers):
            print(f"OpenAlex: {completed:,}/{len(identifiers):,} papers")
        time.sleep(delay_seconds)
    return works


def identity_from_authorship(
    local_name: str, authorship: dict[str, Any] | None
) -> tuple[str, str, str]:
    if authorship:
        author = authorship.get("author") or {}
        orcid = canonical_orcid(author.get("orcid"))
        openalex_id = canonical_openalex(author.get("id"))
        if orcid:
            return f"orcid:{orcid}", orcid, openalex_id
        if openalex_id:
            return f"openalex:{openalex_id}", "", openalex_id
    return f"name:{normalize_name(local_name)}", "", ""


def enrich_snapshot(snapshot: dict[str, Any], works: dict[str, Any]) -> dict[str, Any]:
    source_authors = snapshot["authors"]
    identity_names: dict[str, Counter[str]] = defaultdict(Counter)
    identity_metadata: dict[str, tuple[str, str]] = {}
    daily: dict[str, Counter[tuple[str, int]]] = defaultdict(Counter)
    matched_papers = 0
    matched_contributions = 0
    orcid_contributions = 0

    for day, paper_rows in snapshot.get("papers", {}).items():
        for arxiv_id, category_id, author_ids in paper_rows:
            local_names = [source_authors[author_id]["name"] for author_id in author_ids]
            work = works.get(str(arxiv_id).lower())
            authorships = (work or {}).get("authorships") or []
            matches = match_authorships(local_names, authorships) if work else [None] * len(local_names)
            if work:
                matched_papers += 1
            for local_name, authorship in zip(local_names, matches):
                key, orcid, openalex_id = identity_from_authorship(local_name, authorship)
                identity_names[key][local_name] += 1
                identity_metadata[key] = (orcid, openalex_id)
                daily[day][(key, int(category_id))] += 1
                if authorship:
                    matched_contributions += 1
                if orcid:
                    orcid_contributions += 1

    canonical_names = {
        key: counts.most_common(1)[0][0] for key, counts in identity_names.items()
    }
    identity_keys = sorted(
        identity_names,
        key=lambda key: (
            canonical_names[key].casefold(),
            identity_metadata[key][0],
            identity_metadata[key][1],
        ),
    )
    identity_ids = {key: index for index, key in enumerate(identity_keys)}
    enriched = {key: value for key, value in snapshot.items() if key != "papers"}
    enriched["authors"] = [
        {
            "name": canonical_names[key],
            "orcid": identity_metadata[key][0],
            "openalex_id": identity_metadata[key][1],
        }
        for key in identity_keys
    ]
    enriched["days"] = {
        day: [
            [identity_ids[key], category_id, count]
            for (key, category_id), count in sorted(
                counts.items(), key=lambda item: (identity_ids[item[0][0]], item[0][1])
            )
        ]
        for day, counts in sorted(daily.items())
    }
    enriched["identity_resolution"] = {
        "source": "OpenAlex authorships with ORCID when available",
        "matched_papers": matched_papers,
        "matched_author_contributions": matched_contributions,
        "orcid_author_contributions": orcid_contributions,
    }
    return enriched


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve arXiv authors through ORCID/OpenAlex")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--data-dir", type=Path, default=Path("web/public/data/authors"))
    args = parser.parse_args()
    target = args.data_dir / f"{args.year}.json"
    snapshot = json.loads(target.read_text(encoding="utf-8"))
    arxiv_ids = [
        str(row[0])
        for paper_rows in snapshot.get("papers", {}).values()
        for row in paper_rows
        if row[0]
    ]
    works = fetch_openalex(arxiv_ids)
    enriched = enrich_snapshot(snapshot, works)
    target.write_text(
        json.dumps(enriched, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    stats = enriched["identity_resolution"]
    print(
        f"{args.year}: {len(enriched['authors']):,} identities, "
        f"{stats['matched_papers']:,} OpenAlex papers, "
        f"{stats['orcid_author_contributions']:,} ORCID contributions"
    )


if __name__ == "__main__":
    main()

