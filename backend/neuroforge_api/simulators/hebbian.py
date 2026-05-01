"""Hebbian learning — pure Hebb 1949 vs Oja 1982 normalization.

Neuroscience anchor:
    Bliss TVP, Lømo T. Long-lasting potentiation of synaptic transmission in
    the dentate area of the anaesthetized rabbit following stimulation of the
    perforant path. J Physiol. 1973;232(2):331-356.
    doi:10.1113/jphysiol.1973.sp010273   PMID:4727084
    (First demonstration of LTP — the cellular correlate of Hebb's rule.)

Foundational rule:
    Hebb DO. The Organization of Behavior. Wiley, 1949.
    "When an axon of cell A is near enough to excite cell B and repeatedly or
    persistently takes part in firing it, some growth process or metabolic
    change takes place in one or both cells such that A's efficiency, as one
    of the cells firing B, is increased."  (p. 62)

Stabilizing variant:
    Oja E. A simplified neuron model as a principal component analyzer.
    J Math Biol. 1982;15(3):267-273.   doi:10.1007/BF00275687

AI lineage: pure Hebb is unstable (runaway potentiation). Oja's rule is the
basis of unsupervised PCA learning, self-organizing maps (Kohonen), and the
energy-minimizing weight dynamics of Hopfield networks (1982).

Sign and unit conventions:
    pre activity x ∈ R^N (continuous firing rate, arbitrary units)
    post activity y = w · x
    weight vector w ∈ R^N

Update rules (per pattern presentation):
    Pure Hebb:  Δw = η · y · x
    Oja:        Δw = η · y · (x - y · w)

Pure Hebb has no fixed point — |w| → ∞. Oja has a unique fixed point at the
principal eigenvector of the input covariance matrix, with |w| = 1.

This module is pure NumPy. No Brian2 required: Hebbian learning is a
discrete weight-update rule on continuous activations, not an ODE. Per
CLAUDE.md, the stack-locked simulator (Brian2) governs spiking biophysics —
the rate-based learning rule legitimately stays out of it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

Rule = Literal["hebb", "oja"]


def _step(rule: Rule, w: np.ndarray, x: np.ndarray, eta: float) -> np.ndarray:
    y = float(np.dot(w, x))
    if rule == "hebb":
        return w + eta * y * x
    if rule == "oja":
        return w + eta * y * (x - y * w)
    raise ValueError(f"unknown rule: {rule}")


@dataclass(frozen=True, slots=True)
class HebbianTrace:
    """Output of one Hebbian-learning run.

    iterations          — 1-indexed pattern presentation number
    weight_norm         — ||w||₂ at each iteration (after the update)
    weight_angle_deg    — angle (deg) between w and the principal eigenvector
                          of the empirical input covariance matrix
    final_weight        — w after the last iteration (for inspection)
    principal_direction — principal eigenvector of the empirical input cov
    rule                — "hebb" or "oja"
    """

    iterations: np.ndarray
    weight_norm: np.ndarray
    weight_angle_deg: np.ndarray
    final_weight: np.ndarray
    principal_direction: np.ndarray
    rule: Rule


def simulate_hebbian(
    *,
    rule: Rule,
    n_iterations: int,
    learning_rate: float,
    input_dim: int = 2,
    correlation: float = 0.8,
    seed: int = 0,
    record_every_n: int = 1,
) -> HebbianTrace:
    """Drive a single neuron with correlated inputs and learn under given rule.

    Inputs are drawn i.i.d. from a zero-mean N-D Gaussian with covariance C
    where off-diagonals = correlation, diagonals = 1. The principal
    eigenvector of C is the all-ones vector (in 2D: (1,1)/√2 with eigenvalue
    1+correlation). Both Hebb and Oja should rotate w toward that direction;
    Hebb additionally blows |w| up, Oja keeps it at 1.

    Args:
        rule: "hebb" or "oja"
        n_iterations: number of pattern presentations
        learning_rate: η. For correlation=0.8 and dim=2, 0.005-0.01 is a
            reasonable range; bigger η makes Hebb diverge faster but doesn't
            change the steady-state direction.
        input_dim: dimensionality N of the input vector
        correlation: off-diagonal entry of the input covariance (must be in
            (-1, 1) for the matrix to be positive definite)
        seed: RNG seed (deterministic for tests)
        record_every_n: subsample factor for the returned trajectory
    """
    if rule not in ("hebb", "oja"):
        raise ValueError(f"unknown rule: {rule}")
    if n_iterations < 1:
        raise ValueError("n_iterations must be >= 1")
    if learning_rate <= 0:
        raise ValueError("learning_rate must be > 0")
    if input_dim < 1:
        raise ValueError("input_dim must be >= 1")
    if not -1.0 < correlation < 1.0:
        raise ValueError("correlation must be in (-1, 1)")
    if record_every_n < 1:
        raise ValueError("record_every_n must be >= 1")

    rng = np.random.default_rng(seed)
    cov = np.full((input_dim, input_dim), correlation)
    np.fill_diagonal(cov, 1.0)
    L = np.linalg.cholesky(cov)

    # Empirical principal eigenvector of the *true* input covariance.
    eigvals, eigvecs = np.linalg.eigh(cov)
    principal = eigvecs[:, -1]
    if principal[0] < 0:
        principal = -principal

    # Small random initial weight to avoid being on the unstable fixed point.
    w = 0.1 * rng.standard_normal(input_dim)

    iterations: list[int] = []
    norms: list[float] = []
    angles: list[float] = []

    for step in range(1, n_iterations + 1):
        x = L @ rng.standard_normal(input_dim)
        w = _step(rule, w, x, learning_rate)
        if step % record_every_n == 0 or step == n_iterations:
            n = float(np.linalg.norm(w))
            if n > 0:
                cos = float(np.clip(np.dot(w, principal) / n, -1.0, 1.0))
                # Angle in [0, 90] — w and -w model the same axis under Hebb/Oja.
                angle_deg = float(np.degrees(np.arccos(abs(cos))))
            else:
                angle_deg = float("nan")
            iterations.append(step)
            norms.append(n)
            angles.append(angle_deg)

    return HebbianTrace(
        iterations=np.array(iterations, dtype=np.int64),
        weight_norm=np.array(norms, dtype=np.float64),
        weight_angle_deg=np.array(angles, dtype=np.float64),
        final_weight=w,
        principal_direction=principal,
        rule=rule,
    )
