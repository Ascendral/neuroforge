# Phase 2 Audit — 3D Renderer

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING — Alex to run independent audit on the Phase 2 diff before merging Phase 3 work.

## Scope of Phase 2
Frontend 3D viewer that fetches a real neuron from the Phase 1 backend and renders its actual SWC reconstruction in WebGL. Click-to-log point IDs. Camera controls (orbit / zoom / pan). No inspector panel yet (Phase 3).

## What got built
- `frontend/lib/types.ts` — TS mirror of backend `NeuronResponse` / `NeuronPoint`. Single source of truth still lives in `backend/neuroforge_api/models/neuron.py`.
- `frontend/lib/api.ts` — `fetchNeuron(id)` against `NEXT_PUBLIC_API_BASE` (defaults to `http://localhost:8000`).
- `frontend/components/viewer/SWCNeuron.tsx` — soma rendered as a `<mesh>` sphere at the centroid of all type-1 points; non-root points rendered as instanced cylinder segments from each child to its parent. Color scheme is anti-theater UI rule: red soma (#ff2d2d accent), white basal dendrites, light gray apical, pale blue axon, gray for unknown types. Click handlers wire through to `onSegmentClick`.
- `frontend/components/viewer/NeuronCanvas.tsx` — R3F `<Canvas>` with computed bounding box → camera position at 3× extent. Ambient + 2 directional lights. `<OrbitControls>` with damping, target locked to neuron centroid.
- `frontend/app/page.tsx` — fetches neuron 1 on mount, displays loading / error / loaded states. Header strip shows real metadata. Bottom-left card shows last-clicked point id/type/parent. Bottom-right card shows source archive + first DOI.

## Verified against real data — 2026-04-30

### Browser verification (preview_screenshot at :3000)
- Page loads, `fetch('/api/neurons/1')` returns the cached real neuron from Phase 1's SQLite cache (already populated by Phase 1 tests).
- 3D scene renders the actual cnic_001 morphology: red soma sphere at origin, dendrites branching outward in the published reconstruction pattern of a Rhesus monkey prefrontal layer-3 pyramidal cell. Branches are visible white tubes against black background.
- Header: `cnic_001 · monkey · neocortex / prefrontal / layer 3 · 1,274 points`
- Source card: `neuromorpho.org · Wearne_Hof · neuron 1` and `doi: 10.1016/S0306-4522(02)00305-6` — the real, resolvable upstream DOI.

### Coordinate sanity
Verified live extent matches expected pyramidal-neuron scale:
- x ∈ [-140.81, 149.13]  (width ≈ 290 µm)
- y ∈ [-214.07, 167.78]  (height ≈ 382 µm)
- z ∈ [-17.5, 97.84]     (depth ≈ 115 µm)
- soma radius = 8.1498 µm
These are real reconstructed coordinates, not synthetic.

### Static checks
- `pnpm typecheck` — clean (TS strict)
- `pnpm lint` — clean (next eslint)

## Honest limitations of this verification

1. **Click handler is wired but not end-to-end browser-verified.** Synthetic `PointerEvent` dispatches through `preview_eval` do not propagate through React-Three-Fiber's raycaster the way a real mouse event does. The handler is implemented (`onClick` props on the soma `<mesh>` and the `<Instances>` group, with `console.log` + state callback), and the JSX path that renders the click info card is in place. But a real human mouse click in a browser is required to fully verify the round-trip: click → raycast → handler → state → info card. **This is on Alex's plate during cross-model audit.**

2. **One transient runtime error was observed and explained.** During automated testing I dispatched synthetic `pointerdown`+`pointerup` events with a fabricated `pointerId`. OrbitControls (three-stdlib) reacted with `NotFoundError: Failed to execute 'releasePointerCapture' on 'Element': No active pointer with the given id is found`. This is a TEST artifact — real browser pointer events never trigger this path. The error was not present after a clean page reload. Documented here so it doesn't get rediscovered later as a "phantom bug."

3. **No automated frontend tests yet.** vitest harness not set up. Phase 2 is verified by browser observation + static checks. Frontend test infra is queued for Phase 3 alongside the inspector component.

4. **Per-instance click resolution is by-segment, not by-point.** The user clicks a segment (parent→child cylinder); we report the *child's* `id`/`type`/`parent_id`. That matches the plan ("Click on any segment → console log point ID, type, parent") but is worth flagging.

## Anti-theater self-checks

- **No synthetic neurons.** The renderer accepts only `NeuronResponse` shaped data fetched from the live backend. There is no "if neuron is missing, render a demo" branch.
- **No fabricated coordinates.** All segment endpoints are read straight from `neuron.points`. The only computed values are midpoints, lengths, and orientation quaternions — all derivable from the real points.
- **No fake citations in the UI.** The DOI shown in the corner card comes from `neuron.reference_doi[0]`, sourced from the upstream NeuroMorpho record.
- **No mocked API.** `fetchNeuron` hits the real backend, which hits real `neuromorpho.org` (or its SQLite cache of real fetched bytes).
- **Black/white + red accent UI rule** held: soma is red, branches are white/gray, error text uses red accent, no cartoony elements.

## Cross-model audit checklist (for Alex to run)

Paste the Phase 2 diff into a fresh GPT-4 / Opus session with this prompt:

> Audit this diff for: hardcoded fake neuron data, mock API responses, dead code paths, claims of functionality that don't match implementation, citations that aren't sourced from real records, type drift between frontend `NeuronResponse` and the backend pydantic model, and any rendered geometry that doesn't trace back to the SWC points returned by `fetchNeuron`.
>
> Specifically: does `SWCNeuron` only render shapes derivable from `neuron.points`? Does the click handler actually fire `onSegmentClick` with `child.id`, `child.type`, `child.parent_id`? Does `fetchNeuron` actually hit the backend, or is anything synthesized client-side?
>
> Plus a manual step: open http://localhost:3000, click the soma sphere, click any branch, and confirm the bottom-left card updates with id/type/parent matching what the SWC says.
>
> Report only theater. Be brutal.

Append the verdict (PASS/FAIL + findings) below before opening any Phase 3 PR.

### Verdict
_Pending Alex's cross-model audit + manual click verification._
