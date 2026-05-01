"""GET /api/neurons/{id} — fetch a real neuron from NeuroMorpho with SQLite cache."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from neuroforge_api.db import init_db, session_scope
from neuroforge_api.models.neuron import CachedNeuron, NeuronPoint, NeuronResponse
from neuroforge_api.parsers.swc import SwcParseError, parse_swc
from neuroforge_api.sources.neuromorpho import (
    NeuroMorphoError,
    NeuroMorphoNeuron,
    download_swc,
    get_neuron,
    swc_url,
)

router = APIRouter(prefix="/api/neurons", tags=["neurons"])


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
