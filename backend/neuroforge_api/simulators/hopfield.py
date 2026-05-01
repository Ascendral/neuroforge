"""Hopfield 1982 attractor network — content-addressable memory.

Reference (foundational):
    Hopfield JJ. Neural networks and physical systems with emergent
    collective computational abilities. Proc Natl Acad Sci USA.
    1982 Apr;79(8):2554-2558.
    doi:10.1073/pnas.79.8.2554   PMID:6953413   Nobel Prize Physics 2024.

Reference (capacity bound):
    Amit DJ, Gutfreund H, Sompolinsky H. Statistical mechanics of neural
    networks near saturation. Ann Phys. 1987;173(1):30-67.
    doi:10.1016/0003-4916(87)90092-3
    (Established critical capacity α_c ≈ 0.138 for the standard Hopfield
    network, i.e. K_max ≈ 0.138 · N stored patterns for reliable recall.)

Reference (modern AI lineage):
    Ramsauer H, et al. Hopfield Networks is All You Need. ICLR 2021.
    arXiv:2008.02217 — establishes formal equivalence between modern
    continuous Hopfield networks and the attention mechanism in transformers.

Sign convention: bipolar units s_i ∈ {-1, +1}.

Storage rule (Hebbian outer product):
    W_ij = (1/N) Σ_μ ξ_μ_i · ξ_μ_j      (i ≠ j)
    W_ii = 0

Asynchronous update (one neuron i at random per step):
    s_i ← sign( Σ_j W_ij · s_j )
    s_i unchanged if the field is exactly zero (rare for real patterns)

Energy (Lyapunov function — monotonically non-increasing under async update):
    E(s) = -½ Σ_ij W_ij · s_i · s_j

Stored patterns are local minima of E. Retrieval = relaxation toward the
nearest minimum from a corrupted initial state.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _sign_bipolar(x: float | np.ndarray) -> np.ndarray | int:
    """sign(x) but mapping 0 → +1 (no zero-state in bipolar Hopfield)."""
    return np.where(np.asarray(x) >= 0, 1, -1)


def hebbian_storage(patterns: np.ndarray) -> np.ndarray:
    """Build the Hopfield weight matrix from K bipolar patterns.

    Args:
        patterns: shape (K, N), each row in {-1, +1}.

    Returns:
        W: shape (N, N), symmetric, zero diagonal.
    """
    if patterns.ndim != 2:
        raise ValueError("patterns must be 2-D (K, N)")
    if not np.all(np.isin(patterns, (-1, 1))):
        raise ValueError("patterns must be bipolar {-1, +1}")
    K, N = patterns.shape
    W = (patterns.T @ patterns).astype(np.float64) / N
    np.fill_diagonal(W, 0.0)
    return W


def energy(W: np.ndarray, s: np.ndarray) -> float:
    """Hopfield energy for state s under weight matrix W."""
    return float(-0.5 * s @ W @ s)


def overlap(s: np.ndarray, pattern: np.ndarray) -> float:
    """Normalized overlap m = (1/N) s · pattern. ∈ [-1, +1]."""
    return float(np.dot(s, pattern) / s.size)


@dataclass(frozen=True, slots=True)
class HopfieldRun:
    n_neurons: int
    n_patterns: int
    target_index: int
    patterns: np.ndarray            # (K, N)
    corrupted_input: np.ndarray     # (N,)
    states: np.ndarray              # (T+1, N) — initial + per update
    energies: np.ndarray            # (T+1,)
    overlaps_with_target: np.ndarray  # (T+1,)
    update_neurons: np.ndarray      # (T,) which neuron flipped each step (-1 if no change)
    final_overlap: float
    converged: bool
    target_capacity_alpha: float    # K / N


def simulate_hopfield(
    *,
    n_neurons: int = 64,
    n_patterns: int = 6,
    corruption_fraction: float = 0.2,
    target_index: int | None = None,
    max_sweeps: int = 10,
    seed: int = 42,
) -> HopfieldRun:
    """Train a Hopfield network on random bipolar patterns and recall one.

    Args:
        n_neurons: N. Number of binary units.
        n_patterns: K. Number of patterns stored. Reliable recall requires
            K / N < ~0.138 (Amit-Gutfreund-Sompolinsky 1987 critical capacity).
        corruption_fraction: fraction of bits to flip in the chosen target
            pattern before relaxation. 0 = exact, 1 = inverted.
        target_index: which stored pattern to corrupt and recall. If None,
            uses pattern 0.
        max_sweeps: number of full-N sweeps of async updates. Each sweep
            randomly orders neurons and applies one update each.
        seed: RNG seed.
    """
    if n_neurons < 4:
        raise ValueError("n_neurons must be >= 4")
    if n_patterns < 1:
        raise ValueError("n_patterns must be >= 1")
    if not 0.0 <= corruption_fraction <= 1.0:
        raise ValueError("corruption_fraction must be in [0, 1]")
    if max_sweeps < 1:
        raise ValueError("max_sweeps must be >= 1")

    rng = np.random.default_rng(seed)
    patterns = rng.choice([-1, 1], size=(n_patterns, n_neurons)).astype(np.int8)
    W = hebbian_storage(patterns)

    idx = 0 if target_index is None else int(target_index)
    if not 0 <= idx < n_patterns:
        raise ValueError(f"target_index must be in [0, {n_patterns - 1}]")
    target = patterns[idx].astype(np.int64)

    s = target.copy()
    n_flips = int(round(corruption_fraction * n_neurons))
    if n_flips > 0:
        flip_idx = rng.choice(n_neurons, size=n_flips, replace=False)
        s[flip_idx] *= -1

    states = [s.copy()]
    energies = [energy(W, s)]
    overlaps = [overlap(s, target)]
    flipped: list[int] = []

    for _ in range(max_sweeps):
        order = rng.permutation(n_neurons)
        for i in order:
            field = float(W[i] @ s)
            new_val = 1 if field >= 0 else -1
            if new_val != s[i]:
                s[i] = new_val
                flipped.append(int(i))
            else:
                flipped.append(-1)
            states.append(s.copy())
            energies.append(energy(W, s))
            overlaps.append(overlap(s, target))

    states_arr = np.stack(states, axis=0)
    energies_arr = np.array(energies, dtype=np.float64)
    overlaps_arr = np.array(overlaps, dtype=np.float64)

    final_overlap = overlaps_arr[-1]
    converged = abs(final_overlap) > 0.95

    return HopfieldRun(
        n_neurons=n_neurons,
        n_patterns=n_patterns,
        target_index=idx,
        patterns=patterns,
        corrupted_input=states_arr[0],
        states=states_arr,
        energies=energies_arr,
        overlaps_with_target=overlaps_arr,
        update_neurons=np.array(flipped, dtype=np.int64),
        final_overlap=final_overlap,
        converged=bool(converged),
        target_capacity_alpha=float(n_patterns / n_neurons),
    )
