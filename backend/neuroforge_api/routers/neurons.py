"""GET /api/neurons/{id} — fetch a real neuron from NeuroMorpho with SQLite cache."""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from neuroforge_api.db import init_db, session_scope
from neuroforge_api.models.neuron import CachedNeuron, NeuronPoint, NeuronResponse
from neuroforge_api.parsers.swc import SwcParseError, parse_swc
from neuroforge_api.sources.neuromorpho import (
    NeuroMorphoError,
    NeuroMorphoNeuron,
    download_swc,
    get_neuron,
    search_neurons,
    swc_url,
)


class NeuronSummary(BaseModel):
    neuron_id: int
    neuron_name: str
    archive: str
    species: str
    scientific_name: str
    brain_region: list[str]
    cell_type: list[str]
    reference_doi: list[str]
    reference_pmid: list[str]
    png_url: str | None
    source_url: str
    swc_url: str


class NeuronSearchResponse(BaseModel):
    region_query: list[str]
    total_matching: int
    page: int
    size: int
    results: list[NeuronSummary]
    citation_note: str

router = APIRouter(prefix="/api/neurons", tags=["neurons"])

# In-memory cache for the per-region sample endpoints. neuromorpho.org's
# region listings change ~yearly; caching for 1 hour cheap-side avoids
# hammering them during page reloads. Keyed by (region_query, size).
_SAMPLE_CACHE: dict[tuple[str, int], tuple[float, NeuronSearchResponse]] = {}
_SAMPLE_TTL_S = 3600.0


def _cached_search(
    cache_key: tuple[str, int],
    *,
    criteria: dict[str, list[str]],
    size: int,
    region_query: list[str],
    citation_note: str,
):
    now = time.monotonic()
    cached = _SAMPLE_CACHE.get(cache_key)
    if cached and now - cached[0] < _SAMPLE_TTL_S:
        return cached[1]
    try:
        results, total = search_neurons(criteria=criteria, page=0, size=size)
    except NeuroMorphoError as exc:
        raise HTTPException(status_code=502, detail=f"neuromorpho.org: {exc}") from exc
    response = NeuronSearchResponse(
        region_query=region_query,
        total_matching=total,
        page=0,
        size=size,
        results=[_summary(n) for n in results],
        citation_note=citation_note,
    )
    _SAMPLE_CACHE[cache_key] = (now, response)
    return response


def _summary(meta: NeuroMorphoNeuron) -> NeuronSummary:
    return NeuronSummary(
        neuron_id=meta.neuron_id,
        neuron_name=meta.neuron_name,
        archive=meta.archive,
        species=meta.species,
        scientific_name=meta.scientific_name,
        brain_region=list(meta.brain_region),
        cell_type=list(meta.cell_type),
        reference_doi=list(meta.reference_doi),
        reference_pmid=list(meta.reference_pmid),
        png_url=meta.png_url,
        source_url=f"https://neuromorpho.org/neuron_info.jsp?neuron_id={meta.neuron_id}",
        swc_url=swc_url(meta.neuron_name, meta.archive),
    )


@router.get("/ca3/sample", response_model=NeuronSearchResponse)
def sample_ca3_pyramidals(size: int = 5) -> NeuronSearchResponse:
    """Real CA3 hippocampal pyramidal reconstructions.

    CA3 is the recurrent-collateral region of hippocampus widely modeled as
    the biological substrate of attractor-network dynamics — including the
    pattern-completion and content-addressable recall implemented by the
    Hopfield 1982 network.

    Filter: brain_region=['CA3'] AND cell_type=['pyramidal'].
    """
    if size < 1 or size > 50:
        raise HTTPException(status_code=422, detail="size must be in [1, 50]")
    return _cached_search(
        ("ca3", size),
        criteria={"brain_region": ["CA3"], "cell_type": ["pyramidal"]},
        size=size,
        region_query=["CA3", "pyramidal"],
        citation_note=(
            "CA3 pyramidals form recurrent collaterals — the anatomical "
            "substrate widely modeled as a biological Hopfield-style "
            "attractor network for episodic memory recall."
        ),
    )


