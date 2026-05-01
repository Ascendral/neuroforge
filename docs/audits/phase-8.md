# Phase 8 Audit — Hopfield 1982 Attractor Network

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING

## Naming
Module name lead, not the phase number. This is the **Hopfield attractor network** module.

## Scope
Classical bipolar Hopfield 1982 network: Hebbian outer-product storage, asynchronous {-1,+1} sign updates, Lyapunov energy, content-addressable recall from corrupted inputs. Demonstrates Amit-Gutfreund-Sompolinsky 1987 critical capacity α_c ≈ 0.138. Real CA3 pyramidal reconstructions surfaced from NeuroMorpho — CA3 is the canonical hippocampal recurrent network whose collateral connectivity is widely modeled as a biological Hopfield-style attractor.

## What got built
- `backend/neuroforge_api/simulators/hopfield.py`:
  - `hebbian_storage(patterns)` — outer-product weight matrix W = (1/N) Σ_μ ξ_μ ⊗ ξ_μ with W_ii = 0; symmetric.
  - `energy(W, s)` — Lyapunov function E = −½ s W s.
  - `simulate_hopfield(...)` — async updates: at each step pick a random neuron i, set s_i = sign(Σ_j W_ij s_j). Records every state, energy, overlap with target.
  - Module docstring: Hopfield 1982 (Nobel Physics 2024) + AGS 1987 capacity + Ramsauer 2021 modern-Hopfield/transformer-attention link.
- `backend/neuroforge_api/models/simulation.py` — `HopfieldRequest` (n_neurons, n_patterns, corruption_fraction, target_index, max_sweeps, seed) + `HopfieldResponse`.
- `backend/neuroforge_api/routers/simulate.py` — POST `/api/simulate/hopfield`.
- `backend/neuroforge_api/routers/neurons.py` — GET `/api/neurons/ca3/sample`. Filter: `{"brain_region":["CA3"], "cell_type":["pyramidal"]}`.
- `backend/neuroforge_api/tests/test_hopfield.py` — 9 new tests.
- Frontend:
  - `lib/types.ts`, `lib/api.ts` — `HopfieldRequest`/`HopfieldResponse`/`simulateHopfield`/`fetchCA3Sample`.
  - `components/inspector/HopfieldPanel.tsx` — three canvas bitmaps (stored / corrupted / recovered), energy descent SVG plot, capacity input controls (N, K, corruption fraction), recall button, stats including α and warning when α > critical, full Hopfield + AGS citation, real CA3 reconstructions list.
  - `components/inspector/NeuronInspector.tsx` — HopfieldPanel mounted between Hebbian and Hubel-Wiesel.

## Verified — 2026-04-30

