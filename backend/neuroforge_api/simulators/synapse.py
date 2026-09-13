"""Synapse-level kinetics — AMPA, NMDA (with Mg²⁺ block) and GABA-A conductances.

This is the molecular rung of the scale ladder: below the neuron sits the
synapse, and its currents are what Hebb/STDP/LTP actually modify.

Reference (two-state kinetic receptor model, the standard for all three):
    Destexhe A, Mainen ZF, Sejnowski TJ. An efficient method for computing
    synaptic conductances based on a kinetic model of receptor binding.
    Neural Comput. 1994;6(1):14-18. doi:10.1162/neco.1994.6.1.14

Reference (NMDA voltage-dependent Mg²⁺ block — the coincidence detector):
    Jahr CE, Stevens CF. Voltage dependence of NMDA-activated macroscopic
    conductances predicted by single-channel kinetics. J Neurosci.
    1990;10(9):3178-3182. doi:10.1523/JNEUROSCI.10-09-03178.1990
        B(V) = 1 / (1 + [Mg²⁺]/3.57 mM · exp(−0.062 · V/mV))

Reference (NMDA receptor as the trigger for LTP):
    Collingridge GL, Kehl SJ, McLennan H. Excitatory amino acids in synaptic
    transmission in the Schaffer collateral-commissural pathway of the rat
    hippocampus. J Physiol. 1983;334(1):33-46.
    doi:10.1113/jphysiol.1983.sp014478

Model (per receptor, dual-exponential conductance from the kinetic scheme):
    g(t) = g_max · (exp(−t/τ_decay) − exp(−t/τ_rise)) / norm,  norm scales the peak to g_max
    I(t) = g(t) · B(V) · (V − E_rev)                    B ≡ 1 for AMPA and GABA-A

Time constants and reversal potentials are the Destexhe 1994/1998 fits (cited
in the RECEPTOR table). Holding voltage is user-set. Output is current in pA
for a 1 nS peak conductance so the three receptors are comparable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MG_HALF_BLOCK_MM = 3.57      # Jahr & Stevens 1990
MG_VOLTAGE_SLOPE = 0.062     # per mV, Jahr & Stevens 1990


@dataclass(frozen=True, slots=True)
class ReceptorKinetics:
    key: str
    name: str
    transmitter: str
    tau_rise_ms: float
    tau_decay_ms: float
    e_rev_mV: float
    mg_block: bool
    citation: str


# Kinetic constants from Destexhe, Mainen & Sejnowski's fits to hippocampal /
# cortical recordings (Destexhe 1994 Neural Comput; Destexhe, Mainen &
# Sejnowski 1998, "Kinetic models of synaptic transmission", in Methods in
# Neuronal Modeling 2nd ed., MIT Press — the standard reference table).
RECEPTORS: tuple[ReceptorKinetics, ...] = (
    ReceptorKinetics(
        key="AMPA",
        name="AMPA receptor (fast excitatory)",
        transmitter="glutamate",
        tau_rise_ms=0.4,
        tau_decay_ms=2.0,
        e_rev_mV=0.0,
        mg_block=False,
        citation="Destexhe A, Mainen ZF, Sejnowski TJ. Neural Comput. 1994;6(1):14-18. doi:10.1162/neco.1994.6.1.14",
    ),
    ReceptorKinetics(
        key="NMDA",
        name="NMDA receptor (slow excitatory, Mg²⁺-gated coincidence detector)",
        transmitter="glutamate",
        tau_rise_ms=2.0,
        tau_decay_ms=100.0,
        e_rev_mV=0.0,
        mg_block=True,
        citation="Jahr CE, Stevens CF. J Neurosci. 1990;10(9):3178-3182. doi:10.1523/JNEUROSCI.10-09-03178.1990; Destexhe 1994 doi:10.1162/neco.1994.6.1.14",
    ),
    ReceptorKinetics(
        key="GABA_A",
        name="GABA-A receptor (fast inhibitory, Cl⁻)",
        transmitter="GABA",
        tau_rise_ms=0.5,
        tau_decay_ms=10.0,
        e_rev_mV=-70.0,
        mg_block=False,
        citation="Destexhe A, Mainen ZF, Sejnowski TJ. Neural Comput. 1994;6(1):14-18. doi:10.1162/neco.1994.6.1.14",
    ),
)


def receptor(key: str) -> ReceptorKinetics:
    for r in RECEPTORS:
        if r.key == key:
            return r
    raise KeyError(key)


def mg_block(v_mV: float | np.ndarray, mg_mM: float = 1.0) -> float | np.ndarray:
    """Jahr-Stevens 1990 fraction of NMDA channels NOT blocked by Mg²⁺ at voltage V."""
    if mg_mM < 0:
        raise ValueError("mg_mM must be >= 0")
    return 1.0 / (1.0 + (mg_mM / MG_HALF_BLOCK_MM) * np.exp(-MG_VOLTAGE_SLOPE * np.asarray(v_mV)))


def dual_exponential(t_ms: np.ndarray, tau_rise: float, tau_decay: float) -> np.ndarray:
    """Unit-peak dual-exponential conductance waveform."""
    if tau_decay <= tau_rise:
        raise ValueError("tau_decay must exceed tau_rise")
    t = np.clip(t_ms, 0.0, None)
    raw = np.exp(-t / tau_decay) - np.exp(-t / tau_rise)
    # analytic time of peak → normalize to 1
    t_peak = (tau_rise * tau_decay / (tau_decay - tau_rise)) * np.log(tau_decay / tau_rise)
    peak = np.exp(-t_peak / tau_decay) - np.exp(-t_peak / tau_rise)
    return raw / peak


@dataclass(frozen=True, slots=True)
class SynapseTrace:
    key: str
    times_ms: np.ndarray
    conductance_nS: np.ndarray
    current_pA: np.ndarray
    holding_mV: float
    mg_mM: float
    block_fraction: float   # B(V) applied (1.0 when no Mg block)
    g_max_nS: float


def simulate_synapse(
    key: str,
    *,
    holding_mV: float = -65.0,
    g_max_nS: float = 1.0,
    mg_mM: float = 1.0,
    duration_ms: float = 200.0,
    dt_ms: float = 0.1,
    onset_ms: float = 5.0,
) -> SynapseTrace:
    """Postsynaptic current for one transmitter release event at a clamped voltage."""
    if duration_ms <= 0 or dt_ms <= 0 or g_max_nS < 0 or onset_ms < 0:
        raise ValueError("duration_ms, dt_ms > 0; g_max_nS, onset_ms >= 0")
    r = receptor(key)
    times = np.arange(0.0, duration_ms, dt_ms)
    g = g_max_nS * dual_exponential(times - onset_ms, r.tau_rise_ms, r.tau_decay_ms)
    g[times < onset_ms] = 0.0
    b = float(mg_block(holding_mV, mg_mM)) if r.mg_block else 1.0
    # I = g · B · (V − E),  nS · mV = pA
    current = g * b * (holding_mV - r.e_rev_mV)
    return SynapseTrace(
        key=key,
        times_ms=times,
        conductance_nS=g,
        current_pA=current,
        holding_mV=holding_mV,
        mg_mM=mg_mM,
        block_fraction=b,
        g_max_nS=g_max_nS,
    )


def nmda_iv_curve(
    *, v_min_mV: float = -90.0, v_max_mV: float = 40.0, points: int = 131, mg_mM: float = 1.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Peak NMDA current vs holding voltage — the famous J-shaped I–V (Jahr-Stevens).

    Returns (V, I_with_Mg, I_without_Mg) for 1 nS peak conductance.
    """
    if points < 3 or v_max_mV <= v_min_mV:
        raise ValueError("points >= 3 and v_max > v_min required")
    v = np.linspace(v_min_mV, v_max_mV, points)
    e_rev = receptor("NMDA").e_rev_mV
    with_mg = mg_block(v, mg_mM) * (v - e_rev)
    without = (v - e_rev)
    return v, with_mg, without
