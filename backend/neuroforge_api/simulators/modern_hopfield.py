"""Modern (dense) Hopfield network — the bridge from Hopfield 1982 to transformer attention.

Reference (continuous modern Hopfield + attention equivalence):
    Ramsauer H, Schäfl B, Lehner J, Seidl P, Widrich M, Adler T, Gruber L,
    Holzleitner M, Pavlović M, Sandve GK, Greiff V, Kreil D, Kopp M,
    Klambauer G, Brandstetter J, Hochreiter S. Hopfield Networks is All You
    Need. ICLR 2021. arXiv:2008.02217. doi:10.48550/arXiv.2008.02217

Reference (dense associative memory, polynomial energy):
    Krotov D, Hopfield JJ. Dense Associative Memory for Pattern Recognition.
    NeurIPS 2016. arXiv:1606.01164. doi:10.48550/arXiv.1606.01164

Reference (exponential storage capacity proof):
    Demircigil M, Heusel J, Löwe M, Upgang S, Vermet F. On a Model of
    Associative Memory with Huge Storage Capacity. J Stat Phys.
    2017;168(2):288-299. doi:10.1007/s10955-017-1806-y

Stored patterns X ∈ R^{d×N}  (N patterns, each d-dimensional), query ξ ∈ R^d.

Energy (Ramsauer 2021 eq. 2):
    E(ξ) = -lse(β, Xᵀξ) + ½ ξᵀξ + β⁻¹ log N + ½ M²        M = max_i ‖x_i‖
    lse(β, z) = β⁻¹ log Σ_i exp(β z_i)

Update rule (Ramsauer 2021 eq. 3 — concave-convex procedure on E):
    ξ_new = X · softmax(β · Xᵀ ξ)

Attention equivalence (Ramsauer 2021 §3, "Hopfield update rule is attention"):
    with query Q = ξᵀ, keys K = Xᵀ, values V = Xᵀ and β = 1/√d_k,
    ξ_newᵀ = softmax(β Q Kᵀ) V   — exactly Vaswani et al. 2017 scaled dot-product attention.

Capacity:
    classic Hopfield (Amit-Gutfreund-Sompolinsky 1987): N_max ≈ 0.138 · d
    modern Hopfield  (Demircigil 2017, exp energy):      N_max ≈ 2^{d/2}   (exponential in d)

Everything below is that math and nothing else. The capacity sweep is an
empirical measurement on random bipolar patterns — it is *evidence for*, not
a restatement of, the theorems above.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import logsumexp, softmax

from neuroforge_api.simulators.hopfield import hebbian_storage

CLASSIC_CRITICAL_ALPHA = 0.138  # Amit-Gutfreund-Sompolinsky 1987


def modern_update(X: np.ndarray, xi: np.ndarray, beta: float) -> np.ndarray:
    """One Ramsauer update:  ξ_new = X softmax(β Xᵀ ξ).

    Args:
        X: (d, N) stored patterns as columns.
        xi: (d,) query state.
        beta: inverse temperature β > 0.
    """
    if beta <= 0:
        raise ValueError("beta must be > 0")
    if X.ndim != 2 or xi.ndim != 1 or X.shape[0] != xi.shape[0]:
        raise ValueError("X must be (d, N) and xi must be (d,)")
    p = softmax(beta * (X.T @ xi))  # (N,)
    return X @ p


def modern_energy(X: np.ndarray, xi: np.ndarray, beta: float) -> float:
    """Ramsauer 2021 eq. 2 energy."""
    n_patterns = X.shape[1]
    lse = logsumexp(beta * (X.T @ xi)) / beta
    m_sq = float(np.max(np.sum(X * X, axis=0)))
    return float(-lse + 0.5 * float(xi @ xi) + np.log(n_patterns) / beta + 0.5 * m_sq)


def attention(Q: np.ndarray, K: np.ndarray, V: np.ndarray, beta: float) -> np.ndarray:
    """Scaled dot-product attention  softmax(β Q Kᵀ) V  (Vaswani 2017 with β = 1/√d_k)."""
    scores = beta * (Q @ K.T)  # (n_q, N)
    return softmax(scores, axis=-1) @ V


def cosine_overlap(a: np.ndarray, b: np.ndarray) -> float:
    """cos∠(a, b). For bipolar vectors this equals the classic Hopfield overlap (1/N) a·b."""
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(a @ b / (na * nb))


def _random_bipolar_patterns(rng: np.random.Generator, n_patterns: int, d: int) -> np.ndarray:
    # Same call as simulators/hopfield.py so the classic and modern nets can
    # be handed IDENTICAL pattern sets for a like-for-like comparison.
    return rng.choice([-1, 1], size=(n_patterns, d)).astype(np.int8)


def _corrupt(rng: np.random.Generator, target: np.ndarray, fraction: float) -> np.ndarray:
    s = target.astype(np.float64).copy()
    n_flips = int(round(fraction * target.size))
    if n_flips > 0:
        idx = rng.choice(target.size, size=n_flips, replace=False)
        s[idx] *= -1
    return s


def _classic_recall(W: np.ndarray, s0: np.ndarray, rng: np.random.Generator, sweeps: int) -> np.ndarray:
    """Asynchronous sign-update recall (identical rule to simulators/hopfield.py)."""
    s = s0.astype(np.int64).copy()
    d = s.size
    for _ in range(sweeps):
        for i in rng.permutation(d):
            s[i] = 1 if float(W[i] @ s) >= 0 else -1
    return s


@dataclass(frozen=True, slots=True)
class ModernHopfieldRun:
    d: int
    n_patterns: int
    alpha: float
    beta: float
    target_index: int
    target: np.ndarray                # (d,)
    corrupted: np.ndarray             # (d,)
    modern_states: np.ndarray         # (T+1, d) continuous
    modern_energies: np.ndarray       # (T+1,)
    modern_overlaps: np.ndarray       # (T+1,) cosine with target
    modern_attention_weights: np.ndarray  # (N,) softmax weights of the FIRST update — the "attention" row
    classic_final: np.ndarray         # (d,)
    classic_overlap: float
    attention_max_abs_diff: float     # |modern_update − attention(Q=ξ,K=V=X)|  — should be ~1e-12


def simulate_modern_hopfield(
    *,
    d: int = 64,
    n_patterns: int = 64,
    corruption_fraction: float = 0.2,
    beta: float | None = None,
    n_updates: int = 3,
    classic_sweeps: int = 6,
    target_index: int = 0,
    seed: int = 42,
) -> ModernHopfieldRun:
    """Store N random bipolar patterns in d dims; recall one from a corrupted query
    with BOTH the classic 1982 net and the modern 2021 net on the same patterns.

    Args:
        beta: inverse temperature. Default 1.0. Transformers use β = 1/√d_k on
            *learned* projections (Vaswani 2017; Ramsauer 2021 §3); on raw
            bipolar patterns that low β averages many patterns into a
            metastable blend once N ≳ d — try it and watch retrieval fail.
            Ramsauer 2021 Theorem 4: larger β → single-pattern fixed points.
    """
    if d < 4:
        raise ValueError("d must be >= 4")
    if n_patterns < 1:
        raise ValueError("n_patterns must be >= 1")
    if not 0.0 <= corruption_fraction <= 1.0:
        raise ValueError("corruption_fraction must be in [0, 1]")
    if n_updates < 1:
        raise ValueError("n_updates must be >= 1")
    if not 0 <= target_index < n_patterns:
        raise ValueError(f"target_index must be in [0, {n_patterns - 1}]")
    b = float(beta) if beta is not None else 1.0
    if b <= 0:
        raise ValueError("beta must be > 0")

    rng = np.random.default_rng(seed)
    patterns = _random_bipolar_patterns(rng, n_patterns, d)  # (N, d)
    X = patterns.T.astype(np.float64)  # (d, N)
    target = patterns[target_index].astype(np.float64)
    corrupted = _corrupt(rng, target, corruption_fraction)

    # --- modern ---
    xi = corrupted.copy()
    states = [xi.copy()]
    energies = [modern_energy(X, xi, b)]
    overlaps = [cosine_overlap(xi, target)]
    first_weights = softmax(b * (X.T @ xi))
    att_diff = float(np.max(np.abs(modern_update(X, xi, b) - attention(xi[None, :], X.T, X.T, b)[0])))
    for _ in range(n_updates):
        xi = modern_update(X, xi, b)
        states.append(xi.copy())
        energies.append(modern_energy(X, xi, b))
        overlaps.append(cosine_overlap(xi, target))

    # --- classic, same patterns ---
    W = hebbian_storage(patterns)
    classic_final = _classic_recall(W, corrupted, rng, classic_sweeps)

    return ModernHopfieldRun(
        d=d,
        n_patterns=n_patterns,
        alpha=n_patterns / d,
        beta=b,
        target_index=target_index,
        target=target,
        corrupted=corrupted,
        modern_states=np.stack(states),
        modern_energies=np.asarray(energies),
        modern_overlaps=np.asarray(overlaps),
        modern_attention_weights=first_weights,
        classic_final=classic_final.astype(np.float64),
        classic_overlap=cosine_overlap(classic_final.astype(np.float64), target),
        attention_max_abs_diff=att_diff,
    )


@dataclass(frozen=True, slots=True)
class CapacitySweep:
    d: int
    alphas: np.ndarray            # load α = N/d
    n_patterns: np.ndarray        # N per α
    classic_success: np.ndarray   # fraction of trials with cos overlap > threshold
    modern_success: np.ndarray
    n_trials: int
    threshold: float
    corruption_fraction: float
    beta: float


def capacity_sweep(
    *,
    d: int = 64,
    alphas: tuple[float, ...] = (0.05, 0.1, 0.138, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0),
    n_trials: int = 8,
    corruption_fraction: float = 0.2,
    beta: float | None = None,
    threshold: float = 0.95,
    seed: int = 7,
) -> CapacitySweep:
    """Empirical retrieval success vs load α = N/d for classic and modern nets.

    Expectation from theory: classic collapses past α ≈ 0.138; modern keeps
    retrieving far beyond α = 1 (capacity exponential in d).
    """
    if d < 4 or n_trials < 1:
        raise ValueError("d >= 4 and n_trials >= 1 required")
    b = float(beta) if beta is not None else 1.0
    rng = np.random.default_rng(seed)
    a_arr = np.asarray(alphas, dtype=np.float64)
    n_arr = np.maximum(1, np.round(a_arr * d)).astype(int)
    classic_hits = np.zeros(len(a_arr))
    modern_hits = np.zeros(len(a_arr))
    for k, n in enumerate(n_arr):
        for _ in range(n_trials):
            patterns = _random_bipolar_patterns(rng, int(n), d)
            X = patterns.T.astype(np.float64)
            t_idx = int(rng.integers(0, n))
            target = patterns[t_idx].astype(np.float64)
            corrupted = _corrupt(rng, target, corruption_fraction)
            # modern: 3 updates
            xi = corrupted.copy()
            for _ in range(3):
                xi = modern_update(X, xi, b)
            if cosine_overlap(xi, target) > threshold:
                modern_hits[k] += 1
            # classic: 6 sweeps
            W = hebbian_storage(patterns)
            s = _classic_recall(W, corrupted, rng, 6)
            if cosine_overlap(s.astype(np.float64), target) > threshold:
                classic_hits[k] += 1
    return CapacitySweep(
        d=d,
        alphas=a_arr,
        n_patterns=n_arr,
        classic_success=classic_hits / n_trials,
        modern_success=modern_hits / n_trials,
        n_trials=n_trials,
        threshold=threshold,
        corruption_fraction=corruption_fraction,
        beta=b,
    )
