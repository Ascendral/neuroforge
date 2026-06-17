# NeuroForge

Interactive neuroscience-grounded AI lab. Loads real reconstructed neurons from public databases, simulates their firing using **biophysically accurate** models with parameters traceable to peer-reviewed publications, and shows the lineage from real biology to AI computational models. **Zero theater. Zero fake data. Zero placeholder responses.**

## Status

Six canonical modules live, plus citation export and DOI verification.

| Module                      | Phase | Source paper                                            | Real-data anchor (NeuroMorpho)                 |
| --------------------------- | ----- | ------------------------------------------------------- | ---------------------------------------------- |
| McCulloch-Pitts (1943)      | 9     | doi:10.1007/BF02478259                                  | (symbolic — flagged as historical abstraction) |
| Hebbian + LTP (1949 / 1973) | 7     | doi:10.1113/jphysiol.1973.sp010273 + 10.1007/BF00275687 | 18,421 hippocampal pyramidals                  |
| Hodgkin-Huxley (1952)       | 4     | doi:10.1113/jphysiol.1952.sp004764                      | (squid giant axon — Brian2 single-compartment) |
| Hubel-Wiesel V1 (1962)      | 6     | doi:10.1113/jphysiol.1962.sp006837                      | 9,553 primary visual cortex                    |
| Hopfield (1982)             | 8     | doi:10.1073/pnas.79.8.2554 (Nobel 2024)                 | 1,279 CA3 pyramidals                           |
| STDP (Bi & Poo 1998)        | 5     | doi:10.1523/JNEUROSCI.18-24-10464.1998                  | (hippocampal pair recordings)                  |

74 / 74 backend tests passing. ruff / typecheck / eslint clean. All 12 cited DOIs verified resolvable via Crossref.

## Hard rules

- **100% real data.** Every neuron rendered comes from neuromorpho.org via their REST API. Every citation has a real DOI verified against Crossref.
- **No fabricated firing.** Every spike, every weight change, every tuning curve is the output of a simulator running cited published parameters. No `Math.sin(t)` masquerading as a membrane trace anywhere.
- **No mocked APIs.** Live integration tests hit neuromorpho.org and verify the returned data matches what's cited.
- **Allen Brain Atlas remains deferred.** Probing showed Allen does not publish 3D human structure meshes. Documented in `docs/audits/atlas-discovery.md`.
- **Anti-theater protocol** in [CLAUDE.md](CLAUDE.md). Each phase has a per-module audit doc in `docs/audits/`.

## Stack

- **Backend:** Python 3.12, FastAPI, Brian2 (CPU), SQLite, NumPy/SciPy, requests
- **Frontend:** Next.js 14 (App Router), TypeScript strict, React 18, React Three Fiber + drei + Three.js, Tailwind + shadcn/ui, Zustand
- **Monorepo:** pnpm workspaces

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system design.

## Local dev

```bash
# backend (one-time setup)
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

# backend run
uvicorn neuroforge_api.main:app --reload --port 8000

# frontend (one-time setup)
cd frontend
pnpm install

# frontend run (separate terminal)
pnpm dev   # serves on :3000
```

## API

| Endpoint                          | Method | Returns                                                                |
| --------------------------------- | ------ | ---------------------------------------------------------------------- |
| `/health`                         | GET    | `{"status":"ok","version":"0.0.0"}`                                    |
| `/api/neurons/{id}`               | GET    | Full reconstructed neuron with parsed SWC points + metadata + citation |
| `/api/neurons/v1/sample`          | GET    | First N V1 reconstructions from NeuroMorpho                            |
| `/api/neurons/hippocampus/sample` | GET    | First N hippocampal pyramidals                                         |
| `/api/neurons/ca3/sample`         | GET    | First N CA3 pyramidals                                                 |
| `/api/simulate/hh`                | POST   | Hodgkin-Huxley membrane trace under step current                       |
| `/api/simulate/stdp`              | POST   | Bi-Poo STDP weight change for one pre/post pair                        |
| `/api/simulate/v1`                | POST   | V1 Gabor + orientation tuning curve                                    |
| `/api/simulate/hebbian`           | POST   | Pure Hebb vs Oja weight trajectories                                   |
| `/api/simulate/hopfield`          | POST   | Hopfield retrieval from a corrupted pattern                            |
| `/api/simulate/mcp/{gate}`        | GET    | M-P truth table for AND/OR/NOT/NAND/NOR/xor-search                     |
| `/api/citations`                  | GET    | JSON list of all cited references                                      |
| `/api/citations/bibtex`           | GET    | BibTeX dump of every cited reference                                   |

Swagger UI at `http://localhost:8000/docs`.

## Verifying citations

```bash
python scripts/verify_dois.py
```

Hits `api.crossref.org/works/{DOI}` for every cited reference and prints the canonical title returned. Exits non-zero if any DOI is unregistered.

## Tests

```bash
cd backend
source .venv/bin/activate
pytest neuroforge_api/tests -v
```

Includes live integration tests against neuromorpho.org (auto-skipped if network unreachable). Physics tests for HH, STDP, V1, Hebbian, Hopfield, and M-P verify simulator output against canonical published values.

## Cross-model audit

Each phase commit ships a per-module audit doc in `docs/audits/phase-N.md` ending with a checklist for an independent model (GPT-4 / fresh Claude session) to run against the diff. The verdict line at the bottom is `_Pending Alex's cross-model audit + …_` until validated.

This is the project's anti-theater gate. **A green CI build with no cross-model audit attached is meaningless.**

## License

TBD.
