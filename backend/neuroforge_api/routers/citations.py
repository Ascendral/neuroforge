"""GET /api/citations/* — BibTeX dump and DOI list."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from neuroforge_api.citations import REFERENCES, all_dois, to_bibtex_dump

router = APIRouter(prefix="/api/citations", tags=["citations"])


class CitationSummary(BaseModel):
    bibtex_key: str
    entry_type: str
    title: str
    year: str
    doi: str | None
    used_by: list[str]


class CitationsResponse(BaseModel):
    total: int
    references: list[CitationSummary]
    dois: list[str]


@router.get("", response_model=CitationsResponse)
def list_citations() -> CitationsResponse:
    refs = [
        CitationSummary(
            bibtex_key=r.bibtex_key,
            entry_type=r.entry_type,
            title=r.fields.get("title", ""),
            year=r.fields.get("year", ""),
            doi=r.doi,
            used_by=list(r.used_by),
        )
        for r in REFERENCES
    ]
    return CitationsResponse(total=len(REFERENCES), references=refs, dois=all_dois())


@router.get("/bibtex", response_class=PlainTextResponse)
def bibtex_dump() -> str:
    """Plain-text BibTeX of every cited reference."""
    return to_bibtex_dump()
