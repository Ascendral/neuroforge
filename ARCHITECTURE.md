# NeuroForge — Architecture

## The organizing idea: one ladder, two sides

Every artifact in the app sits on one of five rungs, on the brain side or the AI side. The rung is the unit of navigation; the cross-side link is the unit of content.

| rung | brain              | AI                    | live models on this rung                     |
| ---- | ------------------ | --------------------- | -------------------------------------------- |
| 1    | organ              | deployed system       | —                                            |
| 2    | region / network   | architecture          | dopamine RPE (VTA/SNc)                       |
| 3    | circuit            | block internals       | modern Hopfield ≡ attention, V1, Hopfield    |
| 4    | cell               | unit                  | Hodgkin-Huxley, McCulloch-Pitts              |
| 5    | synapse / molecule | parameter             | synapse kinetics, STDP, Hebbian/Oja          |

Cross-side links carry an evidence tag — `equivalence` (proved same mathematics), `strong` (quantitative/causal evidence), `analogy` (conceptual only), `none` (no counterpart; the note explains why). The registry tests reject nodes that lack citations, lack a link or none-note, claim `equivalence` without the proof attached, or anchor to atlas labels that do not exist.

## Data flow

```
 nilearn / OSF / Zenodo / GitHub releases          neuromorpho.org REST
 (fsaverage, Harvard-Oxford, Pauli, Diedrichsen,   (search + SWC)
  Yeo, Schaefer, DiFuMo, HCP-1065, Hansen PET,
  Allen microarray)                                        │
              │                                            ▼
              ▼                                  parsers/swc.py → SQLite cache
   data/atlas.py, pauli.py, cerebellum.py, …               │
              │                                            │
              ▼                                            ▼
   data/scales.py  ──anchors resolved──▶  routers/scales.py  ◀── data/research_timeline.py
   (66 nodes, 35 edges,                   /api/scales/graph
    68 cross-side links)                  /api/research/timeline
                                                    │
   simulators/*  ──▶  routers/simulate.py           │
   (9 models)         /api/simulate/*               │
                                                    ▼
                               frontend/lib/api.ts → page.tsx
                                                    │
        ┌──────────────┬──────────────┬─────────────┼──────────────┐
        ▼              ▼              ▼             ▼              ▼
   BrainCanvas     ScaleExplorer   AISchematic   TimelineView   NeuronCanvas
   (R3F, atlases,  (two columns,   (SVG, every   (72 milestones, (R3F SWC)
    real cells,     links by        box a node,   jump-to-node)
    highlights)     evidence)       every arrow
                        │           an edge)
                        └──────┬────────┘
                               ▼
                           NodeDetail
              (what / does / how, numbers, anchors → brain,
               real cells, bridge cards, zoom in/out, live model)
```

## Backend layout

```
backend/neuroforge_api/
├── main.py                 # FastAPI app; routers: neurons, simulate, citations, brain, scales
├── citations.py            # module bibliography (BibTeX export + DOI gate)
├── data/
│   ├── scales.py           # THE multi-scale registry (brain + AI nodes, edges, cites, analogs)
│   ├── research_timeline.py
│   ├── atlas.py            # fsaverage / Destrieux / Harvard-Oxford, cognitive functions, tracts
│   ├── pauli.py cerebellum.py networks.py yeo17.py schaefer.py difumo.py hcp1065.py
│   ├── receptors.py        # Hansen 2022 PET maps (19 receptors)
│   └── allen_genes.py
├── simulators/
│   ├── hodgkin_huxley.py stdp.py hebbian.py hopfield.py hubel_wiesel.py mcp.py
│   ├── modern_hopfield.py  # Ramsauer 2021: update ≡ attention; capacity sweep
│   ├── dopamine_rpe.py     # Schultz 1997 TD(0)
│   └── synapse.py          # Destexhe 1994 + Jahr-Stevens 1990
├── routers/  neurons.py simulate.py citations.py brain.py scales.py
├── models/   neuron.py simulation.py
├── sources/  neuromorpho.py
├── parsers/  swc.py
└── tests/    (116)
```

## Frontend layout

```
frontend/
├── app/page.tsx                    # views: brain | scales | ai schematic | timeline | neuron
├── components/
│   ├── viewer/    BrainCanvas, NeuronCanvas, SWCNeuron, NeuronGlyph
│   ├── scales/    ScaleExplorer, AISchematic, NodeDetail, TimelineView, LinePlot, strength.ts
│   ├── inspector/ NeuronInspector, FiringPlot, CitationCard,
│   │              HHPanel, STDPPanel, HebbianPanel, HopfieldPanel, ModernHopfieldPanel,
│   │              DopaminePanel, SynapsePanel, HubelWieselPanel, McCullochPittsPanel
│   └── ui/        CollapsibleSection
└── lib/           api.ts, types.ts, neuron-context.tsx
```

## Adding a node (the only way content grows)

1. Add a `Node(...)` to `BRAIN` or `AI` in `data/scales.py` with `description`, `function`, `mechanism`, `cites`, and either `analogs=(Analog(target, strength, note, cites),)` or `no_analog_note`.
2. Brain nodes: add `ho_labels` / `pauli` / `cerebellum` anchors and a `neuromorpho` query if real cells exist. Optional `widget` if a simulator applies.
3. `pytest neuroforge_api/tests/test_scales.py` — integrity gate.
4. `python scripts/verify_dois.py` — every DOI must resolve.
5. For an AI node, add a slot in `AISchematic.tsx` `LAYOUT` (otherwise it is listed in the "not placed" strip, never hidden).

## Gates

- `scripts/verify_dois.py` — Crossref then DataCite; all three registries.
- `tests/test_scales.py` — registry integrity (see above).
- Simulator tests compare against published values (HH resting potential, STDP window, Schultz panels, Jahr-Stevens closed form, attention equivalence to 1e-12, capacity crossover).
- ruff + eslint + prettier + tsc on every push; pytest on every push.
- Pre-commit hook blocks `# TODO: hardcoded`, `# FAKE`, `# MOCK` without tracked justification.
- Audit log per sprint in `docs/audits/`.

## Scope decisions

- Brian2 CPU only. No Tauri (web only). No Allen SDK (numpy pin) — Allen data via abagen cache and REST.
- The AI side models a decoder-only transformer LLM plus its training loop; CNN-specific structure appears only where the brain link needs it (V1 ↔ first conv layer).
- The registry is a curriculum, not an encyclopedia: canonical regions, seven circuits, ten cell types, nine synaptic mechanisms. Growth is by DOI-gated node additions.
