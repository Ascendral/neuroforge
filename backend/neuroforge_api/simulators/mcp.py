"""McCulloch-Pitts 1943 — first formal model of a neuron.

Reference (foundational):
    McCulloch WS, Pitts W. A logical calculus of the ideas immanent in
    nervous activity. Bull Math Biophys. 1943;5(4):115-133.
    doi:10.1007/BF02478259

Reference (XOR impossibility for single-layer):
    Minsky M, Papert S. Perceptrons: An Introduction to Computational
    Geometry. MIT Press, 1969. (Established that linearly inseparable
    functions like XOR cannot be computed by a single threshold neuron.)

Reference (multi-layer escape):
    Rumelhart DE, Hinton GE, Williams RJ. Learning representations by
    back-propagating errors. Nature. 1986;323(6088):533-536.
    doi:10.1038/323533a0

The M-P neuron:
    y = 1   if  Σ_i w_i · x_i  ≥  θ
    y = 0   otherwise

Inputs x_i ∈ {0, 1}. The original 1943 formulation used binary weights and
introduced inhibitory inputs that absolutely block firing; we use the modern
real-valued threshold-logic neuron, which subsumes the 1943 form and is the
direct predecessor of the perceptron (Rosenblatt 1958).

Failure mode shown:
    A single threshold neuron computes only linearly separable Boolean
    functions of its inputs. XOR is the canonical counterexample. This
    module includes a brute-force integer-weight search confirming there
    is no single-neuron M-P solution to XOR — anti-theater proof of
    the Minsky-Papert 1969 result rather than a hand-waved citation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def mp_neuron(weights: np.ndarray, threshold: float, inputs: np.ndarray) -> int:
    """Compute the M-P neuron output for one input vector.

    Args:
        weights: shape (N,)
        threshold: θ
        inputs: shape (N,), each entry in {0, 1}

    Returns:
        1 if Σ w_i x_i ≥ θ, else 0.
    """
    if weights.shape != inputs.shape:
        raise ValueError(f"weights {weights.shape} and inputs {inputs.shape} must match")
    return int(float(np.dot(weights, inputs)) >= threshold)


def truth_table(n_inputs: int) -> np.ndarray:
    """All 2^n binary input combinations, shape (2^n, n)."""
    return np.array([[(i >> b) & 1 for b in range(n_inputs)] for i in range(2**n_inputs)])


@dataclass(frozen=True, slots=True)
class GateSpec:
    name: str
    description: str
    n_inputs: int
    weights: tuple[float, ...]
    threshold: float
    expected: tuple[int, ...]


# Hand-derived weight/threshold values that compute each Boolean function.
# These are not "looks right" demos — they are mathematically correct M-P
# realizations of the listed truth tables. Tests verify truth-table match.
GATES: dict[str, GateSpec] = {
    "AND": GateSpec(
        name="AND",
        description="A ∧ B  (output 1 iff both inputs are 1)",
        n_inputs=2,
        weights=(1.0, 1.0),
        threshold=2.0,
        expected=(0, 0, 0, 1),
    ),
    "OR": GateSpec(
        name="OR",
        description="A ∨ B  (output 1 iff at least one input is 1)",
        n_inputs=2,
        weights=(1.0, 1.0),
        threshold=1.0,
        expected=(0, 1, 1, 1),
    ),
    "NOT": GateSpec(
        name="NOT",
        description="¬A    (output 1 iff input is 0)",
        n_inputs=1,
        weights=(-1.0,),
        threshold=0.0,
        expected=(1, 0),
    ),
    "NAND": GateSpec(
        name="NAND",
        description="¬(A ∧ B)",
        n_inputs=2,
        weights=(-1.0, -1.0),
        threshold=-1.0,
        expected=(1, 1, 1, 0),
    ),
    "NOR": GateSpec(
        name="NOR",
        description="¬(A ∨ B)",
        n_inputs=2,
        weights=(-1.0, -1.0),
        threshold=0.0,
        expected=(1, 0, 0, 0),
    ),
}


XOR_TARGET: tuple[int, ...] = (0, 1, 1, 0)


@dataclass(frozen=True, slots=True)
class GateResult:
    name: str
    description: str
    n_inputs: int
    weights: tuple[float, ...]
    threshold: float
    inputs_table: list[list[int]]
    expected: tuple[int, ...]
    produced: tuple[int, ...]
    passes: bool


def evaluate_gate(name: str) -> GateResult:
    """Run the named gate's truth table through its M-P neuron."""
    if name not in GATES:
        raise ValueError(f"unknown gate '{name}'; choices: {sorted(GATES)}")
    spec = GATES[name]
    table = truth_table(spec.n_inputs)
    weights = np.array(spec.weights, dtype=np.float64)
    produced = tuple(mp_neuron(weights, spec.threshold, row) for row in table)
    passes = produced == spec.expected
    return GateResult(
        name=spec.name,
        description=spec.description,
        n_inputs=spec.n_inputs,
        weights=spec.weights,
        threshold=spec.threshold,
        inputs_table=table.astype(int).tolist(),
        expected=spec.expected,
        produced=produced,
        passes=passes,
    )


@dataclass(frozen=True, slots=True)
class XorImpossibilityProof:
    target: tuple[int, ...]
    weight_range: tuple[int, int]
    threshold_range: tuple[int, int]
    weight_step: float
    threshold_step: float
    combinations_tried: int
    best_match_correct: int
    best_weights: tuple[float, ...] | None
    best_threshold: float | None
    no_solution: bool


def search_xor_single_layer(
    *,
    weight_range: tuple[int, int] = (-3, 3),
    threshold_range: tuple[int, int] = (-3, 3),
    step: float = 0.5,
) -> XorImpossibilityProof:
    """Brute-force search for any single M-P neuron that computes XOR.

    XOR is linearly inseparable; per Minsky & Papert 1969 no single threshold
    neuron exists. This function exhaustively searches integer-spaced
    (w1, w2, θ) triples in the requested cube and confirms none of them
    achieves a perfect match. Returns the best partial-match score (≤ 3 / 4).
    """
    table = truth_table(2)
    target = np.array(XOR_TARGET)
    weights_grid = np.arange(weight_range[0], weight_range[1] + step / 2, step)
    thresholds_grid = np.arange(threshold_range[0], threshold_range[1] + step / 2, step)

    best_correct = -1
    best_w: tuple[float, float] | None = None
    best_t: float | None = None
    n_tried = 0

    for w1 in weights_grid:
        for w2 in weights_grid:
            for t in thresholds_grid:
                n_tried += 1
                produced = np.array(
                    [mp_neuron(np.array([w1, w2]), float(t), row) for row in table]
                )
                correct = int((produced == target).sum())
                if correct > best_correct:
                    best_correct = correct
                    best_w = (float(w1), float(w2))
                    best_t = float(t)
                    if correct == 4:
                        # Found one — would falsify Minsky-Papert. Bail.
                        return XorImpossibilityProof(
                            target=XOR_TARGET,
                            weight_range=weight_range,
                            threshold_range=threshold_range,
                            weight_step=step,
                            threshold_step=step,
                            combinations_tried=n_tried,
                            best_match_correct=4,
                            best_weights=best_w,
                            best_threshold=best_t,
                            no_solution=False,
                        )

    return XorImpossibilityProof(
        target=XOR_TARGET,
        weight_range=weight_range,
        threshold_range=threshold_range,
        weight_step=step,
        threshold_step=step,
        combinations_tried=n_tried,
        best_match_correct=best_correct,
        best_weights=best_w,
        best_threshold=best_t,
        no_solution=best_correct < 4,
    )
