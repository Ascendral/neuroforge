"""GET /api/scales/* and /api/research/timeline — the multi-scale brain/AI graph."""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from neuroforge_api.data import atlas as atlas_module
from neuroforge_api.data import cerebellum as cerebellum_module
from neuroforge_api.data import pauli as pauli_module
from neuroforge_api.data import research_timeline, scales

router = APIRouter(tags=["scales"])


class CiteModel(BaseModel):
    text: str
    doi: str | None


class AnalogModel(BaseModel):
    target: str
    target_name: str
    strength: str
    note: str
    cites: list[CiteModel]


class FactModel(BaseModel):
    label: str
    value: str
    cite: CiteModel


class AnchorCentroid(BaseModel):
    label: str
    source: str            # harvard_oxford | pauli | diedrichsen
    centroid_mni_mm: list[float]


class NodeModel(BaseModel):
    id: str
    side: str
    level: int
    name: str
    parent: str | None
    group: str
    order: int
    description: str
    function: str
    mechanism: str
    cites: list[CiteModel]
    analogs: list[AnalogModel]
    no_analog_note: str | None
    facts: list[FactModel]
    anchors: list[AnchorCentroid]
    neuromorpho: dict[str, str] | None
    widget: str | None
    children: list[str]
    analog_of: list[str]   # ids on the other side that point at this node


class EdgeModel(BaseModel):
    source: str
    target: str
    kind: str
    note: str
    cite: CiteModel | None


class LevelModel(BaseModel):
    level: int
    brain_name: str
    ai_name: str
    brain_blurb: str
    ai_blurb: str


class ScalesGraphResponse(BaseModel):
    levels: list[LevelModel]
    nodes: list[NodeModel]
    edges: list[EdgeModel]
    strengths: list[str]
    note: str


class MilestoneModel(BaseModel):
    year: int
    category: str
    title: str
    who: str
    doi: str | None
    significance: str
    links: list[str]
    note: str | None


class TimelineResponse(BaseModel):
    milestones: list[MilestoneModel]
    n: int
    note: str


def _cite(c: scales.Cite) -> CiteModel:
    return CiteModel(text=c.text, doi=c.doi)


@lru_cache(maxsize=1)
def _anchor_index() -> dict[tuple[str, str], list[float]]:
    """(source, label) → MNI centroid, built once from the real atlases."""
    idx: dict[tuple[str, str], list[float]] = {}
    for r in atlas_module.harvard_oxford_cortical_regions() + atlas_module.harvard_oxford_subcortical_regions():
        if r.centroid_mni_mm:
            idx[("harvard_oxford", r.label)] = list(r.centroid_mni_mm)
    for n in pauli_module.all_pauli_nuclei():
        idx[("pauli", n.abbrev)] = list(n.centroid_mni_mm)
    cb = cerebellum_module.cerebellum_mesh()
    if cb is not None:
        idx[("diedrichsen", "Cerebellum")] = list(cb.centroid_mni_mm)
    return idx


def _anchors(n: scales.Node) -> list[AnchorCentroid]:
    idx = _anchor_index()
    out: list[AnchorCentroid] = []
    for lbl in n.ho_labels:
        c = idx.get(("harvard_oxford", lbl))
        if c:
            out.append(AnchorCentroid(label=lbl, source="harvard_oxford", centroid_mni_mm=c))
    for ab in n.pauli:
        c = idx.get(("pauli", ab))
        if c:
            out.append(AnchorCentroid(label=ab, source="pauli", centroid_mni_mm=c))
    if n.cerebellum:
        c = idx.get(("diedrichsen", "Cerebellum"))
        if c:
            out.append(AnchorCentroid(label="Cerebellum", source="diedrichsen", centroid_mni_mm=c))
    return out


@lru_cache(maxsize=1)
def _graph() -> ScalesGraphResponse:
    children: dict[str, list[str]] = {n.id: [] for n in scales.NODES}
    analog_of: dict[str, list[str]] = {n.id: [] for n in scales.NODES}
    for n in scales.NODES:
        if n.parent:
            children[n.parent].append(n.id)
        for a in n.analogs:
            analog_of[a.target].append(n.id)

    nodes = [
        NodeModel(
            id=n.id,
            side=n.side,
            level=n.level,
            name=n.name,
            parent=n.parent,
            group=n.group,
            order=n.order,
            description=n.description,
            function=n.function,
            mechanism=n.mechanism,
            cites=[_cite(c) for c in n.cites],
            analogs=[
                AnalogModel(
                    target=a.target,
                    target_name=scales.node(a.target).name,
                    strength=a.strength,
                    note=a.note,
                    cites=[_cite(c) for c in a.cites],
                )
                for a in n.analogs
            ],
            no_analog_note=n.no_analog_note,
            facts=[FactModel(label=f.label, value=f.value, cite=_cite(f.cite)) for f in n.facts],
            anchors=_anchors(n),
            neuromorpho=n.neuromorpho,
            widget=n.widget,
            children=children[n.id],
            analog_of=analog_of[n.id],
        )
        for n in scales.NODES
    ]
    edges = [
        EdgeModel(source=e.source, target=e.target, kind=e.kind, note=e.note, cite=_cite(e.cite) if e.cite else None)
        for e in scales.EDGES
    ]
    return ScalesGraphResponse(
        levels=[
            LevelModel(level=lv.level, brain_name=lv.brain_name, ai_name=lv.ai_name, brain_blurb=lv.brain_blurb, ai_blurb=lv.ai_blurb)
            for lv in scales.LEVELS
        ],
        nodes=nodes,
        edges=edges,
        strengths=list(scales.STRENGTHS),
        note=(
            "Every node cites primary literature; every DOI is resolved by scripts/verify_dois.py. "
            "Evidence tags: equivalence = proved same mathematics; strong = quantitative/causal evidence; "
            "analogy = conceptual parallel only; none = no known counterpart. Brain anchors are real atlas "
            "centroids (Harvard-Oxford, Pauli 2017, Diedrichsen 2009)."
        ),
    )


@router.get("/api/scales/graph", response_model=ScalesGraphResponse)
def get_scales_graph() -> ScalesGraphResponse:
    try:
        return _graph()
    except Exception as exc:  # noqa: BLE001 — surface real atlas errors
        raise HTTPException(status_code=502, detail=f"scales graph error: {exc}") from exc


@router.get("/api/scales/node/{node_id}", response_model=NodeModel)
def get_scales_node(node_id: str) -> NodeModel:
    g = get_scales_graph()
    for n in g.nodes:
        if n.id == node_id:
            return n
    raise HTTPException(status_code=404, detail=f"unknown node: {node_id}")


@router.get("/api/research/timeline", response_model=TimelineResponse)
def get_timeline() -> TimelineResponse:
    ms = [
        MilestoneModel(
            year=m.year, category=m.category, title=m.title, who=m.who, doi=m.doi,
            significance=m.significance, links=list(m.links), note=m.note,
        )
        for m in sorted(research_timeline.TIMELINE, key=lambda m: (m.year, m.title))
    ]
    return TimelineResponse(
        milestones=ms,
        n=len(ms),
        note="Landmark results 1921-2025. Categories: neuro / ai / bridge. Every DOI verified via Crossref or DataCite.",
    )
