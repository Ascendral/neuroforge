# Multi-scale ladder sprint — audit log

**Date:** 2026-09-13
**Range:** `01bfae6..HEAD` (backend commit `110c3af`, frontend commit follows)
**Trigger:** Alex asked for (1) NeuroForge refined as a complete, up-to-date body of neuro research, (2) a complete schematic of the "AI brain", and (3) a model of both brain and AI that zooms from the whole system down to the neuron / synapse.

## What shipped

**One ladder, two sides.** Brain and AI are placed on the same five rungs — organ/system, region/architecture, circuit/block, cell/unit, synapse/parameter — in `backend/neuroforge_api/data/scales.py` (39 brain nodes, 35 AI nodes, 35 edges, 68 cross-side links). Every node states what it is, what it does and how, cites primary literature, and either names its counterpart on the other side with an evidence tag or carries an explicit no-analog note.

**Evidence tags are the honesty mechanism.** `equivalence` may only be claimed with the Ramsauer 2021 proof attached (enforced by `test_equivalence_is_reserved_for_proved_mathematics`). `strong` requires quantitative or causal evidence and is used 14 times (e.g. dopamine ≙ TD error; layer norm ≙ divisive normalization; block depth ≙ cortical hierarchy). `analogy` is the default and says so. `none` is used where the disanalogy is the fact (backprop, optimizer, tokenizer, training/deployment split, data regime, amygdala, SST gating, vesicle stochasticity, gene→protein consolidation, cell-type diversity).

**Three new simulators, all real math with cited constants:**
- `modern_hopfield.py` — Ramsauer update; numerically identical to `softmax(βQKᵀ)V` (tested to 1e-12); energy monotone (tested); classic-vs-modern capacity sweep on identical random patterns: classic collapses past α = 0.138, modern retrieves at α = 2 (tested). β exposed; the transformer β = 1/√d on raw bipolar patterns blends patterns past α ≈ 1 (tested, and disclosed in the docstring).
- `dopamine_rpe.py` — TD(0) with the Montague 1996 tapped-delay stimulus. Reproduces the three Schultz 1997 panels exactly (δ = 1 at reward naive; δ ≈ 0.67 at cue / 0 at reward trained; δ = −1 on omission). Numerical constants (α, γ, bins, times, trials) are the demo's and are returned in `parameter_note` — the response says which claims are the paper's (sign, timing) and which are ours.
- `synapse.py` — Destexhe 1994 dual-exponential kinetics; Jahr-Stevens 1990 Mg²⁺ block in closed form (tested against the formula); NMDA J-shaped I-V. Kinetic constants are the Destexhe fits and the table cites them.

**Research timeline** — 72 milestones 1921 → 2025 in `research_timeline.py`. Post-2020 entries: Dabney 2020, Lillicrap 2020, Ramsauer 2020, TEM 2020, GPT-3, Schrimpf 2021, Beniaguev 2021, Goldstein 2022, InstructGPT, DishBrain, induction heads, Siletti 2023 human cell atlas, BICCN mouse atlas, Willett 2023, Tang 2023, Winding 2023, SAE features, Frank 2023, FlyWire 2024, H01 2024, MICrONS 2025, Wang 2025 foundation model, IBL 2025 brain-wide map. No 2026 entries: nothing from 2026 could be verified against a registered DOI at build time, so nothing was invented.

**DOI gate extended.** `scripts/verify_dois.py` now checks all three registries and falls back to DataCite for arXiv DOIs. Result at build: **128 / 128 resolved.** Two candidate DOIs were found to resolve to the WRONG paper during drafting (a chicken-EEG paper under the key meant for Golgi; a disentangled-representation paper under the key meant for Frank 2023) and were removed / corrected — the verifier prints titles precisely so this is caught by eye.

**Follow-ups from the A2 audit closed:** yeo17 path derived from nilearn's bunch; FDOPA primary source found via Crossref (García-Gómez 2018, Imagen Diagnóstica); NET primary source (Hesse 2017, EJNMMI); SN and Purkinje cells anchored to per-hemisphere centroids computed from the real Pauli / Diedrichsen meshes (olfactory bulb is now the only schematic placement and the legend says so).

## What "complete" means here — and what it does not

Complete = every rung exists on both sides, is populated with the canonical structures at that scale, is navigable up and down, and is cited. It does NOT mean every known fact of neuroscience is in the registry: 39 brain nodes cover the canonical regions, seven circuits, ten cell types and nine synaptic/molecular mechanisms — a curriculum, not an encyclopedia. The registry format makes adding a node a ~20-line, DOI-gated edit; the integrity tests reject any node without citations, without a cross-side link or explicit none-note, or with an anchor label absent from the atlas.

## Known limits (disclosed in UI or code)

- AI schematic layout is static, keyed by node id; new registry nodes without a slot are listed in a strip at the bottom rather than hidden.
- Cross-link lines in the scale explorer are drawn only between nodes on the same rung; links to other rungs are shown as jump chips.
- `RealCells` queries NeuroMorpho live; two cell nodes (PV basket, SST Martinotti) use `cell_type` strings that may return zero results for some region filters — the UI shows the real count, including 0.
- Frontend has no automated tests (pre-existing gap); typecheck / eslint / prettier are clean and the five views were exercised in the Browser pane.

## Verification performed

- `pytest`: 116 / 116 (was 83).
- `ruff`: clean. `tsc --noEmit`, `next lint`, `prettier --check`: clean.
- `scripts/verify_dois.py`: 128 / 128.
- Browser: scales view (level 2, links drawn), node detail for dopamine nuclei (anchors VTA/SNc resolved to MNI, 836 NeuroMorpho reconstructions listed, RLHF bridge), dopamine model trained and plotted, AI schematic rendered with dimming on selection, attention head → modern Hopfield run (modern overlap 1.00, classic 0.28, attention row peaked on target), timeline rendered.

_Independent cross-model audit: pending Alex._
