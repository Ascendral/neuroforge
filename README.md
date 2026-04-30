# NeuroForge

Interactive 3D neuroscience-grounded AI lab. Load real reconstructed neurons from public databases, click any branch to inspect factual sourced data, run biophysically accurate firing simulations using published parameters.

**Status:** Phase 0 (scaffolding). Not yet usable.

## Hard rules
- 100% real data from NeuroMorpho.org, Allen Brain Atlas, ModelDB
- Every clickable element shows source citation (DOI, archive, lab)
- If data cannot be sourced, the feature is cut
- No mocks, no stubs, no placeholder firing patterns
- Cross-model audit required per phase (see `docs/audits/`)
- See [CLAUDE.md](CLAUDE.md) for the full anti-theater protocol

## Stack
- **Backend:** Python 3.12, FastAPI, Brian2 (CPU), Allen SDK, SQLite
- **Frontend:** Next.js 14, TypeScript, React Three Fiber, Tailwind + shadcn/ui
- **Monorepo:** pnpm workspaces

## Local dev
```bash
# backend
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn neuroforge_api.main:app --reload --port 8000

# frontend
cd frontend
pnpm install
pnpm dev   # :3000
```

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md).

## License
TBD.
