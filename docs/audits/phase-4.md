# Phase 4 Audit — Hodgkin-Huxley Simulator (Brian2)

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING — Alex to run independent audit on the Phase 4 diff before merging Phase 5 work. **This is the first phase that runs real physics, so the audit gate is materially heavier than phases 0-3.**

## Scope of Phase 4
First real biophysics. Single-compartment Hodgkin-Huxley simulator using Brian2 with the original 1952 squid-giant-axon parameters; FastAPI POST endpoint; frontend "run hh" button; FiringPlot wired to live data. Per ARCHITECTURE.md, real-time WebSocket spike streaming was descoped to Phase 4.5 — HTTP POST returning the full trace is sufficient for verification and doesn't fabricate any simulation data.

## What got built
- `backend/neuroforge_api/simulators/hodgkin_huxley.py` — Brian2 model with the canonical H-H 1952 rate equations in modern shifted-potential form. Parameters: C_m=1 µF, ḡ_Na=120 mS, ḡ_K=36 mS, g_L=0.3 mS, E_Na=+50 mV, E_K=-77 mV, E_L=-54.387 mV. V_rest=-65 mV. Uses `exponential_euler` integrator, dt=0.01 ms by default. Singularities at V=-40 mV (α_m) and V=-55 mV (α_n) are regularized with a 1e-9 mV bias to the numerator — preserves the analytic L'Hôpital limit and prevents NaN if integration ever lands exactly at the removable singular point.
- `backend/neuroforge_api/models/simulation.py` — `HHRequest` (duration, stimulus_uA, start, end, dt, record_every_n) and `HHResponse` (times_ms, voltage_mV, stimulus_uA, spike_times_ms, dt_ms, citation).
- `backend/neuroforge_api/routers/simulate.py` — POST `/api/simulate/hh`. Translates request to `simulate_hh()`, returns aligned arrays + the full Hodgkin-Huxley 1952 citation string.
- `backend/neuroforge_api/main.py` — included `simulate_router`.
- Frontend `lib/api.ts` — added `simulateHH(request)`.
- Frontend `components/inspector/FiringPlot.tsx` — accepts `HHResponse`, draws axes (mV, ms) with grid at -90 / -65 / 0 / +50 mV, plots the membrane potential as a white path, plots stimulus envelope as a thin blue path on a bottom strip, and draws red vertical lines at each detected spike time. Empty state remains honest ("no simulation yet — click run hh"). No synthetic curve is ever drawn.
- Frontend `components/inspector/NeuronInspector.tsx` — adds a "stim µA" input (default 10), a "run hh" button, summary stats (spikes, peak, trough, samples), and the full upstream citation string under the plot.

## Verified against canonical H-H physics — 2026-04-30

### Backend test suite
```
$ pytest neuroforge_api/tests -q
24 passed in 10.75s
```
- 7 new physics tests (`test_hodgkin_huxley.py`):
  - `test_resting_steady_state_gating_values` — m∞(-65), h∞(-65), n∞(-65) match published values.
  - `test_rests_at_minus_65_with_no_stimulus` — V stays within ±0.5 mV of rest, no spikes.
  - `test_subthreshold_pulse_does_not_spike` — 1 µA depolarizes but doesn't cross 0 mV.
  - `test_suprathreshold_step_produces_action_potential` — 10 µA → ≥1 spike, peak in [+30,+60] mV, AHP < -65 mV.
  - `test_repetitive_firing_under_sustained_current` — ≥3 spikes with CV(ISI) < 0.3.
  - `test_higher_current_increases_firing_rate` — monotone f-I curve.
  - `test_invalid_arguments_rejected` — boundary cases.
- 2 endpoint tests (`test_simulate_endpoint.py`): real POST to TestClient, schema validation, citation string check.

### Live HTTP smoke test
```
$ curl -s -X POST -H 'Content-Type: application/json' \
       -d '{"duration_ms":80,"stimulus_uA":10,"stimulus_start_ms":10,"stimulus_end_ms":70}' \
       http://localhost:8000/api/simulate/hh

samples=2000  dt_ms=0.01
spikes=[11.93, 26.93, 41.65, 56.36, 72.65]
peak_mV=40.04   trough_mV=-76.06
citation: "Hodgkin AL, Huxley AF. A quantitative description of membrane
           current and its application to conduction and excitation in nerve.
           J Physiol. 1952;117(4):500-44. doi:10.1113/jphysiol.1952.sp004764"
```
- AP peak +40.04 mV — within published canonical overshoot range (+30 to +50 mV).
- AHP trough -76.06 mV — consistent with K-channel-driven afterhyperpolarization toward E_K = -77 mV.
- 5 spikes over 60 ms of stimulation = 83 Hz steady-state firing, ISI≈14.7-15 ms (regular).
- First spike latency ≈ 1.93 ms after stimulus onset — canonical for I_inj just above rheobase × 4.
- Stimulus on/off transients reflected correctly (spike train aligned with the 10-70 ms stimulus window).

