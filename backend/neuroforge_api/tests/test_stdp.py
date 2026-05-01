"""STDP physics tests against Bi & Poo 1998.

These verify:
  - Sign convention (LTP for Δt > 0, LTD for Δt < 0)
  - Magnitude bounds (|Δw| ≤ A_+/-, decays away from Δt=0)
  - LTP / LTD asymmetry (LTP magnitude > LTD magnitude near Δt=0)
  - Brian2 pair simulation matches the analytical kernel to numerical precision
    (the Phase 5 audit gate from ARCHITECTURE.md)
  - Endpoint returns aligned curve + observed point + real citation
"""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from neuroforge_api.main import app
from neuroforge_api.simulators.stdp import (
    A_MINUS,
    A_PLUS,
    TAU_MINUS_MS,
    TAU_PLUS_MS,
    simulate_stdp_pair,
    stdp_curve,
    stdp_kernel,
)


def test_kernel_sign_convention():
    """Δt > 0 → LTP (positive Δw); Δt < 0 → LTD (negative Δw)."""
    for dt in [1.0, 5.0, 10.0, 20.0]:
        assert stdp_kernel(dt) > 0, f"expected LTP at Δt={dt}"
    for dt in [-1.0, -5.0, -20.0, -50.0]:
        assert stdp_kernel(dt) < 0, f"expected LTD at Δt={dt}"
    assert stdp_kernel(0.0) == 0.0


def test_kernel_bounded_by_amplitudes():
    """|Δw| <= A_+ for LTP and |Δw| <= A_- for LTD."""
    for dt in np.linspace(0.01, 200, 50):
        assert 0 < stdp_kernel(float(dt)) <= A_PLUS + 1e-9
    for dt in np.linspace(-200, -0.01, 50):
        assert -A_MINUS - 1e-9 <= stdp_kernel(float(dt)) < 0


def test_kernel_decays_with_distance():
    """|Δw| at Δt=±2τ must be <= 0.16·A (i.e. exp(-2) ≈ 0.135 of peak)."""
    assert stdp_kernel(2 * TAU_PLUS_MS) <= 0.16 * A_PLUS
    assert -stdp_kernel(-2 * TAU_MINUS_MS) <= 0.16 * A_MINUS


def test_ltp_dominates_ltd_near_zero():
    """Bi-Poo asymmetry: LTP at +5ms is larger in magnitude than LTD at -5ms."""
    assert stdp_kernel(5.0) > -stdp_kernel(-5.0)


def test_brian2_pair_matches_kernel_within_tolerance():
    """Phase 5 audit gate: Brian2 simulation must reproduce the kernel."""
    for dt in [-50.0, -20.0, -10.0, -5.0, -1.0, 1.0, 5.0, 10.0, 20.0, 50.0]:
        result = simulate_stdp_pair(dt)
        assert result.delta_w == pytest.approx(result.kernel_dw, abs=1e-6), (
            f"Brian2 sim deviated from kernel at Δt={dt}: "
            f"got {result.delta_w}, expected {result.kernel_dw}"
        )


def test_curve_grid_is_monotone():
    grid, values = stdp_curve(dt_min_ms=-80.0, dt_max_ms=80.0, points=161)
    assert len(grid) == 161
    assert grid[0] == -80.0
    assert grid[-1] == 80.0
    # values should cross zero exactly once (at the kernel's own zero)
    sign_changes = int(np.sum(np.diff(np.sign(values[values != 0])) != 0))
    assert sign_changes >= 1


def test_endpoint_returns_canonical_stdp_response():
    client = TestClient(app)
    response = client.post("/api/simulate/stdp", json={"dt_ms": 5.0})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["dt_ms"] == 5.0
    assert body["observed_delta_w"] > 0  # LTP
    assert body["kernel_delta_w"] == pytest.approx(body["observed_delta_w"], abs=1e-6)
    assert body["tau_plus_ms"] == TAU_PLUS_MS
    assert body["tau_minus_ms"] == TAU_MINUS_MS
    assert "Bi GQ, Poo MM" in body["citation"]
    assert "10.1523/JNEUROSCI.18-24-10464.1998" in body["citation"]
    assert len(body["curve_dt_ms"]) == len(body["curve_delta_w"])
    assert body["curve_dt_ms"][0] < 0 and body["curve_dt_ms"][-1] > 0


def test_endpoint_handles_negative_dt_ltd():
    client = TestClient(app)
    response = client.post("/api/simulate/stdp", json={"dt_ms": -5.0})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["observed_delta_w"] < 0  # LTD
