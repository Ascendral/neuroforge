"""NeuroMorpho.org REST API client.

Public, registration-free API documented at https://neuromorpho.org/api.jsp

Endpoints used:
    GET /api/neuron/id/{id}            single neuron metadata
    GET /api/neuron?page=N&size=M      paginated neuron list
    GET /dableFiles/{archive_lower}/CNG version/{name}.CNG.swc   SWC reconstruction

The CNG-standardized SWC is the canonical reconstruction NeuroMorpho serves.
Archive directory names are lowercased on disk.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import requests

API_BASE = "https://neuromorpho.org/api"
SWC_BASE = "https://neuromorpho.org/dableFiles"
# Bumped from 30s after observing real upstream latency of ~70s on
# /api/neuron/id/{id} during 2026-04-30. neuromorpho.org's response time is
# inconsistent; failing under 30s is a backend artifact, not a real outage.
DEFAULT_TIMEOUT_S = 120


class NeuroMorphoError(RuntimeError):
    """Raised on any non-success response from neuromorpho.org."""


@dataclass(frozen=True, slots=True)
class NeuroMorphoNeuron:
    """Subset of NeuroMorpho metadata we surface to clients.

    Full upstream record has ~50 fields; we keep the ones needed for the inspector
    panel (display) and the simulators (parameter look-up). Add fields here only
    when a downstream consumer needs them.
    """

    neuron_id: int
    neuron_name: str
    archive: str
    species: str
    scientific_name: str
    brain_region: tuple[str, ...]
    cell_type: tuple[str, ...]
    reference_pmid: tuple[str, ...]
    reference_doi: tuple[str, ...]
    png_url: str | None
    raw: dict  # full upstream JSON, for citation and future fields


def _request(url: str, *, timeout: float = DEFAULT_TIMEOUT_S) -> requests.Response:
    try:
        response = requests.get(url, timeout=timeout, headers={"Accept": "application/json"})
    except requests.RequestException as exc:
        raise NeuroMorphoError(f"network error fetching {url}: {exc}") from exc
    if response.status_code == 404:
        raise NeuroMorphoError(f"not found: {url}")
    if not response.ok:
        raise NeuroMorphoError(
            f"HTTP {response.status_code} fetching {url}: {response.text[:200]}"
        )
    return response


def _parse_neuron_record(record: dict) -> NeuroMorphoNeuron:
    def _str_tuple(value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, list):
            return tuple(str(v) for v in value)
        return (str(value),)

    return NeuroMorphoNeuron(
        neuron_id=int(record["neuron_id"]),
        neuron_name=str(record["neuron_name"]),
        archive=str(record["archive"]),
        species=str(record.get("species", "")),
        scientific_name=str(record.get("scientific_name", "")),
        brain_region=_str_tuple(record.get("brain_region")),
        cell_type=_str_tuple(record.get("cell_type")),
        reference_pmid=_str_tuple(record.get("reference_pmid")),
        reference_doi=_str_tuple(record.get("reference_doi")),
        png_url=record.get("png_url") or None,
        raw=record,
    )


def get_neuron(neuron_id: int) -> NeuroMorphoNeuron:
    """Fetch metadata for a single neuron by NeuroMorpho ID."""
    response = _request(f"{API_BASE}/neuron/id/{neuron_id}")
    return _parse_neuron_record(response.json())


def list_neurons(*, page: int = 0, size: int = 50) -> list[NeuroMorphoNeuron]:
    """Fetch a page of neurons. Default 50 per page; upstream max is 500."""
    if page < 0 or size < 1 or size > 500:
        raise ValueError("page must be >= 0 and 1 <= size <= 500")
    response = _request(f"{API_BASE}/neuron?page={page}&size={size}")
    payload = response.json()
    embedded = payload.get("_embedded", {}).get("neuronResources", [])
    return [_parse_neuron_record(record) for record in embedded]


def search_neurons(
    *,
    criteria: dict[str, list[str]],
    page: int = 0,
    size: int = 25,
) -> tuple[list[NeuroMorphoNeuron], int]:
    """Filtered search via POST /api/neuron/select.

    Each criterion key is a queryable field name (see /api/neuron/fields) and
    the value is a list of allowed values for that field (OR-combined within a
    field; AND-combined across fields). The full list of allowed brain_region
    values is at GET /api/neuron/fields/brain_region.

    Returns: (neurons_in_page, total_matching_elements).
    """
    if page < 0 or size < 1 or size > 500:
        raise ValueError("page must be >= 0 and 1 <= size <= 500")
    if not criteria:
        raise ValueError("criteria must be non-empty")

    url = f"{API_BASE}/neuron/select?page={page}&size={size}"
    try:
        response = requests.post(
            url,
            json=criteria,
            timeout=DEFAULT_TIMEOUT_S,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
    except requests.RequestException as exc:
        raise NeuroMorphoError(f"network error posting {url}: {exc}") from exc
    if not response.ok:
        raise NeuroMorphoError(
            f"HTTP {response.status_code} posting {url}: {response.text[:200]}"
        )

    payload = response.json()
    embedded = payload.get("_embedded", {}).get("neuronResources", [])
    total = int(payload.get("page", {}).get("totalElements", 0))
    return [_parse_neuron_record(record) for record in embedded], total


def swc_url(neuron_name: str, archive: str) -> str:
    """Build the CNG-standardized SWC URL for a neuron.

    Archive directory is lowercased on the NeuroMorpho server. The canonical
    reconstruction lives in the 'CNG version' subdirectory and uses .CNG.swc suffix.
    """
    archive_dir = quote(archive.lower(), safe="")
    name_part = quote(f"{neuron_name}.CNG.swc", safe="")
    return f"{SWC_BASE}/{archive_dir}/CNG%20version/{name_part}"


def download_swc(neuron_name: str, archive: str) -> str:
    """Download the canonical CNG SWC text for a neuron.

    Raises NeuroMorphoError on non-200 response.
    """
    url = swc_url(neuron_name, archive)
    response = _request(url)
    return response.text
