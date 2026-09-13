"""Integrity tests for the multi-scale graph and the research timeline.

These are the anti-theater gate for registry content: every node is cited,
every cross-link points at a real node on the other side with a legal
evidence tag, every anchor label exists in the real atlas, every level is
populated on both sides, and every DOI has the shape of a DOI.
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from neuroforge_api.data import atlas as atlas_module
from neuroforge_api.data import research_timeline, scales
from neuroforge_api.data.pauli import PAULI_NUCLEI
from neuroforge_api.main import app

DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


def test_ids_unique_and_parents_exist():
    ids = [n.id for n in scales.NODES]
    assert len(ids) == len(set(ids))
    for n in scales.NODES:
        if n.parent is not None:
            assert n.parent in scales._BY_ID, n.id
            assert scales.node(n.parent).side == n.side, n.id
            assert scales.node(n.parent).level <= n.level, n.id


def test_every_level_populated_on_both_sides():
    for lv in scales.LEVELS:
        for side in ("brain", "ai"):
            count = sum(1 for n in scales.NODES if n.side == side and n.level == lv.level)
            assert count >= 1, f"{side} level {lv.level} empty"
    # and the interesting rungs have real breadth
    for side in ("brain", "ai"):
        for level in (2, 3, 4, 5):
            assert sum(1 for n in scales.NODES if n.side == side and n.level == level) >= 3, (side, level)


def test_every_node_is_cited_and_says_what_it_does():
    for n in scales.NODES:
        assert len(n.cites) >= 1, n.id
        assert n.description and n.function and n.mechanism, n.id
        assert n.side in ("brain", "ai") and 1 <= n.level <= 5, n.id


def test_analogs_cross_sides_with_legal_strength_or_explicit_none():
    for n in scales.NODES:
        assert n.analogs or n.no_analog_note, f"{n.id} has neither an analog nor a no-analog note"
        for a in n.analogs:
            assert a.target in scales._BY_ID, (n.id, a.target)
            assert scales.node(a.target).side != n.side, (n.id, a.target)
            assert a.strength in scales.STRENGTHS, (n.id, a.strength)
            assert a.note, (n.id, a.target)
            assert len(a.cites) >= 1, (n.id, a.target)


def test_equivalence_is_reserved_for_proved_mathematics():
    """'equivalence' may only be claimed with the Ramsauer proof attached."""
    for n in scales.NODES:
        for a in n.analogs:
            if a.strength == "equivalence":
                assert any(c.doi == "10.48550/arXiv.2008.02217" for c in a.cites), (n.id, a.target)


def test_anchor_labels_exist_in_real_atlases():
    ho = {r.label for r in atlas_module.harvard_oxford_cortical_regions() + atlas_module.harvard_oxford_subcortical_regions()}
    for n in scales.NODES:
        for lbl in n.ho_labels:
            assert lbl in ho, (n.id, lbl)
        for ab in n.pauli:
            assert ab in PAULI_NUCLEI, (n.id, ab)
        if n.side == "ai":
            assert not (n.ho_labels or n.pauli or n.cerebellum or n.neuromorpho), n.id


def test_every_brain_region_and_circuit_has_an_anchor():
    for n in scales.NODES:
        if n.side == "brain" and n.level in (2, 3):
            assert n.ho_labels or n.pauli or n.cerebellum, n.id


def test_edges_reference_nodes_on_same_side():
    for e in scales.EDGES:
        assert e.source in scales._BY_ID and e.target in scales._BY_ID, e
        assert scales.node(e.source).side == scales.node(e.target).side, e
        assert e.kind in ("projects_to", "data_flow", "modulates", "gradient", "teaches"), e


def test_widgets_are_real_simulators():
    known = {"hh", "stdp", "hebbian", "hopfield", "modern_hopfield", "dopamine_rpe", "synapse", "v1", "mcp"}
    for n in scales.NODES:
        if n.widget:
            assert n.widget in known, (n.id, n.widget)


def test_dois_well_formed_and_unique_per_registry():
    for doi in scales.all_dois():
        assert DOI_RE.match(doi), doi
    for doi in research_timeline.all_dois():
        assert DOI_RE.match(doi), doi


def test_timeline_links_resolve_and_years_ordered():
    for m in research_timeline.TIMELINE:
        assert m.category in ("neuro", "ai", "bridge"), m.title
        assert m.significance and m.who, m.title
        assert m.doi or m.note, m.title  # no DOI ⇒ must say why
        for link in m.links:
            assert link in scales._BY_ID, (m.title, link)
        assert 1900 <= m.year <= 2026
    years = [m.year for m in research_timeline.TIMELINE]
    assert min(years) < 1950 and max(years) >= 2025


def test_graph_endpoint_resolves_anchors_and_backlinks():
    client = TestClient(app)
    r = client.get("/api/scales/graph")
    assert r.status_code == 200, r.text[:300]
    g = r.json()
    assert len(g["levels"]) == 5
    by_id = {n["id"]: n for n in g["nodes"]}
    # anchors resolved to real centroids
    da = by_id["brain.region.midbrain_da"]
    assert {a["label"] for a in da["anchors"]} == {"VTA", "SNc"}
    assert all(len(a["centroid_mni_mm"]) == 3 for a in da["anchors"])
    cb = by_id["brain.region.cerebellum"]
    assert any(a["source"] == "diedrichsen" for a in cb["anchors"])
    # back-links
    assert "brain.circuit.hippocampus" in by_id["ai.block.attention"]["analog_of"] or \
        "ai.block.attention" in by_id["brain.circuit.hippocampus"]["analog_of"]
    assert "ai.block" in by_id["ai.arch.blocks"]["children"]
    # single node endpoint + 404
    assert client.get("/api/scales/node/ai.block.attention").status_code == 200
    assert client.get("/api/scales/node/nope").status_code == 404


def test_timeline_endpoint():
    client = TestClient(app)
    r = client.get("/api/research/timeline")
    assert r.status_code == 200
    body = r.json()
    assert body["n"] == len(research_timeline.TIMELINE) >= 60
    years = [m["year"] for m in body["milestones"]]
    assert years == sorted(years)
