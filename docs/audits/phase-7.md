# Phase 7 Audit — Hebbian + LTP (Hebb 1949 · Bliss-Lømo 1973 · Oja 1982)

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING

## Naming
The audit doc lead with the module name (Hebbian + LTP) and not just "Phase 7". The original NEUROFORGE plan uses different numbering across its examples; what matters is the module delivered, not where it falls in a sequence. This is the **Hebbian / LTP module** by content.

## Scope
Pure Hebb 1949 vs Oja 1982 unsupervised learning rule on 2D correlated inputs. Backend NumPy simulator + endpoint + tests + frontend panel showing the canonical runaway-vs-stable dichotomy. Real hippocampal pyramidal neurons (the cells in which Bliss & Lømo 1973 first demonstrated LTP) listed via NeuroMorpho.

## What got built
- `backend/neuroforge_api/simulators/hebbian.py`:
  - `simulate_hebbian(rule, n_iterations, learning_rate, correlation, input_dim, seed, record_every_n)` — drives a single neuron with i.i.d. Gaussian inputs of specified covariance, applies the rule's update for each pattern, records ‖w‖ and the angle to the true principal eigenvector of the covariance matrix. Returns an `HebbianTrace`.
  - **Pure Hebb update:** Δw = η · y · x where y = w·x.
  - **Oja update:** Δw = η · y · (x − y · w).
  - Module docstring traces every formula to Hebb 1949, Bliss & Lømo 1973, Oja 1982.
- `backend/neuroforge_api/models/simulation.py` — `HebbianRequest` (n_iterations, learning_rate, correlation, input_dim, seed) + `HebbianResponse` (iterations, hebb_norm, hebb_angle_deg, oja_norm, oja_angle_deg, principal_direction, final_hebb_weight, final_oja_weight, citation).
- `backend/neuroforge_api/routers/simulate.py` — POST `/api/simulate/hebbian` runs both rules with the same RNG seed and returns aligned trajectories.
- `backend/neuroforge_api/routers/neurons.py` — GET `/api/neurons/hippocampus/sample?size=N`. Filter: `{"brain_region": ["hippocampus"], "cell_type": ["pyramidal"]}`.
- Frontend:
  - `lib/types.ts`, `lib/api.ts` — `HebbianRequest`/`HebbianResponse`/`fetchHippocampalSample`/`simulateHebbian`.
  - `components/inspector/HebbianPanel.tsx` — log-scale weight-norm plot (red Hebb, blue Oja, dashed line at ‖w‖=1), iteration/η inputs, "run learning" button, stats (final ‖w‖, final angle, principal direction), full Hebb-Bliss-Oja citation, real hippocampal pyramidal reconstructions list.
  - `components/inspector/NeuronInspector.tsx` — HebbianPanel mounted between STDP and Hubel-Wiesel.

## Verified — 2026-04-30

### Backend tests
```
$ pytest neuroforge_api/tests -q
50 passed in 13.50s
```
- 7 new Hebbian tests (`test_hebbian.py`):
  - `test_pure_hebb_runs_away` — final ‖w‖ > 1000× initial under correlated input.
  - `test_oja_stabilizes_norm_at_one` — final ‖w‖ within 5% of 1.
  - `test_both_rules_align_to_principal_component` — final angle to true PC < 5°.
  - `test_oja_robustness_across_seeds` — ‖w‖ converges to 1 regardless of seed.
  - `test_uncorrelated_input_no_principal_direction_preference` — Oja still stabilizes when correlation = 0.
  - `test_invalid_arguments_rejected` — bogus rule name, n_iterations=0, η<0, |correlation|≥1.
  - `test_hebbian_endpoint_runs_both_rules` — TestClient round-trip with citation + magnitude separation between rules.

### Live HTTP smoke test
```
$ curl -s -X POST -H 'Content-Type: application/json' \
    -d '{"n_iterations":2000,"learning_rate":0.005,"correlation":0.8}' \
    http://localhost:8000/api/simulate/hebbian

iters_recorded=200
final_hebb_norm=3.64e+06
final_oja_norm=1.0002
final_hebb_angle=0.92°
final_oja_angle=0.93°
principal=[0.7071067811865475, 0.7071067811865475]
final_hebb_w=[-2532988.6, -2615393.4]
final_oja_w=[-0.6957, -0.7186]
```
- Pure Hebb blew up by 7 orders of magnitude — canonical runaway behavior.
- Oja stabilized at ‖w‖ = 1.000 to within 0.02% — canonical PCA fixed point.
- Both rotated to within ~1° of the true principal eigenvector (1,1)/√2 — canonical eigenvector tracking.
- Hebb's final `w` direction = `[-0.696, -0.719]` (after dividing by norm) ≈ −1·principal eigenvector. Sign-symmetric per the rule's invariance.

### Real hippocampal pyramidals via NeuroMorpho
```
$ curl -s 'http://localhost:8000/api/neurons/hippocampus/sample?size=3'

total_matching=18421
- n419  #100   rat · hippocampus / CA1 · pyramidal, principal cell · Turner archive
- n420  #101   rat · hippocampus / CA1 · pyramidal, principal cell · Turner archive
- n10fts #1013 rat · hippocampus · pyramidal, principal cell · Ascoli archive
```
Filter: `{"brain_region": ["hippocampus"], "cell_type": ["pyramidal"]}`. These are the canonical Bliss-Lømo cell type — pyramidal neurons of CA1 / CA3 / dentate where LTP was first observed.

