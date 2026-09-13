"""Modern Hopfield (Ramsauer 2021) tests.

Verify:
  - one update step is numerically identical to scaled dot-product attention with K=V=X
  - energy is non-increasing under the update (Ramsauer 2021 Theorem 1)
  - modern net retrieves far beyond the classic 0.138·d bound on the SAME patterns
  - classic net fails there (sanity: the comparison is fair)
  - capacity sweep shows the crossover
  - endpoint returns aligned arrays + real citation
"""

from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from neuroforge_api.main import app
from neuroforge_api.simulators.hopfield import simulate_hopfield
from neuroforge_api.simulators.modern_hopfield import (
    CLASSIC_CRITICAL_ALPHA,
    attention,
    capacity_sweep,
    modern_energy,
    modern_update,
    simulate_modern_hopfield,
)


def test_update_is_attention():
    rng = np.random.default_rng(0)
    X = rng.choice([-1.0, 1.0], size=(32, 40))
    xi = rng.normal(size=32)
    beta = 0.7
    lhs = modern_update(X, xi, beta)
    rhs = attention(xi[None, :], X.T, X.T, beta)[0]
    np.testing.assert_allclose(lhs, rhs, atol=1e-12)


def test_energy_monotone_non_increasing():
    rng = np.random.default_rng(1)
    X = rng.choice([-1.0, 1.0], size=(48, 96))
    xi = rng.normal(size=48)
    beta = 1.0
    prev = modern_energy(X, xi, beta)
    for _ in range(6):
        xi = modern_update(X, xi, beta)
        e = modern_energy(X, xi, beta)
        assert e <= prev + 1e-9
        prev = e


def test_modern_retrieves_past_classic_capacity_same_patterns():
    run = simulate_modern_hopfield(d=64, n_patterns=64, corruption_fraction=0.2, seed=42)
    assert run.alpha == 1.0 > CLASSIC_CRITICAL_ALPHA
    assert run.modern_overlaps[-1] > 0.95
    assert run.classic_overlap < 0.6
    # first-update attention row concentrates on the target pattern
    assert int(np.argmax(run.modern_attention_weights)) == run.target_index
    assert run.attention_max_abs_diff < 1e-9


def test_same_patterns_as_classic_module():
    """Fair comparison: the modern module draws the identical pattern set the
    classic module draws for the same seed."""
    classic = simulate_hopfield(n_neurons=64, n_patterns=6, seed=42)
    modern = simulate_modern_hopfield(d=64, n_patterns=6, seed=42)
    np.testing.assert_array_equal(classic.patterns[0], modern.target.astype(np.int8))


def test_capacity_sweep_crossover():
    s = capacity_sweep(d=64, n_trials=5, seed=7)
    a = s.alphas
    assert s.classic_success[a <= 0.1].mean() >= 0.8
    assert s.classic_success[a >= 0.5].max() <= 0.2
    assert s.modern_success[a >= 0.5].min() >= 0.8


def test_low_beta_blends_patterns():
    """Ramsauer Thm 4: small β → metastable averaged states. Retrieval should
    degrade at high load with the transformer β = 1/√d on raw patterns."""
    hi = simulate_modern_hopfield(d=64, n_patterns=128, beta=1.0, seed=3)
    lo = simulate_modern_hopfield(d=64, n_patterns=128, beta=1 / 8, seed=3)
    assert hi.modern_overlaps[-1] > 0.95
    assert lo.modern_overlaps[-1] < hi.modern_overlaps[-1]


def test_endpoint():
    client = TestClient(app)
    r = client.post("/api/simulate/modern-hopfield", json={"d": 36, "n_patterns": 36, "sweep_trials": 2})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["target"]) == 36 == len(body["modern_final"]) == len(body["classic_final"])
    assert len(body["modern_energies"]) == len(body["modern_overlaps"]) == 4
    assert body["sweep"] is not None and len(body["sweep"]["alphas"]) == len(body["sweep"]["modern_success"])
    assert "10.48550/arXiv.2008.02217" in body["citation"]
    assert body["classic_critical_alpha"] == CLASSIC_CRITICAL_ALPHA