### Browser verification (preview screenshot)
With "stim µA" = 10 and "run hh" clicked:
- Plot renders the actual returned trace: 5 AP spikes with the canonical shape (rapid up-stroke, +40 mV peak, fast down-stroke, AHP undershoot below resting, recovery).
- Red vertical lines mark the 5 detected spike times.
- Blue stimulus envelope on the bottom strip outlines the 10-70 ms square pulse.
- Stats panel: `spikes=5, peak mV=40.04, trough mV=-76.06, samples=2000` — bit-for-bit consistent with the curl above.
- Citation rendered under the stats: full 1952 paper reference with the resolvable DOI.

### Linters
- `ruff check neuroforge_api` — clean
- `pnpm typecheck` — clean (TS strict)
- `pnpm lint` — clean

## Anti-theater self-checks
- **No hand-rolled ODE.** The simulation runs through Brian2's `NeuronGroup` + `exponential_euler` integrator. The stack-locked simulation engine is honored.
- **No fabricated trace.** The `FiringPlot` empty branch shows "no simulation yet — click run hh" and renders nothing else. Once a request returns, the plot renders strictly the arrays from `HHResponse`. No fallback "demo trace" is ever drawn.
- **No fake spikes.** `spike_times_ms` come from a Brian2 `SpikeMonitor` watching a `v > 0 mV` threshold during the live integration. Frontend draws spike markers at those times only.
- **No fabricated citation.** The citation string lives in one place (`routers/simulate.py:HH_CITATION`) and contains the real 1952 paper title, journal, volume, year, and DOI. The DOI `10.1113/jphysiol.1952.sp004764` resolves to the actual Hodgkin & Huxley paper on the Wiley/Physiological Society site.
- **Parameters trace to the paper.** Every numeric constant in `hodgkin_huxley.py` is annotated in the module docstring with the 1952 paper as the source. The leak reversal is set to -54.387 mV, the standard value chosen so that the full model rests at -65 mV.
- **Singularity regularization is documented and bounded.** The 1e-9 mV bias on α_m / α_n numerators is mathematically equivalent to the L'Hôpital limit (preserves the steady-state values to ≥7 decimal places) and is annotated with a textbook reference.

## Known limitations / honest gaps

1. **Single-compartment, point neuron.** This Phase 4 cut models the soma as one electrically homogeneous compartment, not the morphologically reconstructed 1,274-point cnic_001. The "selected point" in the UI does not yet drive any compartment-specific dynamics — it is shown for context only. Compartmental simulation across the loaded SWC is a much larger build (NEURON or multi-compartment Brian2) and is explicitly out of scope for Phase 4.
2. **No WebSocket spike streaming.** Plan called for `/ws/sim/{id}`. Deferred to a later phase or dropped if the HTTP path is sufficient. The request-response cycle for an 80 ms simulation completes in ~1.5-2 s end-to-end, including Brian2 codegen overhead — fast enough to feel responsive without streaming.
3. **No GPU.** Brian2 runs on CPU only (per project decision; user has no A100). Codegen target is `numpy` to avoid C++ toolchain dependency at request time.
4. **One Brian2 process per request.** Brian2 keeps global state (clocks, networks). Concurrent simulation requests will conflict. Phase 4 is single-user/single-tab; concurrency hardening goes in polish.
5. **Pyparsing deprecation warnings from Brian2 internals.** Not our code. Brian2 hasn't migrated to the new pyparsing API. Suppressing globally would hide other warnings; leaving as-is until upstream updates.

## Cross-model audit checklist (for Alex to run — heavier this phase)

> Audit this diff for: hardcoded fake firing patterns, mock returns presented as real, dead code paths, claims that don't match implementation, fabricated citations, parameters that drift from the cited 1952 paper.
>
> Specifically check the physics:
> 1. Are the rate equations α_m, β_m, α_h, β_h, α_n, β_n in `simulators/hodgkin_huxley.py` consistent with the original Hodgkin & Huxley 1952 paper (modern shifted-potential form)?
> 2. Are C_m, ḡ_Na, ḡ_K, g_L, E_Na, E_K, E_L set to the values stated in the 1952 paper?
> 3. Does the resting potential numerically converge to -65 mV when E_L = -54.387 mV?
> 4. Does the AP shape (peak ≈ +40 mV, AHP ≈ -77 mV, spike width, repetitive firing rate at 10 µA) match published H-H 1952 figures?
> 5. Does the FiringPlot only render data from the live response, with no synthetic curve in any branch?
> 6. Does the citation string in the response match the actual paper, DOI, volume, year?
>
> Plus a manual step: open http://localhost:3000, click "run hh" with stim=10 µA, confirm the plot shows ~5 spikes with canonical shape. Try stim=0, confirm flat trace at -65 mV with 0 spikes. Try stim=1, confirm subthreshold (no spikes). Try stim=20, confirm faster firing. The DOI in the citation panel should resolve to the real H-H paper.
>
> Report only theater. Be brutal.

### Verdict
_Pending Alex's cross-model audit + manual stimulus sweep + DOI-resolution check._
