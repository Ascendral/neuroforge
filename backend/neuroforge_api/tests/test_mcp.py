"""McCulloch-Pitts physics tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from neuroforge_api.main import app
from neuroforge_api.simulators.mcp import (
    GATES,
    evaluate_gate,
    search_xor_single_layer,
)


@pytest.mark.parametrize("gate_name", list(GATES))
def test_each_gate_truth_table(gate_name: str):
    """Each canonical gate (AND, OR, NOT, NAND, NOR) must match its truth table."""
    result = evaluate_gate(gate_name)
    assert result.passes, (
        f"{gate_name}: produced {result.produced}, expected {result.expected}"
    )


def test_xor_has_no_single_layer_solution():
    """Minsky-Papert 1969: brute-force search confirms no integer-stepped
    single M-P neuron computes XOR exactly."""
    proof = search_xor_single_layer(
        weight_range=(-3, 3),
        threshold_range=(-3, 3),
        step=0.5,
    )
    assert proof.no_solution
    assert proof.best_match_correct < 4
    assert proof.best_match_correct >= 3  # we can always nail 3 of 4 (any 3-corner subset)


def test_unknown_gate_rejected():
    with pytest.raises(ValueError):
        evaluate_gate("XOR")


def test_endpoint_evaluates_all_gates():
    client = TestClient(app)
    for name in GATES:
        response = client.get(f"/api/simulate/mcp/{name}")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["passes"] is True
        assert "McCulloch" in body["citation"]
        assert "10.1007/BF02478259" in body["citation"]


def test_endpoint_xor_search():
    client = TestClient(app)
    response = client.get("/api/simulate/mcp/xor-search")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["no_solution"] is True
    assert body["best_match_correct"] < 4
    assert "Minsky" in body["citation"]
