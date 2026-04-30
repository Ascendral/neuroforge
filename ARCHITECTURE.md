# NeuroForge — Architecture

## What it is
Interactive 3D neuroscience-grounded AI lab. Loads real reconstructed neurons from public databases, renders their actual SWC geometry as clickable 3D meshes, runs biophysically accurate firing simulations using published parameters, and shows the lineage from biological neurons to AI computational models. Six modules covering the foundational neuro↔AI bridges.

## Stack (LOCKED — see CLAUDE.md)
- Backend: Python 3.12, FastAPI, Brian2 (CPU), Allen SDK, SQLite, NumPy/SciPy
- Frontend: Next.js 14 App Router, TS strict, React 18, R3F + drei + Three.js, Tailwind + shadcn/ui, Zustand, TanStack Query
- Monorepo: pnpm workspaces

## Data flow

```
[NeuroMorpho.org / Allen Brain Atlas / ModelDB]
              │
              ▼
   backend/neuroforge_api/sources/   (HTTP clients)
              │
              ▼
   backend/neuroforge_api/parsers/swc.py
              │
              ▼
   SQLite cache (backend/data/neurons.sqlite)
              │
              ▼
   FastAPI routers (REST + WebSocket)
              │
   HTTP/WS    │
              ▼
   frontend/lib/api.ts, frontend/lib/ws.ts
              │
              ▼
   React Three Fiber canvas
              │
       ┌──────┴──────┐
       ▼             ▼
   3D mesh        Inspector panel
   (SWC tubes)    (citations, params, firing plot)
```

## Backend layout
```
backend/
├── pyproject.toml
├── neuroforge_api/
│   ├── main.py              # FastAPI app entry
│   ├── config.py
│   ├── db.py                # SQLite session
│   ├── models/              # pydantic + SQLAlchemy
│   ├── sources/             # neuromorpho.py, allen.py, modeldb.py
│   ├── parsers/             # swc.py
│   ├── simulators/          # mcculloch_pitts, hebbian, hodgkin_huxley, stdp, hubel_wiesel, hopfield
│   ├── routers/             # neurons, simulate, ws
│   └── tests/
└── data/
    ├── neurons.sqlite
    └── swc_cache/
```

## Frontend layout
```
frontend/
├── package.json
├── app/
│   ├── layout.tsx
│   ├── page.tsx             # main lab UI
│   └── modules/{mcp,hebbian,hh,stdp,hubel-wiesel,hopfield}/page.tsx
├── components/
│   ├── viewer/              # NeuronCanvas, SWCNeuron, ClickableSegment, Controls
│   ├── inspector/           # NeuronInspector, CitationCard, FiringPlot
│   ├── modules/             # ModuleSelector, ParamSliders
│   └── ui/                  # shadcn primitives
├── lib/                     # api.ts, ws.ts, swc-parser.ts, types.ts
└── store/                   # zustand
```

## Six modules
| # | Module | Anchor | Real data | AI lineage | Limit shown |
|---|---|---|---|---|---|
| 1 | McCulloch-Pitts (1943) | Action potential threshold | None (symbolic, flagged historical) | Foundation of NNs | Cannot solve XOR |
| 2 | Hebbian + LTP (Hebb 1949 / Bliss-Lømo 1973) | Hippocampal LTP | NeuroMorpho hippocampal pyramidals | Hopfield, SOMs | Runaway potentiation |
| 3 | Hodgkin-Huxley (1952) | Squid giant axon | Real cortical pyramidal SWC + 1952 ODE params | SNNs, neuromorphic chips | Compute cost |
| 4 | STDP (Bi & Poo 1998) | Hippocampal pair recordings | NeuroMorpho hippocampal + Bi-Poo curve | Loihi 2 | Local rule, no global credit assignment |
| 5 | Hubel-Wiesel (1962) | Cat V1 simple/complex cells | Allen Brain Atlas V1 neurons | First conv layer of CNNs | Linear filter, missing cortical complexity |
| 6 | Hopfield (1982) | Hippocampal CA3 attractors | NeuroMorpho CA3 reconstructions | Modern Hopfield → transformer attention | Capacity ~0.14N, spurious attractors |

## v0.1.0 scope (locked)
- Brain regions: **neocortex + hippocampus only** (everything above lives in these two)
- Web-only (no Tauri yet)
- Brian2 CPU only (no CUDA / GPU)
- Repo visibility decision deferred until Phase 0 local scaffold runs

## Phased build
- **Phase 0** — scaffolding (this commit)
- **Phase 1** — NeuroMorpho client + SWC parser + SQLite cache
- **Phase 2** — 3D renderer (R3F SWC mesh, click→inspector)
- **Phase 3** — Inspector panel + citation cards + empty firing plot
- **Phase 4** — Hodgkin-Huxley simulator (Brian2)
- **Phase 5** — STDP module
- **Phase 6** — Hebbian module
- **Phase 7** — Hubel-Wiesel module
- **Phase 8** — Hopfield module
- **Phase 9** — McCulloch-Pitts module (symbolic, flagged historical)
- **Phase 10** — Polish, citation export (BibTeX), full README, tag v0.1.0

Each phase requires: tests pass → manual verification with real data → cross-model audit → audit log committed in `docs/audits/` → commit.

## CI checks
- `scripts/verify_dois.py` — fetches every DOI in citations index, fails build on 404
- `scripts/verify_call_graph.py` — fails if any "learning" function is unreachable from imports
- ruff + eslint + prettier on every push
- pytest + vitest on every push

## Pre-commit hook
Blocks staged files containing `# TODO: hardcoded`, `# FAKE`, `# MOCK` without a tracked justification comment.
