"""End-to-end test for GET /api/neurons/{id} using a temp SQLite DB.

Hits real neuromorpho.org. Per CLAUDE.md, no mocks: if the integration breaks
because upstream changed, that is exactly the kind of bug we want surfaced.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

from neuroforge_api import db as db_module
from neuroforge_api.main import app


def _network_available() -> bool:
    try:
        requests.get("https://neuromorpho.org/api/neuron/id/1", timeout=10)
        return True
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not _network_available(),
    reason="neuromorpho.org unreachable; endpoint integration test skipped",
)


@pytest.fixture
def isolated_db(tmp_path: Path):
    db_path = tmp_path / "test_neurons.sqlite"
    db_module.reset_for_tests(db_path)
    db_module.init_db(db_path)
    yield
    db_module.reset_for_tests(Path(db_module.DEFAULT_DB_PATH))


def test_fetch_neuron_1_end_to_end(isolated_db):
    client = TestClient(app)

    response = client.get("/api/neurons/1")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["neuron_id"] == 1
    assert body["neuron_name"] == "cnic_001"
    assert body["archive"] == "Wearne_Hof"
    assert body["species"] == "monkey"
    assert body["point_count"] > 100
    assert "neocortex" in body["brain_region"]
    assert "pyramidal" in body["cell_type"]
    assert "10.1093/cercor/13.9.950" in body["reference_doi"]
    assert body["swc_url"].endswith(".CNG.swc")

    root = body["points"][0]
    assert root["id"] == 1
    assert root["type"] == 1
    assert root["parent_id"] == -1


def test_second_fetch_uses_cache(isolated_db):
    """After a successful fetch, refetch should return the same payload.

    We can't directly assert 'no network call happened' without injection, but
    we can verify the cached row is present and the response is consistent.
    """
    client = TestClient(app)

    first = client.get("/api/neurons/1")
    assert first.status_code == 200

    from sqlalchemy import select

    from neuroforge_api.models.neuron import CachedNeuron

    with db_module.session_scope() as session:
        cached = session.scalars(select(CachedNeuron).where(CachedNeuron.neuron_id == 1)).first()
        assert cached is not None
        assert cached.neuron_name == "cnic_001"
        assert len(cached.swc_text) > 1000

    second = client.get("/api/neurons/1")
    assert second.status_code == 200
    assert second.json() == first.json()
