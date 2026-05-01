"""Citation registry + endpoint tests."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from neuroforge_api.citations import REFERENCES, all_dois, to_bibtex_dump
from neuroforge_api.main import app

DOI_PATTERN = re.compile(r"^10\.\d{3,9}/[^\s]+$")


def test_every_reference_has_required_fields():
    for ref in REFERENCES:
        assert ref.bibtex_key
        assert ref.entry_type in {"article", "book", "inproceedings", "incollection", "techreport"}
        assert ref.fields.get("title")
        assert ref.fields.get("year")
        assert ref.used_by


def test_every_doi_is_well_formed():
    for doi in all_dois():
        assert DOI_PATTERN.match(doi), f"malformed DOI: {doi}"


def test_bibtex_dump_contains_every_entry():
    dump = to_bibtex_dump()
    for ref in REFERENCES:
        assert f"@{ref.entry_type}{{{ref.bibtex_key}," in dump


def test_citations_endpoint():
    client = TestClient(app)
    response = client.get("/api/citations")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(REFERENCES)
    assert len(body["dois"]) == len(all_dois())


def test_bibtex_endpoint_is_plain_text():
    client = TestClient(app)
    response = client.get("/api/citations/bibtex")
    assert response.status_code == 200
    text = response.text
    assert "@article{hodgkin1952quantitative," in text
    assert "@book{hebb1949organization," in text
    assert "10.1113/jphysiol.1952.sp004764" in text


def test_simulator_modules_are_referenced_in_used_by():
    """Every active simulator module name appears in at least one Reference's used_by."""
    referenced = set()
    for ref in REFERENCES:
        referenced.update(ref.used_by)
    expected = {"hodgkin_huxley", "stdp", "hubel_wiesel", "hebbian", "hopfield", "mcp"}
    assert expected.issubset(referenced), f"missing: {expected - referenced}"
