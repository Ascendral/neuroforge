"""Validation tests for the Hodgkin-Huxley simulator.

These tests verify *qualitative* canonical behavior of the H-H 1952 model.
Specific numeric tolerances are loose enough to pass on any correct
implementation but tight enough that a wrong sign, a missing channel, or a
unit error would break them. They are NOT regression tests against a
particular numerical run; they are physics tests.

Reference: Hodgkin & Huxley 1952, J Physiol 117:500-544.
"""

from __future__ import annotations

import numpy as np
import pytest

from neuroforge_api.simulators.hodgkin_huxley import (
    H_REST,
    M_REST,
    N_REST,
    simulate_hh,
)


def test_resting_steady_state_gating_values():
    """At V_rest = -65 mV, the gating steady states must match published values.

    Published (Hodgkin-Huxley 1952, modern shifted form):
      m∞(-65) ≈ 0.05, h∞(-65) ≈ 0.60, n∞(-65) ≈ 0.32
    """
    assert M_REST == pytest.approx(0.0529, abs=0.005)
    assert H_REST == pytest.approx(0.5961, abs=0.01)
    assert N_REST == pytest.approx(0.3177, abs=0.01)


def test_rests_at_minus_65_with_no_stimulus():
    """No injected current → membrane stays at the resting potential (-65 mV)."""
    trace = simulate_hh(duration_ms=30.0, stimulus_uA=0.0)
    # Voltage should not drift more than 0.5 mV from rest, and never spike.
    assert trace.voltage_mV.min() > -65.5
    assert trace.voltage_mV.max() < -64.5
    assert len(trace.spike_times_ms) == 0


def test_subthreshold_pulse_does_not_spike():
    """A small (1 µA) sustained current depolarizes but does not fire.

    Published rheobase for the H-H equations is roughly 2.3 µA/cm². Below
    that, the cell sits at an elevated steady state with no AP.
    """
    trace = simulate_hh(
        duration_ms=50.0,
        stimulus_uA=1.0,
        stimulus_start_ms=5.0,
        stimulus_end_ms=45.0,
    )
    assert len(trace.spike_times_ms) == 0
    # Voltage should depolarize past rest but never overshoot 0 mV.
    assert trace.voltage_mV.max() < 0.0
    assert trace.voltage_mV.max() > -65.0


def test_suprathreshold_step_produces_action_potential():
    """A 10 µA step elicits action potentials with canonical overshoot.

    Canonical AP peak is between +30 and +50 mV; afterhyperpolarization
    (AHP) trough is between -75 and -90 mV.
    """
    trace = simulate_hh(
        duration_ms=80.0,
        stimulus_uA=10.0,
        stimulus_start_ms=10.0,
        stimulus_end_ms=70.0,
    )
    assert len(trace.spike_times_ms) >= 1
    assert trace.voltage_mV.max() > 30.0
    assert trace.voltage_mV.max() < 60.0
    # AHP after at least one spike
    assert trace.voltage_mV.min() < -65.0


def test_repetitive_firing_under_sustained_current():
    """A 10 µA step over 60 ms should produce >=3 spikes (~50-70 Hz)."""
    trace = simulate_hh(
        duration_ms=80.0,
        stimulus_uA=10.0,
        stimulus_start_ms=10.0,
        stimulus_end_ms=70.0,
    )
    assert len(trace.spike_times_ms) >= 3
    # Inter-spike intervals must be roughly stable (CV < 0.3) — H-H is regular.
    if len(trace.spike_times_ms) >= 3:
        isis = np.diff(trace.spike_times_ms)
        assert isis.std() / isis.mean() < 0.3


def test_higher_current_increases_firing_rate():
    """f-I curve monotonicity: 20 µA must spike at least as fast as 5 µA."""
    low = simulate_hh(
        duration_ms=80.0,
        stimulus_uA=5.0,
        stimulus_start_ms=10.0,
        stimulus_end_ms=70.0,
    )
    high = simulate_hh(
        duration_ms=80.0,
        stimulus_uA=20.0,
        stimulus_start_ms=10.0,
        stimulus_end_ms=70.0,
    )
    assert len(high.spike_times_ms) >= len(low.spike_times_ms)


def test_invalid_arguments_rejected():
    with pytest.raises(ValueError):
        simulate_hh(duration_ms=-1.0, stimulus_uA=0.0)
    with pytest.raises(ValueError):
        simulate_hh(duration_ms=10.0, stimulus_uA=0.0, dt_ms=0.0)
    with pytest.raises(ValueError):
        simulate_hh(duration_ms=10.0, stimulus_uA=0.0, record_every_n=0)
    with pytest.raises(ValueError):
        simulate_hh(
            duration_ms=10.0,
            stimulus_uA=0.0,
            stimulus_start_ms=8.0,
            stimulus_end_ms=2.0,
        )