### Browser verification (DOM-confirmed)
HebbianPanel renders in the inspector with:
- Log-scale weight-norm plot, red curve diverging upward (pure Hebb), blue curve flattening at the dashed `‖w‖=1` reference (Oja).
- Stats panel: `final ‖w‖ (Hebb)=3.64e+6` in accent red, `final ‖w‖ (Oja)=1.0002` in blue, both angles ≈ 0.92°, PC direction `[0.707, 0.707]`.
- Full citation including Hebb 1949 + Bliss-Lømo 1973 (with DOI `10.1113/jphysiol.1973.sp010273`) + Oja 1982 (DOI `10.1007/BF00275687`).
- "Real hippocampal pyramidals" subsection: 18,421 total, 5 listed with real DOIs (`10.1002/(SICI)1096-9861(19980216)391:3<335::AID-CNE4>3.0.CO;2-2`, `10.2307/4134575`).

### Linters
- `ruff check neuroforge_api` — clean
- `pnpm typecheck` — clean
- `pnpm lint` — clean

## Anti-theater self-checks
- **No fabricated divergence.** Pure Hebb's runaway is a real numerical computation: `simulate_hebbian(rule="hebb", n_iterations=2000, …)` produced ‖w‖ = 3.64×10⁶ from an initial ‖w‖ ≈ 0.3. The test `test_pure_hebb_runs_away` asserts a 1000× ratio, but the actual ratio observed in the run is ~10 million.
- **No fabricated stability.** Oja's `‖w‖ → 1` comes from the rule, not a hard normalization step. The simulator is `_step("oja", w, x, eta) = w + eta * y * (x - y*w)` — no clamping, no projection.
- **No fabricated principal direction.** The "PC direction" returned to the frontend is the largest-eigenvalue eigenvector of the *true* input covariance matrix (computed via `np.linalg.eigh(cov)`), not the learned weight. The angle reported is angle between learned `w` and that true PC.
- **No fake citations.** Each DOI in `HEBBIAN_CITATION` resolves to the actual published paper (Hebb's book has no DOI; the citation is the standard book reference).
- **No fake hippocampal data.** All 5 listed neurons come from neuromorpho.org via `POST /api/neuron/select`; their region/type tags are the upstream values.
- **Filter is the canonical LTP cell type.** Bliss & Lømo 1973 worked in dentate gyrus of rabbit hippocampus; the search filter `brain_region="hippocampus" AND cell_type="pyramidal"` matches the pyramidal cells of CA1 / CA3 where most subsequent LTP work has been done. Honest scope: we surface "any hippocampal pyramidal", not specifically Bliss-Lømo's exact rabbit-dentate preparation.

## Honest limitations
1. **Rate-based, not spiking.** Hebbian learning here is on continuous activations (y = w·x). A spiking implementation in Brian2 would convert to STDP-like timing rules (which we already cover in Phase 5). The two formulations are complementary.
2. **No connection from learned `w` to a real reconstruction.** The simulator runs in an abstract input space; we don't yet take a real hippocampal pyramidal SWC and apply Hebbian dynamics on its actual synapses. That would require modeling spatially-distributed synapses on the dendritic tree — a significant compartmental-modeling effort.
3. **Allen Brain Atlas — STILL DEFERRED.** All hippocampal data here goes through NeuroMorpho. No `api.brain-map.org` calls, no `allensdk` import.
4. **No frontend tests.** Continuing the same status as previous module phases.

## Cross-model audit checklist (for Alex to run)

> Audit this diff for: hardcoded fake learning curves, fabricated runaway behavior, dead code paths, citation fabrication, math drift from Hebb / Oja / Bliss-Lømo references.
>
> Specifically:
> 1. Are the update rules in `simulators/hebbian.py` exactly Hebb's `Δw = η y x` and Oja's `Δw = η y (x − y w)`? No clamping, no normalization step?
> 2. Does the simulator generate inputs from a real Cholesky-decomposed correlated Gaussian, or is the trajectory hardcoded?
> 3. Does pure Hebb really diverge under the simulator (run it yourself with seed=42, n=2000, η=0.005, correlation=0.8 — should produce ‖w‖ ~ 10⁶ to 10⁷)?
> 4. Does Oja's rule really converge to ‖w‖ = 1 from any seed?
> 5. Does the frontend HebbianPanel only render data from the response, with no synthetic fallback curve?
> 6. Do all three citation DOIs resolve? (Hebb's book has no DOI; check it's properly attributed as a 1949 Wiley book.)
>
> Manual step: open http://localhost:3000, scroll the inspector to the Hebbian section, click "run learning". Confirm the red curve climbs many decades while the blue curve flattens at ‖w‖=1. Try increasing iterations to 10,000 — Hebb should keep climbing.
>
> Report only theater. Be brutal.

### Verdict
_Pending Alex's cross-model audit + manual divergence check + DOI-resolution check._
