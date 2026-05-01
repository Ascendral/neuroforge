"""Live integration tests for /api/neurons/v1/sample.

Exercises the real NeuroMorpho POST /api/neuron/select endpoint with a
brain_region:'primary visual' filter. Skips on network unreachable.
"""

from __future__ import annotations

import pytest
import requests
from fastapi.testclient import TestClient

from neuroforge_api.main import app
from neuroforge_api.sources.neuromorpho import search_neurons


def _network_available() -> bool:
    try:
        requests.get("https://neuromorpho.org/api/neuron/id/1", timeout=10)
        return True
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not _network_available(),
    reason="neuromorpho.org unreachable; live integration tests skipped",
)


def test_search_neurons_returns_v1_neurons():
    results, total = search_neurons(
        criteria={"brain_region": ["primary visual"]},
        page=0,
        size=5,
    )
    assert total > 100, f"expected many V1 neurons in NeuroMorpho, got {total}"
    assert len(results) == 5
    for neuron in results:
        # Every returned neuron must actually be in primary visual cortex
        assert "primary visual" in neuron.brain_region, (
            f"neuron {neuron.neuron_id} has region {neuron.brain_region}"
        )
        assert neuron.neuron_name and neuron.archive


def test_search_neurons_rejects_invalid_args():
    with pytest.raises(ValueError):
        search_neurons(criteria={}, page=0, size=5)
    with pytest.raises(ValueError):
        search_neurons(
            criteria={"brain_region": ["primary visual"]},
            page=-1,
            size=5,
        )


def test_v1_sample_endpoint():
    client = TestClient(app)
    response = client.get("/api/neurons/v1/sample?size=3")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["region_query"] == ["primary visual"]
    assert body["total_matching"] > 100
    assert len(body["results"]) == 3
    for n in body["results"]:
        assert "primary visual" in n["brain_region"]
        assert n["source_url"].startswith("https://neuromorpho.org/neuron_info.jsp")
        assert n["swc_url"].startswith("https://neuromorpho.org/dableFiles/")
