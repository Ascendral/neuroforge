"""V1 receptive-field tests against published Hubel-Wiesel / Gabor properties."""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from neuroforge_api.main import app
from neuroforge_api.simulators.hubel_wiesel import (
    complex_cell_response,
    gabor_filter,
    orientation_tuning_curve,
    simple_cell_response,
)


def test_gabor_is_zero_mean():
    """A Gabor envelope × cosine carrier integrates to ~0 (band-pass)."""
    g = gabor_filter(image_size=65, orientation_deg=0, spatial_frequency_cyc_per_px=0.1)
    assert g.shape == (65, 65)
    assert abs(g.sum()) < 5.0  # tiny vs the per-pixel range of [-1, +1]


def test_gabor_energy_is_rotation_invariant():
    """Rotating the Gabor preserves total energy ∑ G²."""
    base = (gabor_filter(image_size=65, orientation_deg=0, spatial_frequency_cyc_per_px=0.1) ** 2).sum()
    for theta in (15, 45, 90, 135):
        rot = (gabor_filter(image_size=65, orientation_deg=theta, spatial_frequency_cyc_per_px=0.1) ** 2).sum()
        assert rot == pytest.approx(base, rel=0.05)


def test_orientation_tuning_peaks_at_preferred():
    """Peak of the tuning curve must equal the preferred orientation (mod 180°)."""
    for theta_pref in [0.0, 30.0, 45.0, 90.0, 135.0]:
        tc = orientation_tuning_curve(
            preferred_orientation_deg=theta_pref,
            spatial_frequency_cyc_per_px=0.1,
            n_orientations=36,
        )
        peak_simple = tc.orientations_deg[int(np.argmax(tc.simple_responses))]
        peak_complex = tc.orientations_deg[int(np.argmax(tc.complex_responses))]
        # Tuning curve resolution is 180/36 = 5°; peak must be within one bin.
        assert abs(peak_simple - theta_pref) < 5.1
        assert abs(peak_complex - theta_pref) < 5.1


def test_orthogonal_response_is_far_below_preferred():
    """Bar 90° from preferred orientation should drive cell weakly."""
    tc = orientation_tuning_curve(
        preferred_orientation_deg=0.0,
        spatial_frequency_cyc_per_px=0.1,
        n_orientations=36,
    )
    pref_resp = tc.simple_responses[0]
    ortho_idx = int(np.argmin(abs(tc.orientations_deg - 90.0)))
    assert tc.simple_responses[ortho_idx] < 0.05 * pref_resp


def test_simple_cell_rectifies_negative_input():
    """Anti-correlated stimulus produces zero (not negative) simple-cell response."""
    g = gabor_filter(image_size=65, orientation_deg=0, spatial_frequency_cyc_per_px=0.1)
    # Use the negation of the Gabor itself as a maximally anti-correlated stim
    response = simple_cell_response(-g, g)
    assert response == 0.0


def test_complex_cell_is_phase_invariant_to_carrier_shift():
    """Adelson-Bergen energy: the modulus is invariant under carrier phase shift.

    For an input that is a phase-shifted copy of the Gabor itself, the
    complex-cell response should be (approximately) constant regardless of
    the phase of the input. This is the canonical test that distinguishes
    complex from simple cells.
    """
    even = gabor_filter(image_size=65, orientation_deg=0, spatial_frequency_cyc_per_px=0.1, phase_deg=0)
    odd = gabor_filter(image_size=65, orientation_deg=0, spatial_frequency_cyc_per_px=0.1, phase_deg=90)
    responses = []
    for phase in [0, 30, 60, 90, 120, 150]:
        stim = gabor_filter(image_size=65, orientation_deg=0, spatial_frequency_cyc_per_px=0.1, phase_deg=phase)
        responses.append(complex_cell_response(stim, even, odd))
    # All within 1% of mean → phase-invariant
    mean = float(np.mean(responses))
    for r in responses:
        assert abs(r - mean) / mean < 0.01


def test_endpoint_returns_canonical_tuning_curve():
    client = TestClient(app)
    response = client.post(
        "/api/simulate/v1",
        json={"preferred_orientation_deg": 45.0, "spatial_frequency_cyc_per_px": 0.1},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["preferred_orientation_deg"] == 45.0
    assert "Hubel" in body["citation"] and "Wiesel" in body["citation"]
    assert "10.1113/jphysiol.1962.sp006837" in body["citation"]
    assert len(body["tuning_orientations_deg"]) == len(body["tuning_simple"])
    assert len(body["tuning_orientations_deg"]) == len(body["tuning_complex"])
    peak_idx = int(np.argmax(body["tuning_simple"]))
    assert abs(body["tuning_orientations_deg"][peak_idx] - 45.0) < 5.1
    # Filter visualization arrays are returned with right shapes
    assert len(body["gabor_even"]) == body["image_size"]
    assert len(body["gabor_even"][0]) == body["image_size"]
    assert len(body["gabor_odd"]) == body["image_size"]


def test_endpoint_rejects_invalid_input():
    client = TestClient(app)
    response = client.post(
        "/api/simulate/v1",
        json={"preferred_orientation_deg": 0, "spatial_frequency_cyc_per_px": -0.1},
    )
    assert response.status_code == 422
