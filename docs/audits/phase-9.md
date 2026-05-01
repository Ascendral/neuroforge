# Phase 9 Audit — McCulloch-Pitts 1943 (Threshold Logic + XOR Impossibility)

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING

## Naming
Module-name-first: **McCulloch-Pitts 1943 (Threshold Logic + XOR Impossibility)**.

## Scope
Sixth and final canonical module from the original plan: the historical-abstraction bookend. Symbolic threshold-logic neuron computing canonical Boolean gates (AND, OR, NOT, NAND, NOR), plus a brute-force search confirming the Minsky-Papert 1969 result that no single-layer M-P neuron computes XOR. No NeuroMorpho data anchor — M-P is a pure mathematical abstraction; honest about that.

## What got built
- `backend/neuroforge_api/simulators/mcp.py`:
  - `mp_neuron(weights, threshold, inputs)` — y = 1 iff Σ wᵢ xᵢ ≥ θ.
  - `truth_table(n_inputs)` — all 2ⁿ binary combinations.
  - `GATES` dictionary — hand-derived (w, θ) for AND, OR, NOT, NAND, NOR with truth tables.
  - `evaluate_gate(name)` — runs the gate's full truth table through the M-P neuron, returns produced vs expected and pass/fail.
  - `search_xor_single_layer()` — brute-force search over 13×13×13 = 2,197 (w₁, w₂, θ) integer-stepped triples; confirms no perfect XOR solution exists.
  - Module docstring traces every claim to McCulloch-Pitts 1943, Minsky-Papert 1969, Rumelhart-Hinton-Williams 1986.
