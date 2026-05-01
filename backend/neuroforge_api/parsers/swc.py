"""SWC file format parser.

SWC is the standard format for digital reconstructions of neuronal morphology.
Each non-comment line is whitespace-separated:
    id  type  x  y  z  radius  parent_id

Type codes (Cannon et al. 1998 / NeuroMorpho convention):
    0 = undefined
    1 = soma
    2 = axon
    3 = basal dendrite
    4 = apical dendrite
    5 = fork point          (rare, often unused)
    6 = end point           (rare, often unused)
    7+ = custom

parent_id == -1 indicates a root point (typically the soma center).

Reference: https://neuromorpho.org/myfaq.jsp (SWC format section)
"""

from __future__ import annotations

from dataclasses import dataclass


class SwcParseError(ValueError):
    """Raised when an SWC file cannot be parsed."""


@dataclass(frozen=True, slots=True)
class SwcPoint:
    id: int
    type: int
    x: float
    y: float
    z: float
    radius: float
    parent_id: int  # -1 for root


@dataclass(frozen=True, slots=True)
class SwcMorphology:
    """Parsed SWC reconstruction."""

    points: tuple[SwcPoint, ...]

    @property
    def soma_points(self) -> tuple[SwcPoint, ...]:
        return tuple(p for p in self.points if p.type == 1)

    @property
    def axon_points(self) -> tuple[SwcPoint, ...]:
        return tuple(p for p in self.points if p.type == 2)

    @property
    def dendrite_points(self) -> tuple[SwcPoint, ...]:
        return tuple(p for p in self.points if p.type in (3, 4))

    def __len__(self) -> int:
        return len(self.points)


def parse_swc(text: str) -> SwcMorphology:
    """Parse SWC text into a SwcMorphology.

    Skips blank lines and comment lines starting with '#'.
    Raises SwcParseError on any malformed data line.
    """
    points: list[SwcPoint] = []
    seen_ids: set[int] = set()

    for line_num, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        fields = line.split()
        if len(fields) != 7:
            raise SwcParseError(
                f"line {line_num}: expected 7 whitespace-separated fields, got {len(fields)}"
            )

        try:
            point_id = int(fields[0])
            point_type = int(fields[1])
            x = float(fields[2])
            y = float(fields[3])
            z = float(fields[4])
            radius = float(fields[5])
            parent_id = int(fields[6])
        except ValueError as exc:
            raise SwcParseError(f"line {line_num}: numeric parse error: {exc}") from exc

        if point_id in seen_ids:
            raise SwcParseError(f"line {line_num}: duplicate point id {point_id}")
        seen_ids.add(point_id)

        if parent_id != -1 and parent_id not in seen_ids:
            raise SwcParseError(
                f"line {line_num}: parent_id {parent_id} not seen before point {point_id} "
                "(SWC requires parents to appear before children)"
            )

        points.append(
            SwcPoint(
                id=point_id,
                type=point_type,
                x=x,
                y=y,
                z=z,
                radius=radius,
                parent_id=parent_id,
            )
        )

    if not points:
        raise SwcParseError("no data points found")

    return SwcMorphology(points=tuple(points))
