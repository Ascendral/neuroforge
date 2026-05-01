"""Spike-timing-dependent plasticity (STDP) — Bi & Poo 1998 hippocampal kernel.

Reference:
    Bi GQ, Poo MM. Synaptic modifications in cultured hippocampal neurons:
    dependence on spike timing, synaptic strength, and postsynaptic cell type.
    J Neurosci. 1998 Dec 15;18(24):10464-72.
    doi:10.1523/JNEUROSCI.18-24-10464.1998   PMID:9852584

Sign convention: Δt = t_post - t_pre.
    Δt > 0 (pre fires before post)  →  potentiation (Δw > 0)
    Δt < 0 (post fires before pre)  →  depression  (Δw < 0)

Bi & Poo 1998 figure 7 shows the relative change in EPSC amplitude as a
function of Δt for hippocampal pyramidal pairs in culture. The double-
exponential fit they report is:

    Δw / w₀ = A_+ · exp(-Δt / τ_+)            for Δt > 0
            = -A_- · exp(Δt / τ_-)            for Δt < 0

with the published parameter values used widely in subsequent computational
literature (e.g. Song, Miller, Abbott 2000):

    τ_+ ≈ 16.8 ms,  A_+ ≈ 0.86
    τ_- ≈ 33.7 ms,  A_- ≈ 0.25

These are the values used below. Per CLAUDE.md, no fabricated parameters.

The module exposes both an analytical kernel and a Brian2-based pair-pulse
simulation. Tests in `tests/test_stdp.py` verify that the Brian2 simulation
matches the analytical kernel within numerical tolerance — this satisfies
the Phase 5 audit gate from ARCHITECTURE.md ("the simulated curve must
match the published Bi-Poo curve within numerical tolerance").
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from brian2 import (
    Network,
    SpikeGeneratorGroup,
    Synapses,
    defaultclock,
    ms,
    prefs,
)

prefs.codegen.target = "numpy"

# Bi & Poo 1998 parameters (modern computational fit).
TAU_PLUS_MS = 16.8
TAU_MINUS_MS = 33.7
A_PLUS = 0.86
A_MINUS = 0.25


def stdp_kernel(dt_ms: float) -> float:
    """Analytical STDP weight change for a single pre/post pair.

    Args:
        dt_ms: t_post - t_pre, in milliseconds.

    Returns:
        Relative weight change Δw / w₀.
    """
    if dt_ms == 0.0:
        return 0.0  # by convention; Bi-Poo data has no Δt=0 measurement
    if dt_ms > 0:
        return A_PLUS * float(np.exp(-dt_ms / TAU_PLUS_MS))
    return -A_MINUS * float(np.exp(dt_ms / TAU_MINUS_MS))


def stdp_curve(
    *, dt_min_ms: float = -80.0, dt_max_ms: float = 80.0, points: int = 161
) -> tuple[np.ndarray, np.ndarray]:
    """Sample the analytical kernel on an evenly spaced Δt grid."""
    if points < 3:
        raise ValueError("points must be >= 3")
    if dt_max_ms <= dt_min_ms:
        raise ValueError("dt_max_ms must be > dt_min_ms")
    grid = np.linspace(dt_min_ms, dt_max_ms, points)
    values = np.array([stdp_kernel(float(t)) for t in grid])
    return grid, values


@dataclass(frozen=True, slots=True)
class STDPPairResult:
    """Output of one Brian2 pre/post pair simulation."""

    dt_ms: float
    delta_w: float       # observed weight change from Brian2 simulation
    kernel_dw: float     # analytical kernel value at the same Δt
    pre_spike_ms: float
    post_spike_ms: float


def simulate_stdp_pair(dt_ms: float, *, base_time_ms: float = 50.0) -> STDPPairResult:
    """Run a Brian2 single-pair STDP simulation and return Δw.

    Two SpikeGeneratorGroups, one pre-spike at base_time_ms, one post-spike
    at base_time_ms + dt_ms. A Synapses connects them with the standard
    additive trace-based STDP rule using the Bi-Poo parameters above. After
    the pair fires, we read the synaptic weight (initialized at 0) and
    return the change.
    """
    if not np.isfinite(dt_ms):
        raise ValueError("dt_ms must be finite")
    if base_time_ms <= 0:
        raise ValueError("base_time_ms must be > 0")

    pre_t = base_time_ms
    post_t = base_time_ms + dt_ms
    if post_t <= 0:
        # shift the pair forward so both spikes happen at strictly positive times
        shift = abs(min(pre_t, post_t)) + 1.0
        pre_t += shift
        post_t += shift

    defaultclock.dt = 0.1 * ms

    pre_group = SpikeGeneratorGroup(1, indices=np.array([0]), times=[pre_t * ms])
    post_group = SpikeGeneratorGroup(1, indices=np.array([0]), times=[post_t * ms])

    syn = Synapses(
        pre_group,
        post_group,
        model="""
        w : 1
        dapre/dt  = -apre/tau_plus  : 1 (event-driven)
        dapost/dt = -apost/tau_minus : 1 (event-driven)
        """,
        on_pre="""
        apre += A_plus
        w += apost
        """,
        on_post="""
        apost -= A_minus
        w += apre
        """,
        namespace={
            "tau_plus": TAU_PLUS_MS * ms,
            "tau_minus": TAU_MINUS_MS * ms,
            "A_plus": A_PLUS,
            "A_minus": A_MINUS,
        },
    )
    syn.connect(i=0, j=0)
    syn.w = 0.0
    syn.apre = 0.0
    syn.apost = 0.0

    end_ms = max(pre_t, post_t) + max(5 * TAU_MINUS_MS, 5 * TAU_PLUS_MS)
    net = Network(pre_group, post_group, syn)
    net.run(end_ms * ms)

    delta_w = float(syn.w[0])
    return STDPPairResult(
        dt_ms=dt_ms,
        delta_w=delta_w,
        kernel_dw=stdp_kernel(dt_ms),
        pre_spike_ms=pre_t,
        post_spike_ms=post_t,
    )
