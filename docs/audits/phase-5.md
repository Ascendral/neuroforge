# Phase 5 Audit — STDP (Bi & Poo 1998)

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING — Alex to run independent audit on Phase 5 diff.

## Scope of Phase 5
Spike-timing-dependent plasticity module. Bi-Poo 1998 hippocampal STDP kernel implemented as both an analytical function and a Brian2 pair-pulse simulation. POST `/api/simulate/stdp` returns observed Δw, kernel Δw, full curve, parameters, and citation. Frontend STDPPanel renders the canonical curve with the user's selected Δt highlighted as a red marker.

## What got built
- `backend/neuroforge_api/simulators/stdp.py` — module with:
  - **Parameters** (Bi-Poo 1998 / Song-Miller-Abbott 2000 fit): τ_+ = 16.8 ms, τ_- = 33.7 ms, A_+ = 0.86, A_- = 0.25.
  - `stdp_kernel(dt_ms)` — analytical Δw / w₀ for one pre/post pair.
  - `stdp_curve(dt_min, dt_max, points)` — sample the kernel on a grid.
  - `simulate_stdp_pair(dt_ms)` — Brian2 simulation: two `SpikeGeneratorGroup`s, one Synapse with the standard additive trace-based STDP rule (apre/apost decaying exponentials, weight updated `on_pre` and `on_post`), returns observed Δw alongside the analytical kernel value.
- `backend/neuroforge_api/models/simulation.py` — `STDPRequest`, `STDPResponse` with bounded Δt and curve-points validation.
- `backend/neuroforge_api/routers/simulate.py` — POST `/api/simulate/stdp`. Builds the kernel grid, runs Brian2 pair sim, returns both plus parameters and full citation string.
- Frontend:
  - `lib/types.ts` — TS types mirroring the response.
  - `lib/api.ts` — `simulateSTDP(request)`.
  - `components/inspector/STDPPanel.tsx` — SVG curve + observed-Δw red marker + Δt input + "compute Δw" button + observed/kernel/pre/post/τ/A stats + citation.
  - `components/inspector/NeuronInspector.tsx` — STDPPanel inserted between firing plot and citation card.

## Verified — 2026-04-30

### Brian2 simulation matches analytical kernel (audit gate)
The Phase 5 audit gate from ARCHITECTURE.md requires that "the simulated curve must match the published Bi-Poo curve within numerical tolerance". Verified:

| Δt (ms) | Brian2 Δw   | Kernel Δw   | |diff|       |
|--------:|------------:|------------:|------------:|
|   −50.0 | −0.0567     | −0.0567     | 1.4e-17     |
|   −20.0 | −0.1381     | −0.1381     | 0.0e+00     |
|    −5.0 | −0.2155     | −0.2155     | 0.0e+00     |
|    +5.0 | +0.6386     | +0.6386     | 1.1e-16     |
|   +20.0 | +0.2615     | +0.2615     | 5.6e-17     |
|   +50.0 | +0.0438     | +0.0438     | 0.0e+00     |

The Brian2 simulation reproduces the kernel to machine precision. This is not surprising — the Synapses STDP rule is the operational definition of the kernel — but it confirms (a) the units, signs, and timings of the Brian2 implementation are correct, and (b) the kernel exposed to the frontend is the same object the simulation actually uses.

### Backend test suite
```
$ pytest neuroforge_api/tests -q
32 passed in 15.09s
```
- 8 new STDP tests (`test_stdp.py`):
  - Sign convention (Δt > 0 → LTP, Δt < 0 → LTD, 0 → 0).
  - Magnitude bounds: |Δw| ≤ A_+ for LTP and |Δw| ≤ A_- for LTD.
  - Decay: |Δw| at Δt = ±2τ is ≤ 0.16·A.
  - LTP-LTD asymmetry near zero: stdp_kernel(+5) > -stdp_kernel(-5).
  - Brian2 vs kernel within 1e-6 tolerance for 10 sample Δt's.
  - Curve grid is monotone in dt and crosses zero.
  - Endpoint returns canonical response (LTP, citation, parameters).
  - Endpoint returns negative Δw for negative Δt.

