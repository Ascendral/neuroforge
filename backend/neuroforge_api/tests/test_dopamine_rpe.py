"""Dopamine RPE tests — the three panels of Schultz, Dayan & Montague 1997 Fig. 1.

  1. unpredicted reward → positive δ AT the reward, nothing at the (uninformative) cue
  2. predicted reward   → positive δ AT the cue, ≈0 at the reward
  3. omitted reward     → negative δ AT the expected reward time
  + learning curve: δ(reward) decays, δ(cue) grows across training
"""

from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from neuroforge_api.main import app
from neuroforge_api.simulators.dopamine_rpe import simulate_dopamine_rpe


def _run():
    return simulate_dopamine_rpe(n_steps=30, cue_step=5, reward_step=20, n_training_trials=200)


def test_unpredicted_reward_burst_at_reward_only():
    r = _run()
    assert r.delta_unpredicted[r.reward_step] == 1.0
    assert r.delta_unpredicted[r.cue_step] == 0.0
    off = np.delete(r.delta_unpredicted, [r.reward_step])
    assert np.all(off == 0.0)


def test_predicted_reward_transfers_to_cue():
    r = _run()
    assert r.delta_predicted[r.cue_step] > 0.5
    assert abs(r.delta_predicted[r.reward_step]) < 0.05
    off = np.delete(r.delta_predicted, [r.cue_step, r.reward_step])
    assert np.max(np.abs(off)) < 0.1


def test_omitted_reward_dip():
    r = _run()
    assert r.delta_omitted[r.reward_step] < -0.9
    assert r.delta_omitted[r.cue_step] > 0.5  # cue still predicts


def test_learning_curve():
    r = _run()
    assert r.delta_at_reward_per_trial[0] == 1.0
    assert r.delta_at_reward_per_trial[-1] < 0.01
    assert r.delta_at_cue_per_trial[0] == 0.0
    assert r.delta_at_cue_per_trial[-1] > 0.5
    # value ramps from cue toward reward and is ~1 just before reward delivery
    assert r.value_trained[r.reward_step - 1] > 0.95
    assert r.value_trained[r.cue_step - 1] == 0.0


def test_gamma_one_gives_full_transfer():
    r = simulate_dopamine_rpe(gamma=1.0, n_training_trials=300)
    assert abs(r.delta_predicted[r.cue_step] - 1.0) < 0.02


def test_endpoint():
    client = TestClient(app)
    resp = client.post("/api/simulate/dopamine-rpe", json={"n_training_trials": 50})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    n = body["n_steps"]
    assert len(body["times_ms"]) == n == len(body["delta_predicted"]) == len(body["delta_omitted"])
    assert len(body["delta_at_reward_per_trial"]) == 50
    assert "10.1126/science.275.5306.1593" in body["citation"]
    assert "α=" in body["parameter_note"]


def test_bad_request():
    client = TestClient(app)
    resp = client.post("/api/simulate/dopamine-rpe", json={"cue_step": 25, "reward_step": 10})
    assert resp.status_code == 400
