"""Hebbian learning physics tests."""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from neuroforge_api.main import app
from neuroforge_api.simulators.hebbian import simulate_hebbian


def test_pure_hebb_runs_away():
    """|w| under pure Hebb grows unbounded under correlated input."""
    tr = simulate_hebbian(
        rule="hebb",
        n_iterations=2000,
        learning_rate=0.005,
        correlation=0.8,
        seed=0,
        record_every_n=200,
    )
    initial = tr.weight_norm[0]
    final = tr.weight_norm[-1]
    # Final norm should be many orders of magnitude larger than initial
    assert final > 1e3 * initial


def test_oja_stabilizes_norm_at_one():
    """|w| under Oja's rule converges to 1 (the rule's fixed point)."""
    tr = simulate_hebbian(
        rule="oja",
        n_iterations=2000,
        learning_rate=0.01,
        correlation=0.8,
        seed=0,
        record_every_n=200,
    )
    final = tr.weight_norm[-1]
    assert abs(final - 1.0) < 0.05  # within 5% of unit norm


def test_both_rules_align_to_principal_component():
    """Hebb and Oja should both rotate w toward the principal eigenvector."""
    for rule in ("hebb", "oja"):
        tr = simulate_hebbian(
            rule=rule,
            n_iterations=3000,
            learning_rate=0.005,
            correlation=0.8,
            seed=0,
            record_every_n=300,
        )
        # Final angle should be small (within 5° of principal direction).
        assert tr.weight_angle_deg[-1] < 5.0, (
            f"{rule}: final angle {tr.weight_angle_deg[-1]:.2f}° too large"
        )


def test_oja_robustness_across_seeds():
    """Oja's fixed point is independent of initial conditions."""
    norms = []
    for seed in range(5):
        tr = simulate_hebbian(
            rule="oja",
            n_iterations=3000,
            learning_rate=0.01,
            correlation=0.8,
            seed=seed,
            record_every_n=3000,
        )
        norms.append(tr.weight_norm[-1])
    norms_arr = np.array(norms)
    assert (abs(norms_arr - 1.0) < 0.05).all()


def test_uncorrelated_input_no_principal_direction_preference():
    """With correlation=0, the input has no preferred axis; principal direction
    is arbitrary but Oja's |w| still converges to 1."""
    tr = simulate_hebbian(
        rule="oja",
        n_iterations=3000,
        learning_rate=0.01,
        correlation=0.0,
        seed=0,
        record_every_n=3000,
    )
    assert abs(tr.weight_norm[-1] - 1.0) < 0.1


def test_invalid_arguments_rejected():
    with pytest.raises(ValueError):
        simulate_hebbian(rule="bogus", n_iterations=10, learning_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        simulate_hebbian(rule="oja", n_iterations=0, learning_rate=0.01)
    with pytest.raises(ValueError):
        simulate_hebbian(rule="oja", n_iterations=10, learning_rate=-0.01)
    with pytest.raises(ValueError):
        simulate_hebbian(rule="oja", n_iterations=10, learning_rate=0.01, correlation=1.5)


def test_hebbian_endpoint_runs_both_rules():
    client = TestClient(app)
    response = client.post(
        "/api/simulate/hebbian",
        json={"n_iterations": 1500, "learning_rate": 0.005, "correlation": 0.8},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "Hebb" in body["citation"] and "Oja" in body["citation"]
    assert "Bliss" in body["citation"]
    assert "10.1113/jphysiol.1973.sp010273" in body["citation"]
    assert len(body["iterations"]) == len(body["hebb_norm"])
    assert len(body["iterations"]) == len(body["oja_norm"])
    # Hebb should be much larger than Oja at final step
    assert body["hebb_norm"][-1] > 100 * body["oja_norm"][-1]
    assert abs(body["oja_norm"][-1] - 1.0) < 0.1
