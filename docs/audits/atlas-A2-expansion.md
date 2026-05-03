# Atlas A2 — Expansion sprint audit

**Date:** 2026-05-02
**Range:** `a5858fa..HEAD` (39 commits since Phase 0 scaffolding)
**Auditor:** Fresh-context Claude session (general-purpose subagent), independent of the build context
**Trigger:** Sprint expanded the atlas surface (Yeo7/17, Schaefer, Pauli, Hansen receptors, Catani tracts, Diedrichsen cerebellum, DiFuMo, cognitive-functions registry, +120 real neurons across 8 populations). No audit had been logged since `phase-0.md` / `atlas-A1-acquisition.md`. Per repo `CLAUDE.md`, no commit without audit — gate had drifted. This doc closes the gap.

## Verdict

**PASS-WITH-CONCERNS**

39 commits clean for a sprint of this size. Every atlas module loads from a real published NIfTI (nilearn fetchers or direct GitHub/Zenodo). Centroids and meshes are computed from voxel data (marching cubes / PCA on real masks), not typed inline. Citations match their data sources. All new modules are wired into `routers/brain.py` — no orphan files. No fabricated DOIs. No mock returns disguised as real. No `_try_*` solvers.

## Findings

### Fix-soon (do not block commit, file as follow-ups)

1. **`backend/neuroforge_api/data/yeo17.py:84`** — hardcoded path `~/nilearn_data/yeo_2011/...` after `fetch_atlas_yeo_2011()`. nilearn doesn't return the 17-network volume in its dict; code reaches into the cache directory by name. Works today, fragile under nilearn cache-layout changes or `NILEARN_DATA` env override. Should use `nilearn.datasets.utils.get_data_dirs()`.

2. **`backend/neuroforge_api/data/receptors.py:163-164` (NET, norepinephrine transporter)** — citation reads `"Hesse S et al. Hansen 2022"` with no journal/year for the primary Hesse study. Filename mismatch: `NET` key vs `NAT_MRB_hc10_hesse.nii` URL. Verify download path; flesh out attribution.

3. **`backend/neuroforge_api/data/receptors.py:153` (FDOPA)** — citation reads `"Gomez et al. Hansen 2022"` with no journal/year/title. Real attribution exists in Hansen 2022 supplementary; fill in.

4. **`frontend/app/page.tsx:179-180`** — `substantiaNigraL/R = [±10, -15, -10]` hardcoded "schematic from Mai 2015". Pauli 2017 atlas (commit `56933c7`) provides real `SNc` centroid; SN cells should anchor to that. Same for cerebellum (Diedrichsen mesh, commit `861090b` — real centroid available). The honest fix has zero cost since the data is already in-tree.

### Nits

- `backend/neuroforge_api/routers/brain.py:485-487` — corpus-callosum bilateral hack applies `±25mm` x-offset when `start_label == end_label`. Disclosed in API `note` field. Magic-number drift risk.
- `frontend/components/viewer/NeuronGlyph.tsx:18` — firing animation `250 µm/ms` / `600 ms` period invented for visibility. Disclosed in docstring as "(visualization, not real biophysics)". Confirm UI legend at runtime actually surfaces this disclosure to the user — code comment isn't enough.

## Verified clean (spot-checked)

- Yeo7/17, Schaefer 2018, Pauli 2017, Diedrichsen 2009, DiFuMo 64, Hansen 2022 — load from real NIfTI, no inline coordinates.
- 35-entry `COGNITIVE_FUNCTIONS` registry — Schultz/Dayan/Montague 1997, Kanwisher 1997, Epstein/Kanwisher 1998, Raichle 2001, Posner 1980, Moruzzi/Magoun 1949, Goldman-Rakic 1995, Hubel/Wiesel 1962, LeDoux 1992 — DOIs/journals/years correct.
- Catani schematic tracts honestly disclosed in API `note`; real HCP-1065 alternative shipped in same phase.
- HCP1065 cache directory present (81 real `.nii.gz` files).

## Uncommitted work cleared to land

- `backend/neuroforge_api/data/yeo17.py` (new, 169 lines) — see fix-soon #1, otherwise clean
- `backend/neuroforge_api/data/hcp1065.py` (new, 207 lines) — clean
- `backend/neuroforge_api/routers/brain.py` (+102 lines, Yeo17 + HCP1065 endpoints) — clean
- `.gitignore` patched: `backend/data_cache/`, `*.tsbuildinfo` ignored
- `frontend/tsconfig.tsbuildinfo` change is build artifact, now gitignored

## Process note

Audit gate had drifted for 39 commits. Going forward: audit log per atlas/data-module batch (every 5-10 related commits), not only at phase boundaries. The expansion sprint produced clean code, but luck is not a process.
