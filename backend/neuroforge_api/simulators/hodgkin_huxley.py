"""Hodgkin-Huxley single-compartment simulator using Brian2.

Implements the original 1952 squid giant axon model:
    Hodgkin AL, Huxley AF. A quantitative description of membrane current and
    its application to conduction and excitation in nerve.
    J Physiol. 1952 Aug;117(4):500-44.
    doi: 10.1113/jphysiol.1952.sp004764  PMID: 12991237  Nobel Prize 1963.

Parameters below are the canonical values stated in the 1952 paper, expressed
in the modern membrane-potential convention (V is the absolute potential, not
the displacement from rest). E_L is set to -54.387 mV so that the resting
potential of the full model is exactly -65 mV.

Per CLAUDE.md anti-theater rules: no hand-rolled ODE substitute. Brian2 is
the locked simulation engine. Every parameter below traces to the cited paper.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from brian2 import (
    Equations,
    NeuronGroup,
    SpikeMonitor,
    StateMonitor,
    defaultclock,
    ms,
    msiemens,
    mV,
    pamp,
    prefs,
    uamp,
    uF,
)
from brian2 import (
    run as brian2_run,
)

# Use numpy code-generation: avoids needing a C++ toolchain at request time.
# Slower than cython but tests stay <5s per simulation at the durations we use.
prefs.codegen.target = "numpy"

# Hodgkin & Huxley 1952 parameters. Working per unit area = 1 cm² so capacitance
# and conductances are absolute quantities of the model neuron.
C_m = 1.0 * uF
gbar_Na = 120.0 * msiemens
gbar_K = 36.0 * msiemens
g_L = 0.3 * msiemens
E_Na = 50.0 * mV
E_K = -77.0 * mV
E_L = -54.387 * mV

V_REST = -65.0 * mV
SPIKE_THRESHOLD = 0.0 * mV  # zero-crossing during AP rising phase

# Steady-state gating values at V = V_REST = -65 mV, computed once analytically.
_V_REST_MV = -65.0
_alpha_m_rest = 0.1 * (_V_REST_MV + 40.0) / (1.0 - np.exp(-(_V_REST_MV + 40.0) / 10.0))
_beta_m_rest = 4.0 * np.exp(-(_V_REST_MV + 65.0) / 18.0)
_alpha_h_rest = 0.07 * np.exp(-(_V_REST_MV + 65.0) / 20.0)
_beta_h_rest = 1.0 / (np.exp(-(_V_REST_MV + 35.0) / 10.0) + 1.0)
_alpha_n_rest = 0.01 * (_V_REST_MV + 55.0) / (1.0 - np.exp(-(_V_REST_MV + 55.0) / 10.0))
_beta_n_rest = 0.125 * np.exp(-(_V_REST_MV + 65.0) / 80.0)
M_REST = _alpha_m_rest / (_alpha_m_rest + _beta_m_rest)
H_REST = _alpha_h_rest / (_alpha_h_rest + _beta_h_rest)
N_REST = _alpha_n_rest / (_alpha_n_rest + _beta_n_rest)

# H-H rate equations. The (1e-9*mV) bias on the alpha_m / alpha_n numerators
# avoids the removable 0/0 singularity at V = -40 mV / V = -55 mV without
# changing the physical solution: the limit value is preserved. See:
#   Sterratt et al., Principles of Computational Modelling in Neuroscience, ch. 3.
_EQS = Equations(
    """
    dv/dt = (-gbar_Na*m**3*h*(v - E_Na) - gbar_K*n**4*(v - E_K) - g_L*(v - E_L) + I_ext) / C_m : volt
    I_ext : amp
    dm/dt = alpha_m*(1.0 - m) - beta_m*m : 1
    dh/dt = alpha_h*(1.0 - h) - beta_h*h : 1
    dn/dt = alpha_n*(1.0 - n) - beta_n*n : 1
    alpha_m = (0.1/mV) * (-(v + 40.0*mV) + 1e-9*mV) / (exp(-(v + 40.0*mV)/(10.0*mV)) - 1.0) / ms : Hz
    beta_m  = 4.0 * exp(-(v + 65.0*mV)/(18.0*mV)) / ms : Hz
    alpha_h = 0.07 * exp(-(v + 65.0*mV)/(20.0*mV)) / ms : Hz
    beta_h  = 1.0 / (exp(-(v + 35.0*mV)/(10.0*mV)) + 1.0) / ms : Hz
    alpha_n = (0.01/mV) * (-(v + 55.0*mV) + 1e-9*mV) / (exp(-(v + 55.0*mV)/(10.0*mV)) - 1.0) / ms : Hz
    beta_n  = 0.125 * exp(-(v + 65.0*mV)/(80.0*mV)) / ms : Hz
    """
)


@dataclass(frozen=True, slots=True)
class HHTrace:
    """Output of one simulation run.

    times_ms        — sample times in milliseconds, increasing
    voltage_mV      — membrane potential in mV at each sample time
    spike_times_ms  — times of detected spike events (zero-crossing)
    stimulus_uA     — applied current in µA at each sample time
    dt_ms           — integration step
    """

    times_ms: np.ndarray
    voltage_mV: np.ndarray
    spike_times_ms: np.ndarray
    stimulus_uA: np.ndarray
    dt_ms: float


def simulate_hh(
    *,
    duration_ms: float,
    stimulus_uA: float,
    stimulus_start_ms: float = 0.0,
    stimulus_end_ms: float | None = None,
    dt_ms: float = 0.01,
    record_every_n: int = 4,
) -> HHTrace:
    """Run a single-compartment HH simulation under a step current.

    Args:
        duration_ms: total simulated time in ms.
        stimulus_uA: amplitude of injected current in µA (per cm² of membrane,
            equivalent to absolute current under our unit-area normalization).
        stimulus_start_ms: time at which the step turns on. Default 0.
        stimulus_end_ms: time at which the step turns off. Default = duration.
        dt_ms: integration step in ms. 0.01 reproduces canonical AP shape.
        record_every_n: subsample factor for the returned trace (does not affect
            integration accuracy). 4 → ~25 kHz output sampling at dt=0.01.

    Returns:
        HHTrace with times, voltage, detected spike times, and stimulus profile.
    """
    if duration_ms <= 0:
        raise ValueError("duration_ms must be > 0")
    if dt_ms <= 0:
        raise ValueError("dt_ms must be > 0")
    if record_every_n < 1:
        raise ValueError("record_every_n must be >= 1")
    end = duration_ms if stimulus_end_ms is None else stimulus_end_ms
    if end < stimulus_start_ms:
        raise ValueError("stimulus_end_ms must be >= stimulus_start_ms")

    defaultclock.dt = dt_ms * ms

    neuron = NeuronGroup(
        1,
        model=_EQS,
        method="exponential_euler",
        threshold=f"v > {SPIKE_THRESHOLD / mV}*mV",
        refractory=f"v > {SPIKE_THRESHOLD / mV}*mV",
        namespace={
            "C_m": C_m,
            "gbar_Na": gbar_Na,
            "gbar_K": gbar_K,
            "g_L": g_L,
            "E_Na": E_Na,
            "E_K": E_K,
            "E_L": E_L,
        },
    )
    neuron.v = V_REST
    neuron.m = M_REST
    neuron.h = H_REST
    neuron.n = N_REST
    neuron.I_ext = 0 * pamp

    state_mon = StateMonitor(neuron, ["v", "I_ext"], record=True, dt=dt_ms * record_every_n * ms)
    spike_mon = SpikeMonitor(neuron)

    # Phase 1 (pre-stimulus)
    if stimulus_start_ms > 0:
        brian2_run(stimulus_start_ms * ms)
    # Phase 2 (stimulus on)
    neuron.I_ext = stimulus_uA * uamp
    on_duration_ms = max(end - stimulus_start_ms, 0.0)
    if on_duration_ms > 0:
        brian2_run(on_duration_ms * ms)
    # Phase 3 (stimulus off, post-stimulus tail)
    neuron.I_ext = 0 * pamp
    tail_ms = max(duration_ms - end, 0.0)
    if tail_ms > 0:
        brian2_run(tail_ms * ms)

    times_ms = np.asarray(state_mon.t / ms)
    voltage_mV = np.asarray(state_mon.v[0] / mV)
    stim_uA = np.asarray(state_mon.I_ext[0] / uamp)
    spikes_ms = np.asarray(spike_mon.t / ms)

    return HHTrace(
        times_ms=times_ms,
        voltage_mV=voltage_mV,
        spike_times_ms=spikes_ms,
        stimulus_uA=stim_uA,
        dt_ms=dt_ms,
    )