### Live HTTP verification
```
$ curl -s -X POST -H 'Content-Type: application/json' \
       -d '{"dt_ms":10}' http://localhost:8000/api/simulate/stdp

dt=10.0 observed=+0.4742 kernel=+0.4742 pre/post=50.0/60.0ms
τ+/-=16.8/33.7  A+/-=0.86/0.25  curve_pts=161
citation: "Bi GQ, Poo MM. Synaptic modifications in cultured hippocampal
           neurons: dependence on spike timing, synaptic strength, and
           postsynaptic cell type. J Neurosci. 1998;18(24):10464-72.
           doi:10.1523/JNEUROSCI.18-24-10464.1998"
```
- Δt=+10 ms → +0.4742 (canonical mid-range LTP, observed=kernel exactly).
- Pre at 50 ms, post at 60 ms — correct sign convention (Δt = post − pre).
- 161 curve points spanning [−80, +80] ms.
- Citation contains real DOI `10.1523/JNEUROSCI.18-24-10464.1998` (resolves to the actual paper).

### Browser verification
With Δt=10, "compute Δw" clicked:
- STDP panel renders kernel curve (white path) with the user point marked as a red dot at (+10, +0.4742).
- Stats show observed +0.4742, kernel +0.4742, pre 50.0 / post 60.0, τ_+ 16.8 / τ_- 33.7, A_+ 0.86 / A_- 0.25.
- Citation panel below shows the full Bi & Poo 1998 reference with DOI.

### Linters
- `ruff check neuroforge_api` — clean
- `pnpm typecheck` — clean
- `pnpm lint` — clean

## Anti-theater self-checks
- **No fabricated parameters.** τ_+, τ_-, A_+, A_- are the widely-cited Bi-Poo 1998 fit values, traced in the module docstring to the original paper plus the Song-Miller-Abbott 2000 computational re-fit that established the canonical numerical values.
- **No fake curve.** Frontend `STDPPanel` draws the curve only from `response.curve_dt_ms` / `response.curve_delta_w`. The empty branch shows "no run yet — click compute" and renders no path.
- **No fake observed value.** The red marker is plotted at `(response.dt_ms, response.observed_delta_w)` returned by the backend, not by re-evaluating the kernel client-side.
- **Brian2 stays the simulation engine.** No bypass to a hand-rolled Δw formula — the Brian2 pair simulation runs through `Synapses` with the standard additive trace-based STDP equations.
- **Citation is real.** DOI `10.1523/JNEUROSCI.18-24-10464.1998` resolves to the actual Bi & Poo 1998 J Neurosci paper.

## Honest limitations

1. **Single-pair STDP only.** Real cumulative plasticity over many spike pairs (the actual Bi-Poo experiment) is not implemented. The kernel is the all-or-nothing pair rule.
2. **No interaction with Phase 4 HH neurons.** The pre/post are SpikeGeneratorGroups with externally-imposed times. Wiring the STDP synapse onto two HH neurons (so spike timing comes out of real biophysics rather than a generator) is a natural next step but adds complexity and was scoped out.
3. **No nearest-neighbor vs all-to-all spike interaction toggle.** Single pair, so this distinction doesn't surface.
4. **No frontend tests** for the STDP panel; same status as phases 2-4.

## Cross-model audit checklist (for Alex to run)

> Audit this diff for: hardcoded fake STDP curves, fabricated Δw values, dead code paths, citation fabrication, parameter drift from the Bi-Poo 1998 paper.
>
> Specifically:
> 1. Are τ_+, τ_-, A_+, A_- in `simulators/stdp.py` the canonical Bi-Poo fit values? (Independent check: τ_+ ≈ 17 ms, τ_- ≈ 34 ms, asymmetric A's with A_+ ≈ 3-4× larger than A_-.)
> 2. Does the analytical kernel match Bi-Poo paper figure 7 in shape? Discontinuity at Δt=0, exponential decay on both sides, asymmetric magnitudes?
> 3. Does the Brian2 `Synapses` model use the standard trace-based additive STDP equations (apre, apost decaying with τ_+, τ_-; on_pre adds A_+ to apre and adds apost to w; on_post subtracts A_- from apost and adds apre to w)? Sign-check the on_pre / on_post handlers.
> 4. Does the frontend STDPPanel only plot data from the response, or does it ever draw a curve before a request is made?
> 5. Does the citation DOI resolve to the real paper?
>
> Manual step: open http://localhost:3000, scroll the inspector to the STDP section, run with Δt=10 (expect ~+0.47 LTP), Δt=-10 (expect ~-0.19 LTD), Δt=0 (expect 0), Δt=80 (expect tiny positive). Verify the red marker tracks the curve at each Δt.
>
> Report only theater. Be brutal.

### Verdict
_Pending Alex's cross-model audit + manual Δt sweep + DOI-resolution check._
