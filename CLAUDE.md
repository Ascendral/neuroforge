# CLAUDE.md — NeuroForge Anti-Theater Protocol

## Owner

Alex Pinkevich (Ascendral). Solo builder. Paying out of pocket. No theater.

## CORE RULE — NO FAKE DATA, NO FAKE FIRING

NeuroForge exists to load **real reconstructed neurons** from public peer-reviewed databases, render their **actual geometry**, and run **biophysically accurate simulations** using **published parameters**. Every clickable element shows its source citation (DOI, archive, lab).

If the data cannot be sourced, the feature is cut. There is no "for now we'll use a placeholder." There is no "approximate firing pattern." There is no "cartoon neuron." That is theater. That is theft.

## Data sources (the only allowed inputs)

- **NeuroMorpho.org** — `https://neuromorpho.org/api/` — 260,000+ SWC reconstructions
- **Allen Brain Atlas** — Allen SDK — cell types, electrophysiology, gene expression
- **ModelDB** — `https://modeldb.science/` — published computational models with parameters
- **Original papers** — Hodgkin & Huxley 1952, Bi & Poo 1998, Hubel & Wiesel 1962, Hopfield 1982, Bliss & Lømo 1973, Hebb 1949

Every neuron rendered must show its archive, lab, species, region, and DOI in the inspector.
Every simulation parameter must cite its paper.

## Stack is LOCKED — do not substitute

- **Backend:** Python 3.12, FastAPI, Brian2 (CPU only — no CUDA, no GPU acceleration in v0.1 or v0.2), Allen SDK, requests, SQLite, NumPy, SciPy
- **Frontend:** Next.js 14 (App Router), TypeScript strict, React 18, React Three Fiber + drei + Three.js, Tailwind + shadcn/ui, Zustand, TanStack Query
- **Monorepo:** pnpm workspaces

Do not "simplify" Brian2 to a hand-rolled ODE. Do not swap Next.js for Vite. Do not skip TypeScript strict.

## Before claiming anything works

1. State what's being measured.
2. Show baseline.
3. Show result with **real data loaded** — paste the actual neuron_id, archive, DOI fetched.
4. Run cross-model audit (independent GPT-4 / fresh Claude session) on the diff: "Audit for hardcoded fake data, mock returns presented as real, dead code paths, claims that don't match implementation. Be brutal."
5. Only commit after audit passes. Audit log goes in `docs/audits/{phase-or-module}.md` with timestamp + verdict.

No measurement = no claim. No audit = no commit.

## Prohibited

- Mock neurons, stub geometry, hand-coded spike patterns presented as real
- Hardcoded "example" data in API responses
- Placeholder animations that simulate firing without going through the simulator
- Claiming a module works without loading a real neuron from NeuroMorpho and showing the firing matches a published curve
- Skipping the cross-model audit because "it's obvious"
- Saying "shipped" without paste-able verification output
- Writing `_try_*` functions or pattern-specific solvers
- Inventing DOIs — every DOI shown in the UI must resolve. CI verifies.
- Unreachable "learning" code — if a learning rule exists in the file tree it must be reachable in the import/call graph. CI verifies.

## Required

- If I don't know, I say "I don't know."
- If sourcing fails (API down, no neuron matches criteria), I say so. I do NOT fabricate.
- Every phase commit lists: data sources used, cross-model audit pass/fail.
- Pre-commit hook blocks `# TODO: hardcoded`, `# FAKE`, `# MOCK` markers without a tracked justification.

## UI rules

- Black/white default, red accent allowed
- Looks expensive (no emoji, no cartoon icons, no rounded-everything cuteness)
- Every clickable surface shows source on click
- Every data point traceable to a publication

## Cross-project enforcement

This file is the per-repo guardrail. It overrides anything more permissive in `~/CLAUDE.md`. Both must be obeyed; the stricter rule wins.
