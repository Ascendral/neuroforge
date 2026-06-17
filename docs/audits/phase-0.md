# Phase 0 Audit — Scaffolding

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING — Alex to run an independent GPT-4 (or fresh Claude session) audit on the Phase 0 diff before merging Phase 1 work.

## Scope of Phase 0

Bare scaffolding only: monorepo layout, dependencies installable, FastAPI returns `/health`, Next.js renders a placeholder page, CI workflow defined, pre-commit hook in place. No real data fetched. No simulators implemented.

## Verified

- `pnpm 10.33.2` and `python 3.12.13` installed via Homebrew
- `pip install -e '.[dev]'` succeeds in `backend/.venv` (Brian2 2.9, numpy 1.26.4, scipy 1.17.1, fastapi, sqlalchemy, pytest, ruff)
- `pnpm install` succeeds at repo root, populating `frontend/node_modules`
- Backend test `pytest neuroforge_api/tests -v` → 1 passed (`test_health_returns_ok`)
- Backend running on :8000 → `curl /health` returns `{"status":"ok","version":"0.0.0"}`
- Frontend running on :3000 → page renders "NeuroForge / Phase 0 — scaffolding. No real data yet. / v0.0.0" (verified via accessibility snapshot)
- Frontend `pnpm typecheck` passes (TS strict)

## Not yet implemented (intentional, Phase 1+)

- NeuroMorpho.org client
- SWC parser
- SQLite cache
- 3D viewer
- All 6 simulators
- Inspector panel + citation cards
- WebSocket spike streaming

## Open decisions blocking Phase 1

### 1. Allen SDK incompatibility with Python 3.12

**Discovered:** `pip install allensdk>=2.16` fails — allensdk 2.16.x pins `numpy<1.24`, which has no Python 3.12 wheels.

**Options:**

- **(a)** Drop Python to 3.11 (requires retesting Brian2, simple revert)
- **(b)** Replace `allensdk` with direct REST calls to `api.brain-map.org` (we already use `requests` for NeuroMorpho — same approach, fewer deps, more transparent about what we fetch)
- **(c)** Isolate `allensdk` in a separate Python 3.11 subprocess invoked by the main 3.12 backend

**Recommendation:** (b). Matches the data-sources philosophy already in CLAUDE.md (every fetch is HTTP and auditable), avoids dragging a heavy unmaintained SDK into the venv.

**Status:** `allensdk` removed from `backend/pyproject.toml` with a comment pointing to this audit. Decision needed before Module 5 (Hubel-Wiesel) work begins.

### 2. GitHub remote

Repo is local-only at `~/ClaudeWork/neuroforge/`. `Ascendral` org does not yet exist on GitHub (verified via `gh api orgs/Ascendral` → 404). User to decide:

- **(a)** Create `Ascendral` org on github.com, then `gh repo create Ascendral/neuroforge --private`
- **(b)** Push to `zanderone1980/neuroforge --private` for now, transfer later
- **(c)** Stay local-only until v0.1 ships

## Theater checks performed by implementer

- No mock neuron data anywhere
- No hardcoded firing patterns
- No "for now we'll fake X" placeholders
- Pre-commit hook (`scripts/pre-commit-hook.sh`) blocks `# TODO: hardcoded`, `# FAKE`, `# MOCK`, `// FAKE`, `// MOCK` markers without explicit `ANTI-THEATER-OK:` justification
- Page text on `/` says exactly "Phase 0 — scaffolding. No real data yet." — no false claims of capability

## Cross-model audit checklist (for Alex to run)

Paste the Phase 0 diff into a fresh GPT-4 / Opus session with this prompt:

> Audit this diff for: hardcoded fake data, mock returns presented as real, dead code paths, claims of functionality that don't match implementation, dependencies that don't actually resolve. Report only theater. Be brutal.

Append the verdict (PASS/FAIL + findings) below before opening any Phase 1 PR.

### Verdict

_Pending Alex's cross-model audit run._
