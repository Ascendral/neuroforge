"""Synapse kinetics tests — Destexhe 1994 dual-exponential + Jahr-Stevens 1990 Mg block."""

from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from neuroforge_api.main import app
from neuroforge_api.simulators.synapse import (
    RECEPTORS,
    dual_exponential,
    mg_block,
    nmda_iv_curve,
    receptor,
    simulate_synapse,
)


def test_dual_exponential_unit_peak_and_timescales():
    t = np.arange(0, 400, 0.05)
    for r in RECEPTORS:
        g = dual_exponential(t, r.tau_rise_ms, r.tau_decay_ms)
        assert abs(g.max() - 1.0) < 1e-3  # sampled at 0.05 ms; analytic peak is exactly 1
        # decays to < 5% within ~3 decay constants after peak
        t_peak = t[np.argmax(g)]
        idx = np.searchsorted(t, t_peak + 3.5 * r.tau_decay_ms)
        assert g[idx] < 0.05


def test_jahr_stevens_block_values():
    """At −65 mV and 1 mM Mg²⁺ only a few % of NMDA channels conduct; at +40 mV nearly all."""
    b_rest = float(mg_block(-65.0, 1.0))
    b_depol = float(mg_block(40.0, 1.0))
    assert 0.03 < b_rest < 0.12
    assert b_depol > 0.95
    assert float(mg_block(-65.0, 0.0)) == 1.0  # no Mg → no block
    # closed form check
    v = -30.0
    expected = 1.0 / (1.0 + (1.0 / 3.57) * np.exp(-0.062 * v))
    assert abs(float(mg_block(v, 1.0)) - expected) < 1e-12


def test_sign_of_currents_at_rest():
    ampa = simulate_synapse("AMPA", holding_mV=-65.0)
    nmda = simulate_synapse("NMDA", holding_mV=-65.0)
    gaba = simulate_synapse("GABA_A", holding_mV=-65.0)
    assert ampa.current_pA.min() < 0  # inward (excitatory)
    assert nmda.current_pA.min() < 0
    assert abs(nmda.current_pA.min()) < abs(ampa.current_pA.min())  # Mg block shrinks NMDA
    assert gaba.current_pA.max() > 0  # outward at −65 (E_Cl = −70)
    # GABA-A at its reversal potential carries no current
    assert np.allclose(simulate_synapse("GABA_A", holding_mV=-70.0).current_pA, 0.0)


def test_nmda_iv_is_j_shaped():
    v, i_mg, i_free = nmda_iv_curve()
    # with Mg: current magnitude at −80 is SMALLER than at −20 (the J)
    assert abs(np.interp(-80, v, i_mg)) < abs(np.interp(-20, v, i_mg))
    # without Mg: linear, larger magnitude at more negative V
    assert abs(np.interp(-80, v, i_free)) > abs(np.interp(-20, v, i_free))
    # both cross zero at E_rev = 0
    assert abs(np.interp(0, v, i_mg)) < 1e-9


def test_nmda_slow_ampa_fast():
    assert receptor("NMDA").tau_decay_ms > 10 * receptor("AMPA").tau_decay_ms


def test_endpoint():
    client = TestClient(app)
    r = client.post("/api/simulate/synapse", json={"holding_mV": -65, "duration_ms": 100, "dt_ms": 0.5})
    assert r.status_code == 200, r.text
    body = r.json()
    assert [t["key"] for t in body["traces"]] == ["AMPA", "NMDA", "GABA_A"]
    assert len(body["times_ms"]) == len(body["traces"][0]["current_pA"]) == 200
    assert len(body["nmda_iv_voltage_mV"]) == len(body["nmda_iv_with_mg_pA"])
    assert "10.1523/JNEUROSCI.10-09-03178.1990" in body["citation"]
