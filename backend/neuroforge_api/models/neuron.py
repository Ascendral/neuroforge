"""Database and API models for cached neurons."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CachedNeuron(Base):
    __tablename__ = "neurons"

    neuron_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    neuron_name: Mapped[str] = mapped_column(String, nullable=False)
    archive: Mapped[str] = mapped_column(String, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    swc_text: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class NeuronPoint(BaseModel):
    id: int
    type: int
    x: float
    y: float
    z: float
    radius: float
    parent_id: int


class NeuronResponse(BaseModel):
    """API shape returned to the frontend."""

    neuron_id: int
    neuron_name: str
    archive: str
    species: str
    scientific_name: str
    brain_region: list[str]
    cell_type: list[str]
    reference_pmid: list[str]
    reference_doi: list[str]
    png_url: str | None
    points: list[NeuronPoint]
    point_count: int
    source_url: str
    swc_url: str