@router.get("/hippocampus/sample", response_model=NeuronSearchResponse)
def sample_hippocampal_pyramidals(size: int = 5) -> NeuronSearchResponse:
    """Return a page of real hippocampal pyramidal neurons.

    Uses NeuroMorpho.org's POST /api/neuron/select with the filter
    {"brain_region": ["hippocampus"], "cell_type": ["pyramidal"]} — these are
    the canonical Bliss-Lømo / Hebb-LTP cell type.
    """
    if size < 1 or size > 50:
        raise HTTPException(status_code=422, detail="size must be in [1, 50]")
    return _cached_search(
        ("hippocampus", size),
        criteria={"brain_region": ["hippocampus"], "cell_type": ["pyramidal"]},
        size=size,
        region_query=["hippocampus", "pyramidal"],
        citation_note=(
            "Filter: brain_region='hippocampus' AND cell_type='pyramidal'. "
            "These are the cells in which Bliss & Lømo 1973 first demonstrated "
            "long-term potentiation (LTP), the cellular correlate of Hebb's rule."
        ),
    )


@router.get("/v1/sample", response_model=NeuronSearchResponse)
def sample_v1_neurons(size: int = 5) -> NeuronSearchResponse:
    """Return a page of real V1 (primary visual cortex) reconstructions.

    Uses NeuroMorpho.org's POST /api/neuron/select with brain_region filter
    {"brain_region": ["primary visual"]}. The brain_region vocabulary is the
    one returned by GET /api/neuron/fields/brain_region.
    """
    if size < 1 or size > 50:
        raise HTTPException(status_code=422, detail="size must be in [1, 50]")
    return _cached_search(
        ("v1", size),
        criteria={"brain_region": ["primary visual"]},
        size=size,
        region_query=["primary visual"],
        citation_note=(
            "All metadata fetched live from NeuroMorpho.org. Each neuron's "
            "reference_doi / reference_pmid resolve to the publication that "
            "deposited the reconstruction."
        ),
    )


def _build_response(meta: NeuroMorphoNeuron, swc_text: str) -> NeuronResponse:
    morphology = parse_swc(swc_text)
    return NeuronResponse(
        neuron_id=meta.neuron_id,
        neuron_name=meta.neuron_name,
        archive=meta.archive,
        species=meta.species,
        scientific_name=meta.scientific_name,
        brain_region=list(meta.brain_region),
        cell_type=list(meta.cell_type),
        reference_pmid=list(meta.reference_pmid),
        reference_doi=list(meta.reference_doi),
        png_url=meta.png_url,
        points=[
            NeuronPoint(
                id=p.id, type=p.type, x=p.x, y=p.y, z=p.z, radius=p.radius, parent_id=p.parent_id
            )
            for p in morphology.points
        ],
        point_count=len(morphology),
        source_url=f"https://neuromorpho.org/neuron_info.jsp?neuron_id={meta.neuron_id}",
        swc_url=swc_url(meta.neuron_name, meta.archive),
    )


def _meta_from_cache(row: CachedNeuron) -> NeuroMorphoNeuron:
    raw = row.metadata_json

    def _strs(value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, list):
            return tuple(str(v) for v in value)
        return (str(value),)

    return NeuroMorphoNeuron(
        neuron_id=row.neuron_id,
        neuron_name=row.neuron_name,
        archive=row.archive,
        species=str(raw.get("species", "")),
        scientific_name=str(raw.get("scientific_name", "")),
        brain_region=_strs(raw.get("brain_region")),
        cell_type=_strs(raw.get("cell_type")),
        reference_pmid=_strs(raw.get("reference_pmid")),
        reference_doi=_strs(raw.get("reference_doi")),
        png_url=raw.get("png_url") or None,
        raw=raw,
    )


@router.get("/{neuron_id}", response_model=NeuronResponse)
def fetch_neuron(neuron_id: int) -> NeuronResponse:
    init_db()
    with session_scope() as session:
        row = session.scalars(
            select(CachedNeuron).where(CachedNeuron.neuron_id == neuron_id)
        ).first()
        if row is not None:
            try:
                return _build_response(_meta_from_cache(row), row.swc_text)
            except SwcParseError as exc:
                raise HTTPException(500, f"cached SWC parse error: {exc}") from exc

    try:
        meta = get_neuron(neuron_id)
        swc_text = download_swc(meta.neuron_name, meta.archive)
    except NeuroMorphoError as exc:
        raise HTTPException(502, f"neuromorpho.org: {exc}") from exc

    try:
        response = _build_response(meta, swc_text)
    except SwcParseError as exc:
        raise HTTPException(502, f"upstream SWC parse error: {exc}") from exc

    with session_scope() as session:
        session.merge(
            CachedNeuron(
                neuron_id=meta.neuron_id,
                neuron_name=meta.neuron_name,
                archive=meta.archive,
                metadata_json=meta.raw,
                swc_text=swc_text,
            )
        )

    return response
