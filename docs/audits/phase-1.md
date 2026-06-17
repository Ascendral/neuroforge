# Phase 1 Audit — Real Data Pipeline

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING — Alex to run independent GPT-4 / fresh Claude session on the Phase 1 diff before merging Phase 2 work.

## Scope of Phase 1

NeuroMorpho.org REST client, SWC parser, SQLite cache, `GET /api/neurons/{id}` endpoint. End-to-end fetch of a real reconstructed neuron from the live public API.

## What got built

- `backend/neuroforge_api/sources/neuromorpho.py` — client for `/api/neuron/id/{id}`, paginated `/api/neuron`, and CNG SWC download from `dableFiles/{archive_lower}/CNG version/{name}.CNG.swc`. Typed via `NeuroMorphoNeuron` dataclass.
- `backend/neuroforge_api/parsers/swc.py` — strict SWC parser into `SwcMorphology`. Validates field count, numeric parses, no duplicate ids, no forward parent references. Type-aware accessors for soma / axon / dendrite points.
- `backend/neuroforge_api/db.py` + `models/neuron.py` — SQLite (SQLAlchemy 2.0 declarative) cache table `neurons` storing `metadata_json` + `swc_text` + `fetched_at`. Test-isolated via `reset_for_tests`.
- `backend/neuroforge_api/routers/neurons.py` — `GET /api/neurons/{id}` returns `NeuronResponse` with parsed points + citations + source URLs. Cache-on-miss, serve-from-cache-on-hit.
- `backend/neuroforge_api/main.py` — wired router, swapped deprecated `on_event("startup")` for lifespan handler.

## Verified against real data — 2026-04-30

### Live endpoint output

```
$ curl -s http://localhost:8000/api/neurons/1 | jq summary
neuron_id=1 name=cnic_001 archive=Wearne_Hof species=monkey
brain_region=['neocortex', 'prefrontal', 'layer 3']
cell_type=['Local projecting', 'pyramidal', 'principal cell']
reference_doi=['10.1016/S0306-4522(02)00305-6', '10.1093/cercor/13.9.950']
point_count=1274
swc_url=https://neuromorpho.org/dableFiles/wearne_hof/CNG%20version/cnic_001.CNG.swc
first_3_points=[
  {id:1, type:1, x:0.0,  y:0.0,  z:0.0, radius:8.1498, parent_id:-1},
  {id:2, type:1, x:0.67, y:8.12, z:0.0, radius:8.1498, parent_id:1},
  {id:3, type:1, x:-0.67,y:-8.12,z:0.0, radius:8.1498, parent_id:1},
]
```

Coordinates byte-for-byte match the real `cnic_001.CNG.swc` content fetched directly from neuromorpho.org during API probing. The DOIs are live in CrossRef.

### Test results

```
$ pytest neuroforge_api/tests -v
15 passed in 4.93s
```

- 1 health
- 6 SWC parser unit tests (incl. one parsing the first 12 real cnic_001 data points)
- 5 live integration tests against neuromorpho.org (real neuron fetch, real list page, real SWC download, real 404 handling, URL format)
- 2 end-to-end endpoint tests through TestClient on isolated SQLite (real fetch + cache reuse)

### Linter

```
$ ruff check neuroforge_api
All checks passed!
```

## Theater checks (self-audit, NOT a substitute for cross-model audit)

- No mock NeuroMorpho responses anywhere. Every test that exercises the client hits the real public API and is auto-skipped (with reason logged) only if the network is unreachable.
- No hardcoded neuron data. The 12-line SWC sample in `test_swc_parser.py` is annotated as the real first 12 lines of cnic_001 from a documented URL on a documented date — and is also exercised by `test_download_and_parse_real_swc_for_neuron_1` which fetches the full file from upstream and parses 1,274 real points.
- No fake citations. DOIs come from upstream `reference_doi`. They were not invented.
- No placeholder firing. Phase 1 implements no simulators — only data ingestion. The frontend page still says "Phase 0 — scaffolding. No real data yet." (frontend integration deferred to Phase 2).
- No `# TODO: hardcoded`, `# FAKE`, `# MOCK` markers. Pre-commit hook would block them.

## Known limitations

- Cache has no TTL / invalidation. Phase 2+ may need a "force refresh" path if upstream metadata changes (rare).
- `list_neurons` does not yet expose filter parameters (brain region, species) — only pagination. Filter API needed for Module 2/4 (hippocampal pyramidals) and Module 5 (Allen V1 alternative).
- Allen Brain Atlas integration still unbuilt. Phase 0 audit recommended option (b): direct REST to `api.brain-map.org`. Decision still pending Alex's confirmation; not blocking Phase 2.

## Cross-model audit checklist (for Alex to run)

Paste the Phase 1 diff into a fresh GPT-4 / Opus session with this prompt:

> Audit this diff for: hardcoded fake data, mock returns presented as real, dead code paths, claims of functionality that don't match implementation, dependencies that don't actually resolve, tests that don't actually exercise what their names imply, citations that aren't sourced from real records.
>
> Specifically: do the live integration tests really hit neuromorpho.org? Does the SWC parser handle the documented edge cases? Is the SQLite cache actually wired into the endpoint, or is it dead code? Is the `_build_response` function returning data sourced from the real upstream payload, or is anything synthetic?
>
> Report only theater. Be brutal.

Append the verdict (PASS/FAIL + findings) below before opening any Phase 2 PR.

### Verdict

_Pending Alex's cross-model audit run._
