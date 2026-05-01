"""End-to-end test for POST /api/simulate/hh."""

from __future__ import annotations

from fastapi.testclient import TestClient

from neuroforge_api.main import app


def test_hh_endpoint_returns_canonical_action_potential():
    client = TestClient(app)
    response = client.post(
        "/api/simulate/hh",
        json={
            "duration_ms": 80.0,
            "stimulus_uA": 10.0,
            "stimulus_start_ms": 10.0,
            "stimulus_end_ms": 70.0,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert "Hodgkin" in body["citation"]
    assert "10.1113/jphysiol.1952.sp004764" in body["citation"]
    assert len(body["times_ms"]) == len(body["voltage_mV"]) == len(body["stimulus_uA"])
    assert len(body["spike_times_ms"]) >= 1
    assert max(body["voltage_mV"]) > 30.0
    assert min(body["voltage_mV"]) < -65.0
    # First and last samples are aligned with the requested duration
    assert body["times_ms"][0] >= 0.0
    assert body["times_ms"][-1] <= 80.001


def test_hh_endpoint_rejects_invalid_input():
    client = TestClient(app)
    response = client.post(
        "/api/simulate/hh",
        json={"duration_ms": -1.0, "stimulus_uA": 10.0},
    )
    assert response.status_code == 422, response.text
