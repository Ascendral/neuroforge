#!/usr/bin/env python3
"""Verify every cited DOI in NeuroForge resolves.

Usage:  python scripts/verify_dois.py
Exit code 0 if all DOIs resolve, 1 if any 404 or network error.

Sources of DOIs (all three registries are checked):
  - neuroforge_api.citations.REFERENCES            (module bibliography)
  - neuroforge_api.data.scales.all_dois()          (multi-scale brain/AI graph)
  - neuroforge_api.data.research_timeline.all_dois()

Resolution: Crossref first (journals, most publishers); DataCite second
(arXiv DOIs 10.48550/…, Zenodo). A DOI that resolves at neither is a failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from neuroforge_api.citations import REFERENCES  # noqa: E402
from neuroforge_api.data import research_timeline, scales  # noqa: E402

TIMEOUT_S = 30
HEADERS = {"User-Agent": "neuroforge-doi-verifier/0.2 (mailto:pinkevich1980@gmail.com)"}


def _crossref(doi: str) -> tuple[bool, int, str]:
    try:
        response = requests.get(f"https://api.crossref.org/works/{doi}", timeout=TIMEOUT_S, headers=HEADERS)
    except requests.RequestException as exc:
        return False, 0, f"network error: {exc}"
    if response.status_code == 200:
        title = response.json().get("message", {}).get("title", [""])
        return True, 200, (title[0] if title else "")[:80]
    return False, response.status_code, response.text[:80]


def _datacite(doi: str) -> tuple[bool, int, str]:
    try:
        response = requests.get(f"https://api.datacite.org/dois/{doi}", timeout=TIMEOUT_S, headers=HEADERS)
    except requests.RequestException as exc:
        return False, 0, f"network error: {exc}"
    if response.status_code == 200:
        titles = response.json().get("data", {}).get("attributes", {}).get("titles", [])
        return True, 200, (titles[0].get("title", "") if titles else "")[:80]
    return False, response.status_code, response.text[:80]


def resolves(doi: str) -> tuple[bool, int, str, str]:
    """Return (ok, status, title, source). Crossref, then DataCite."""
    ok, status, title = _crossref(doi)
    if ok:
        return True, status, title, "crossref"
    ok2, status2, title2 = _datacite(doi)
    if ok2:
        return True, status2, title2, "datacite"
    return False, status or status2, title2 or title, "none"


def main() -> int:
    dois: dict[str, str] = {}
    for ref in REFERENCES:
        if ref.doi:
            dois.setdefault(ref.doi, f"citations:{ref.bibtex_key}")
    for doi, owner in scales.all_dois().items():
        dois.setdefault(doi, f"scales:{owner}")
    for doi, owner in research_timeline.all_dois().items():
        dois.setdefault(doi, f"timeline:{owner}")

    failures: list[tuple[str, str, int, str]] = []
    for doi, owner in sorted(dois.items(), key=lambda kv: kv[1]):
        ok, status, title, source = resolves(doi)
        marker = "OK " if ok else "FAIL"
        print(f"{marker}  {status:>3}  {source:8s}  {doi:45s}  →  {title}")
        if not ok:
            failures.append((owner, doi, status, title))

    if failures:
        print(f"\n{len(failures)} DOI(s) failed to resolve:", file=sys.stderr)
        for owner, doi, status, msg in failures:
            print(f"  {owner}: {doi} (status={status}) {msg}", file=sys.stderr)
        return 1
    print(f"\nAll {len(dois)} DOIs resolved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
