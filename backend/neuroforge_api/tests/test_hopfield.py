"""Hopfield network physics tests."""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from neuroforge_api.main import app
from neuroforge_api.simulators.hopfield import (
    hebbian_storage,
    simulate_hopfield,
)


def test_stored_pattern_is_a_fixed_point():
    """Async updates leave a stored pattern unchanged (no flips)."""
    rng = np.random.default_rng(0)
    patterns = rng.choice([-1, 1], size=(5, 80))
    W = hebbian_storage(patterns)
    s = patterns[2].copy()
    for i in rng.permutation(80):
        field = W[i] @ s
        new_val = 1 if field >= 0 else -1
        # Stored pattern is at a local min — every neuron's field has the right sign
        assert new_val == s[i], f"neuron {i} would flip"


def test_energy_is_monotone_non_increasing_in_async():
    """Hopfield energy E(s) cannot increase under async updates."""
    run = simulate_hopfield(n_neurons=100, n_patterns=8, corruption_fraction=0.2, seed=42)
    diffs = np.diff(run.energies)
    assert diffs.max() <= 1e-9, f"energy increased by {diffs.max()}"


def test_subcritical_capacity_recovers_pattern():
    """At α = K/N = 0.08, well below critical 0.138, retrieval succeeds."""
    run = simulate_hopfield(n_neurons=100, n_patterns=8, corruption_fraction=0.2, seed=42)
    assert run.converged
    assert run.final_overlap > 0.99


def test_overcapacity_fails_to_recover():
    """At α = 0.30, well above critical 0.138, retrieval fails."""
    run = simulate_hopfield(n_neurons=100, n_patterns=30, corruption_fraction=0.2, seed=42)
    assert not run.converged
    # And the achieved overlap is far from 1.0 — random would give ~0
    assert run.final_overlap < 0.9


def test_critical_capacity_boundary_is_unreliable():
    """Right at α ≈ 0.14 (just above the AGS bound of 0.138), at least one
    seed must fail to retrieve. We test multiple seeds and assert *some*
    of them fail — proves we're near the theoretical boundary, not above it
    everywhere by accident."""
    failures = 0
    for seed in range(10):
        run = simulate_hopfield(
            n_neurons=100, n_patterns=14, corruption_fraction=0.2, seed=seed
        )
        if not run.converged:
            failures += 1
    assert failures >= 1, "expected at least one retrieval failure near α_c"


def test_hebbian_storage_is_symmetric_zero_diagonal():
    rng = np.random.default_rng(1)
    patterns = rng.choice([-1, 1], size=(4, 32))
    W = hebbian_storage(patterns)
    assert W.shape == (32, 32)
    assert np.allclose(W, W.T)
    assert np.all(np.diag(W) == 0)


def test_hebbian_storage_rejects_non_bipolar():
    with pytest.raises(ValueError, match="bipolar"):
        hebbian_storage(np.array([[0, 1, -1], [1, 1, 1]]))


def test_invalid_arguments():
    with pytest.raises(ValueError):
        simulate_hopfield(n_neurons=2, n_patterns=1)
    with pytest.raises(ValueError):
        simulate_hopfield(n_neurons=20, n_patterns=0)
    with pytest.raises(ValueError):
        simulate_hopfield(n_neurons=20, n_patterns=2, corruption_fraction=1.5)
    with pytest.raises(ValueError):
        simulate_hopfield(n_neurons=20, n_patterns=2, target_index=99)


def test_endpoint_subcritical_recovery():
    client = TestClient(app)
    response = client.post(
        "/api/simulate/hopfield",
        json={
            "n_neurons": 64,
            "n_patterns": 5,
            "corruption_fraction": 0.2,
            "target_index": 0,
            "max_sweeps": 8,
            "seed": 42,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["converged"] is True
    assert body["final_overlap"] > 0.95
    assert "Hopfield JJ" in body["citation"]
    assert "10.1073/pnas.79.8.2554" in body["citation"]
    assert "Amit" in body["citation"]
    # All energy diffs are <= 0
    es = body["energies"]
    diffs = [es[i + 1] - es[i] for i in range(len(es) - 1)]
    assert max(diffs) <= 1e-9