- `backend/neuroforge_api/models/simulation.py` — `MCPGateResponse`, `MCPXorSearchResponse`.
- `backend/neuroforge_api/routers/simulate.py` — GET `/api/simulate/mcp/{gate_or_search}` (also handles `xor-search` keyword).
- `backend/neuroforge_api/tests/test_mcp.py` — 8 new tests including parametrized truth-table verification for each gate, XOR-impossibility, endpoint round-trip.
- Frontend:
  - `lib/types.ts`, `lib/api.ts` — `MCPGateResponse`, `MCPXorSearchResponse`, `fetchMCPGate`, `fetchXorImpossibility`.
  - `components/inspector/McCullochPittsPanel.tsx` — gate selector buttons (AND, OR, NOT, NAND, NOR), truth-table grid (input | expect | produced with ✓/✗), weight/threshold display, XOR brute-force button + results readout, full citation.
  - `components/inspector/NeuronInspector.tsx` — McCullochPittsPanel mounted at the top of the modules section (it's the historical bookend, so it leads chronologically: 1943 → 1949 (Hebb) → 1962 (H-W) → 1973 (Bliss) → 1982 (Hopfield) → 1998 (Bi-Poo)).

## Verified — 2026-04-30

### Backend tests
```
$ pytest neuroforge_api/tests -q
68 passed in 13.51s
```
- 8 new M-P tests:
  - `test_each_gate_truth_table` (parametrized × 5) — every gate produces its full expected truth table.
  - `test_xor_has_no_single_layer_solution` — the search returns `no_solution=True`, `best_match_correct < 4` (in fact = 3, since one corner can always be missed).
  - `test_unknown_gate_rejected` — input validation.
  - `test_endpoint_evaluates_all_gates` — TestClient round-trip with `passes=True` and citation on every gate.
  - `test_endpoint_xor_search` — `no_solution=True`, citation contains "Minsky".

### Live HTTP smoke test
```
$ curl -s 'http://localhost:8000/api/simulate/mcp/AND'
AND passes=True produced=[0, 0, 0, 1] expected=[0, 0, 0, 1] weights=[1.0, 1.0] threshold=2.0

$ curl -s 'http://localhost:8000/api/simulate/mcp/xor-search'
XOR no_solution=True tried=2197 best=3/4 best_w=[-3.0, -3.0] best_t=-3.0
```

### Browser verification (DOM-confirmed, screenshot)
- McCulloch-Pitts panel renders with the AND truth table:
  - A B | expect | produced
  - 0 0 | 0 | 0 ✓
  - 1 0 | 0 | 0 ✓
  - 0 1 | 0 | 0 ✓
  - 1 1 | 1 | 1 ✓
  - w = [1, 1] · θ = 2 · "computed correctly"
- Gate selector buttons (AND, OR, NOT, NAND, NOR) all functional; clicking triggers re-fetch.
- XOR brute-force section shows: target `0 1 1 0`, "searched 2,197 triples in [-3, 3] step 0.5", "best match: 3 / 4 at w=[-3, -3], θ=-3", "no single-layer M-P neuron computes XOR (Minsky-Papert 1969)" in red.
- Citation rendered: "McCulloch WS, Pitts W. A logical calculus of the ideas immanent in nervous activity. Bull Math Biophys. 1943;5(4):115-133. doi:10.1007/BF02478259. Minsky M, Papert S. Perceptrons. MIT Press, 1969 (single-layer XOR impossibility). Rumelhart DE, Hinton GE, Williams RJ. Learning representations by back-propagating errors. Nature. 1986;323(6088):533-536. doi:10.1038/323533a0 (multi-layer escape)."

### Linters
- `ruff check neuroforge_api` — clean
- `pnpm typecheck` — clean
- `pnpm lint` — clean

## Anti-theater self-checks
- **No fabricated truth tables.** Each gate's `expected` tuple in `GATES` is the canonical Boolean function output. The `produced` tuple is the live result of running `mp_neuron` for each row of the truth table. The frontend renders both and visibly shows ✓/✗ — if a gate fails, that would be visible.
- **Empirical XOR proof, not just a citation.** Rather than asserting "Minsky-Papert says XOR can't be computed," the search actually exhausts 2,197 (w₁, w₂, θ) integer-stepped triples and reports the best partial match (3/4). The test asserts this empirically. Anyone can re-run with a wider grid to convince themselves.
- **Honest historical framing.** The panel header says "historical abstraction" and the position in the inspector follows chronology (1943 first). M-P is not anchored to a specific cell from NeuroMorpho — that would be theater since the model is symbolic, not biophysical. The action-potential-threshold concept that motivates M-P is already implemented and cited (Hodgkin-Huxley 1952, Phase 4).
- **Real citations.** McCulloch-Pitts 1943 DOI `10.1007/BF02478259` resolves. Rumelhart-Hinton-Williams 1986 DOI `10.1038/323533a0` resolves. Minsky-Papert 1969 is a book (no DOI), cited by full title.

## Honest limitations
1. **No live "design your own gate" tool.** The user picks from 5 fixed gates; can't enter custom weights/threshold and see the resulting truth table. UI enhancement, not a science gap.
2. **XOR search is integer-stepped.** A finer grid (or a continuous LP) would give a sharper empirical proof but doesn't change the theoretical conclusion (which Minsky-Papert proved via geometric argument: XOR is not linearly separable in input space).
3. **No multi-layer demo.** A two-layer M-P network solving XOR would be a natural follow-up showing the Rumelhart-Hinton-Williams 1986 escape. Cited but not implemented.

## Cross-model audit checklist (for Alex to run)

> Audit this diff for: hardcoded gate outputs, fabricated XOR proof, dead code, citation drift.
>
> Specifically:
> 1. Does `mp_neuron` actually compute `1 iff Σ wᵢ xᵢ ≥ θ`?
> 2. Does each gate's hand-set (w, θ) actually produce its claimed truth table when run through `mp_neuron`?
> 3. Does `search_xor_single_layer` actually iterate all 2,197 triples and check each, or is the `no_solution=True` value short-circuited?
> 4. Does the frontend render only response data — no synthetic ✓ marks?
> 5. Do the M-P 1943 and Rumelhart 1986 DOIs resolve?
>
> Manual: open http://localhost:3000, scroll inspector to McCulloch-Pitts panel, click each gate (AND, OR, NOT, NAND, NOR) and confirm 4 ✓ rows. Click "brute-force search" and confirm "no single-layer M-P neuron computes XOR (Minsky-Papert 1969)" in red.
>
> Report only theater. Be brutal.

### Verdict
_Pending Alex's cross-model audit + manual gate sweep + DOI resolution._

---

## Original 6-module plan: COMPLETE

| Module | Phase | Anchor | Status |
|---|---|---|---|
| 1. McCulloch-Pitts 1943 | 9 | Action-potential threshold | ✓ |
| 2. Hebbian + LTP (Hebb 1949 / Bliss-Lømo 1973) | 7 | Hippocampal pyramidals | ✓ |
| 3. Hodgkin-Huxley 1952 | 4 | Squid giant axon | ✓ |
| 4. STDP (Bi & Poo 1998) | 5 | Hippocampal pairs | ✓ |
| 5. Hubel-Wiesel 1962 | 6 | V1 simple/complex cells | ✓ |
| 6. Hopfield 1982 | 8 | CA3 attractor recall | ✓ |

68/68 backend tests passing. ruff/typecheck/lint all clean. Allen Brain Atlas integration **never attempted** — the project shipped on NeuroMorpho.org alone, with the deferred decision honestly documented across every audit doc.
