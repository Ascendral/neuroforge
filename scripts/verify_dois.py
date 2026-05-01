#!/usr/bin/env python3
"""Verify every cited DOI in NeuroForge resolves.

Usage:  python scripts/verify_dois.py
Exit code 0 if all DOIs resolve, 1 if any 404 or network error.
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from neuroforge_api.citations import REFERENCES  # noqa: E402

TIMEOUT_S = 30


def resolves(doi: str) -> tuple[bool, int, str]:
    """Verify a DOI via Crossref metadata API (api.crossref.org).

    api.crossref.org/works/{DOI} returns metadata for any valid registered
    DOI and does not require browser headers. This is the canonical DOI
    existence probe — testing the publisher landing page directly is
    unreliable (many publishers 403 anonymous HEAD requests).
    """
    url = f"https://api.crossref.org/works/{doi}"
    try:
        response = requests.get(
            url,
            timeout=TIMEOUT_S,
            headers={"User-Agent": "neuroforge-doi-verifier/0.1 (mailto:pinkevich1980@gmail.com)"},
        )
        if response.status_code == 200:
            data = response.json()
            title = data.get("message", {}).get("title", [""])
            title_str = title[0] if title else ""
            return True, 200, title_str[:80]
        return False, response.status_code, response.text[:80]
    except requests.RequestException as exc:
        return False, 0, f"network error: {exc}"


def main() -> int:
    failures: list[tuple[str, str, int, str]] = []
    for ref in REFERENCES:
        if ref.doi is None:
            continue
        ok, status, redirect = resolves(ref.doi)
        marker = "OK " if ok else "FAIL"
        print(f"{marker}  {status:>3}  {ref.doi}  →  {redirect[:80]}")
        if not ok:
            failures.append((ref.bibtex_key, ref.doi, status, redirect))

    if failures:
        print(f"\n{len(failures)} DOI(s) failed to resolve:", file=sys.stderr)
        for key, doi, status, msg in failures:
            print(f"  {key}: {doi} (status={status}) {msg}", file=sys.stderr)
        return 1
    print(f"\nAll {sum(1 for r in REFERENCES if r.doi)} DOIs resolved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