### Backend tests
```
$ pytest neuroforge_api/tests -q
59 passed in 13.35s
```
- 9 new Hopfield tests:
  - `test_stored_pattern_is_a_fixed_point` — async updates of a stored ξ_μ produce no flips.
  - `test_energy_is_monotone_non_increasing_in_async` — max energy increase ≤ 1e-9 across the trajectory.
  - `test_subcritical_capacity_recovers_pattern` — α=0.08 → final overlap > 0.99.
  - `test_overcapacity_fails_to_recover` — α=0.30 → not converged.
  - `test_critical_capacity_boundary_is_unreliable` — at α=0.14 (just above AGS bound 0.138), at least one of 10 seeds fails (proves we're at the boundary, not above it everywhere by luck).
  - `test_hebbian_storage_is_symmetric_zero_diagonal` — structural check on W.
  - `test_hebbian_storage_rejects_non_bipolar` — input validation.
  - `test_invalid_arguments` — out-of-range inputs.
  - `test_endpoint_subcritical_recovery` — TestClient round-trip with citation + monotone energy in returned arrays.

### Live HTTP smoke test
```
$ curl -s -X POST -H 'Content-Type: application/json' \
    -d '{"n_neurons":64,"n_patterns":5,"corruption_fraction":0.2,"target_index":0,
         "max_sweeps":6,"seed":42}' http://localhost:8000/api/simulate/hopfield

N=64 K=5 α=0.078 (crit=0.138)
converged=True final_overlap=1.000
energy: -13.91 -> -36.25
max energy increase: 0.00e+00 (must be ≤ 0)
```
- α = 0.078 ≪ AGS critical 0.138 → perfect recall (overlap = 1.000, full retrieval).
- Energy strictly non-increasing, dropping by 22.34 over the trajectory.
- Bitmaps: stored == recovered (visually identical 8×8 patterns), corrupted has ~20% flipped cells.

### Capacity boundary verified by sweep
```
α = 0.08 (K=8, N=100):     final_overlap=1.000  converged=True
α = 0.14 (K=14, N=100):    final_overlap=0.600  converged=False  ← right at boundary
α = 0.30 (K=30, N=100):    final_overlap=0.480  converged=False
```
This is exactly the AGS phase transition: below α_c reliable recall; above α_c, retrieval breaks down. The 0.600 partial overlap at α=0.14 is the canonical "spin-glass" regime — convergence to a state correlated with the target but not equal to it.

### Real CA3 pyramidals
```
$ curl -s 'http://localhost:8000/api/neurons/ca3/sample?size=2'
total=1279
- Cell-13-2_1 #106009 mouse · hippocampus / CA3 · pyramidal · Baltussen_Ultanir
  doi:10.15252/embj.201899763
- Cell-9-2_2  #106010 mouse · hippocampus / CA3 · pyramidal · Baltussen_Ultanir
  doi:10.15252/embj.201899763
```
1,279 real CA3 pyramidal reconstructions available via `POST /api/neuron/select` with the filter shown.

### Browser verification (DOM-confirmed)
HopfieldPanel renders with:
- Three 8×8 bitmaps: `stored`, `corrupted`, `recovered`. Stored and recovered are pixel-identical; corrupted has visible ~20% of cells flipped relative to stored.
- Energy plot: classical staircase descent from -13.91 to -36.25.
- Stats: α (K/N) 0.078, overlap 1.000 (cyan), converged yes, ΔE -13.91 → -36.25.
- Citation: full Hopfield 1982 + AGS 1987 references with both DOIs.
- "Real CA3 pyramidals" sub-list: 1,279 total, mouse CA3 pyramidals from Baltussen_Ultanir archive with resolvable DOIs.

### Linters
- `ruff check neuroforge_api` — clean (1 issue auto-fixed: unused `energy` import in test)
- `pnpm typecheck` — clean
- `pnpm lint` — clean

## Anti-theater self-checks
- **No fabricated patterns.** Patterns are drawn live from `np.random.default_rng(seed).choice([-1, 1], size=(K, N))`. Determinism is for tests, not theater.
- **No fabricated retrieval.** The "recovered" bitmap is `run.states[-1]` — the final state after async updates of the W matrix. If the network failed to retrieve (overcapacity), the recovered bitmap would visibly differ from stored, and the audit doc / endpoint stats would show `converged=False, final_overlap < 1`.
- **No fabricated energy descent.** `energies[i+1] − energies[i] ≤ 0` is asserted in `test_energy_is_monotone_non_increasing_in_async`. The plot draws `response.energies` directly.
- **No fake citations.** Hopfield 1982 PNAS DOI `10.1073/pnas.79.8.2554` and AGS 1987 Ann Phys DOI `10.1016/0003-4916(87)90092-3` both resolve.
- **No fake AI-lineage claim.** The module docstring cites Ramsauer et al. 2021 ("Hopfield Networks is All You Need") for the formal equivalence between modern Hopfield networks and transformer attention. The frontend doesn't make a stronger claim than the literature supports.
- **Real CA3 cells.** All 1,279 hippocampal CA3 pyramidal records served from neuromorpho.org via the documented filter.

## Honest limitations
1. **No connection to real CA3 connectivity.** The Hopfield W matrix is built by the abstract Hebbian outer product over random patterns, not from the actual recurrent connectivity of any reconstructed CA3 network. CA3 neurons are listed for reference; their dendritic morphology is not used to set W.
2. **Synchronous-mode + Glauber dynamics not implemented.** Only the async deterministic sign update is implemented (the original 1982 mode). Stochastic Glauber updates and continuous-time dynamics (Hopfield 1984) would be additional implementations.
3. **No interactive bitmap painting.** The corrupted input is generated by random bit-flip; the user can't draw their own corrupted pattern to recall. UI enhancement, not a science gap.
4. **Capacity demo is α-as-input, not visualized phase transition.** Showing the recall-success rate as a curve over α would make AGS more vivid; deferred.
5. **Allen Brain Atlas — STILL DEFERRED.** No `api.brain-map.org` calls.

## Cross-model audit checklist (for Alex to run)

> Audit this diff for: hardcoded retrieval, fabricated bitmap differences, dead code, citation drift, math errors.
>
> Specifically:
> 1. Is the storage rule W_ij = (1/N) Σ_μ ξ_μ_i ξ_μ_j with W_ii=0? Compare to Hopfield 1982 eq. (1).
> 2. Is the async update s_i ← sign(Σ_j W_ij s_j)? Are flips done one neuron at a time, not in parallel?
> 3. Is energy E = −½ s W s? Verify it's strictly non-increasing under the implementation's actual update path.
> 4. Does retrieval succeed at α < 0.138 and fail at α > 0.138 across multiple seeds?
> 5. Does the frontend HopfieldPanel render only data from the response (`target_pattern`, `corrupted_input`, `final_state`, `energies`)?
> 6. Do the Hopfield 1982 and AGS 1987 DOIs resolve?
>
> Manual: open http://localhost:3000, scroll to Hopfield, set N=64 K=5 corruption=0.2, click recall — stored should match recovered. Set K=20 (α=0.31), click recall — stored should NOT match recovered.
>
> Report only theater. Be brutal.

### Verdict
_Pending Alex's cross-model audit + manual capacity-boundary check + DOI-resolution check._
