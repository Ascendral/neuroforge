"""Dopamine reward-prediction error — temporal-difference model of VTA/SNc firing.

Reference (the neuroscience):
    Schultz W, Dayan P, Montague PR. A neural substrate of prediction and
    reward. Science. 1997;275(5306):1593-1599. doi:10.1126/science.275.5306.1593
    — midbrain dopamine neurons fire to UNPREDICTED reward, transfer their
    response to a predictive cue after learning, and PAUSE when a predicted
    reward is omitted. The three panels of their Fig. 1.

Reference (the model form used by Schultz 1997):
    Montague PR, Dayan P, Sejnowski TJ. A framework for mesencephalic dopamine
    systems based on predictive Hebbian learning. J Neurosci.
    1996;16(5):1936-1947. doi:10.1523/JNEUROSCI.16-05-01936.1996

Reference (the algorithm):
    Sutton RS. Learning to predict by the methods of temporal differences.
    Mach Learn. 1988;3(1):9-44. doi:10.1007/BF00115009

Reference (phasic burst / pause physiology):
    Schultz W. Predictive reward signal of dopamine neurons. J Neurophysiol.
    1998;80(1):1-27. doi:10.1152/jn.1998.80.1.1

Reference (2020 update — dopamine codes a DISTRIBUTION of expected reward):
    Dabney W, Kurth-Nelson Z, Uchida N, Starkweather CK, Hassabis D, Munos R,
    Botvinick M. A distributional code for value in dopamine-based
    reinforcement learning. Nature. 2020;577(7792):671-675.
    doi:10.1038/s41586-019-1924-6

Model (TD(0) with a complete-serial-compound / tapped-delay-line stimulus,
exactly the representation in Montague 1996 / Schultz 1997):

    x_i(t) = 1  if  t − t_CS == i  else 0          (one feature per delay since the cue)
    V(t)   = w · x(t)
    δ(t)   = r(t) + γ V(t) − V(t−1)                  ← the dopamine signal, stamped at the
                                                      moment the animal arrives in state t
    w     += α · δ(t) · x(t−1)

(Sutton 1988 writes the same error as r_{t+1} + γV(s_{t+1}) − V(s_t); we index it
by arrival time so δ lines up with the cue / reward bins on the plot.)

Numerical constants below (α, γ, bin width, cue/reward times) are OURS for the
demo and are returned in the response so the UI can print them. The paper's
claims that this module reproduces are qualitative: sign and timing of δ in
the three conditions. Nothing here is fitted to spike counts.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class RPEConditions:
    n_steps: int
    bin_ms: float
    cue_step: int
    reward_step: int
    alpha: float
    gamma: float
    n_training_trials: int
    times_ms: np.ndarray
    # δ(t) for the three canonical conditions (Schultz 1997 Fig. 1, top → bottom)
    delta_unpredicted: np.ndarray   # naive animal, reward with no cue history
    delta_predicted: np.ndarray     # after training: cue → reward
    delta_omitted: np.ndarray       # after training: cue, reward withheld
    value_trained: np.ndarray       # V(t) after training
    # learning curve across training trials
    delta_at_reward_per_trial: np.ndarray
    delta_at_cue_per_trial: np.ndarray


def _run_trial(
    w: np.ndarray, *, n_steps: int, cue_step: int, reward_step: int,
    reward: float, alpha: float, gamma: float, learn: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One trial. Returns (δ(t), V(t), updated w). w is mutated only if learn."""
    n_feat = w.size
    x = np.zeros((n_steps, n_feat))
    for t in range(n_steps):
        i = t - cue_step
        if 0 <= i < n_feat:
            x[t, i] = 1.0
    r = np.zeros(n_steps)
    if 0 <= reward_step < n_steps:
        r[reward_step] = reward
    delta = np.zeros(n_steps)
    value = np.zeros(n_steps)
    w_local = w.copy()
    value[0] = float(w_local @ x[0])
    for t in range(1, n_steps):
        v_prev = float(w_local @ x[t - 1])
        v_t = float(w_local @ x[t])
        d = r[t] + gamma * v_t - v_prev
        delta[t] = d
        value[t] = v_t
        if learn:
            w_local += alpha * d * x[t - 1]
    if learn:
        w[:] = w_local
    return delta, value, w


def simulate_dopamine_rpe(
    *,
    n_steps: int = 30,
    bin_ms: float = 100.0,
    cue_step: int = 5,
    reward_step: int = 20,
    reward: float = 1.0,
    alpha: float = 0.1,
    gamma: float = 0.98,
    n_training_trials: int = 200,
) -> RPEConditions:
    """Reproduce the three Schultz-Dayan-Montague 1997 conditions with TD(0)."""
    if n_steps < 4:
        raise ValueError("n_steps must be >= 4")
    if not 0 <= cue_step < reward_step < n_steps:
        raise ValueError("need 0 <= cue_step < reward_step < n_steps")
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")
    if not 0.0 < gamma <= 1.0:
        raise ValueError("gamma must be in (0, 1]")
    if n_training_trials < 1:
        raise ValueError("n_training_trials must be >= 1")
    if bin_ms <= 0:
        raise ValueError("bin_ms must be > 0")

    n_feat = n_steps  # tapped delay line long enough to span the trial
    kw = dict(n_steps=n_steps, cue_step=cue_step, reward_step=reward_step,
              reward=reward, alpha=alpha, gamma=gamma)

    # Condition 1 — unpredicted reward: naive weights, no learning yet.
    w = np.zeros(n_feat)
    delta_unpredicted, _, _ = _run_trial(w, learn=False, **kw)

    # Training: cue reliably followed by reward.
    d_reward_curve = np.zeros(n_training_trials)
    d_cue_curve = np.zeros(n_training_trials)
    for k in range(n_training_trials):
        delta, _, w = _run_trial(w, learn=True, **kw)
        d_reward_curve[k] = delta[reward_step]
        d_cue_curve[k] = delta[cue_step]

    # Condition 2 — predicted reward (probe, no learning).
    delta_predicted, value_trained, _ = _run_trial(w, learn=False, **kw)

    # Condition 3 — predicted reward OMITTED (probe, no learning).
    delta_omitted, _, _ = _run_trial(w, learn=False, **{**kw, "reward": 0.0})

    times = np.arange(n_steps) * bin_ms
    return RPEConditions(
        n_steps=n_steps,
        bin_ms=bin_ms,
        cue_step=cue_step,
        reward_step=reward_step,
        alpha=alpha,
        gamma=gamma,
        n_training_trials=n_training_trials,
        times_ms=times,
        delta_unpredicted=delta_unpredicted,
        delta_predicted=delta_predicted,
        delta_omitted=delta_omitted,
        value_trained=value_trained,
        delta_at_reward_per_trial=d_reward_curve,
        delta_at_cue_per_trial=d_cue_curve,
    )
