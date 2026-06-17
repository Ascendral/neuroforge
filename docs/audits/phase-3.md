# Phase 3 Audit — Inspector + Citations + Firing Plot Placeholder

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING — Alex to run independent audit on the Phase 3 diff before merging Phase 4 work.

## Scope of Phase 3

Side-panel inspector showing real upstream metadata, last-clicked point info, source citations with resolvable links, and an honest empty firing-plot placeholder (no fake membrane traces).

## What got built

- `frontend/components/inspector/CitationCard.tsx` — archive, neuron link to NeuroMorpho `neuron_info.jsp`, raw SWC URL, all `reference_doi` rendered as `https://doi.org/{doi}` anchors, all `reference_pmid` as `https://pubmed.ncbi.nlm.nih.gov/{pmid}/` anchors. No fabricated identifiers.
- `frontend/components/inspector/FiringPlot.tsx` — SVG with mV/ms axes and an explicit caption "phase 4 wires hodgkin-huxley". No synthetic trace. No mock spikes.
- `frontend/components/inspector/NeuronInspector.tsx` — right-side `<aside>`, three sections: Neuron metadata, Selection (point id / type label / parent), Membrane potential, Source. All values pulled from the `NeuronResponse` already verified live in Phase 1/2.
- `frontend/app/page.tsx` — refactored from floating cards to a flex layout: canvas left flex-1, inspector right at 360px. State for `selected` lifted to page; flows to both `NeuronCanvas.onSegmentClick` and `NeuronInspector.selected`.

## Verified against real data — 2026-04-30

### Browser screenshot

- Header: `cnic_001 · monkey · neocortex / prefrontal / layer 3`
- Left pane: 3D viewer rendering the real reconstructed pyramidal neuron (red soma, dendritic tree)
- Right pane (inspector):
  - NEURON section: name `cnic_001`, id `#1`, species `monkey`, scientific `Macaca mulatta`, region `neocortex / prefrontal / layer 3`, cell type `Local projecting, pyramidal, principal cell`, points `1,274`
  - SELECTION section: empty state "click any segment to inspect" (since no click yet from automation)
  - MEMBRANE POTENTIAL: SVG with mV / ms axes + caption "phase 4 wires hodgkin-huxley"
  - SOURCE: `Wearne_Hof`, link to `cnic_001 (#1)` → neuromorpho.org neuron info page, link to raw SWC under `/dableFiles/wearne_hof/CNG version/cnic_001.CNG.swc`
  - REFERENCES: 2 DOIs and 2 PMIDs

### Live anchor verification (read from rendered DOM)

```
neuromorpho.org/neuron_info.jsp?neuron_id=1                                cnic_001 (#1)
neuromorpho.org/dableFiles/wearne_hof/CNG%20version/cnic_001.CNG.swc       (raw SWC)
doi.org/10.1016/S0306-4522(02)00305-6                                       (Neuroscience 2002)
doi.org/10.1093/cercor/13.9.950                                             (Cerebral Cortex 2003)
pubmed.ncbi.nlm.nih.gov/12204204/                                           (PMID 12204204)
pubmed.ncbi.nlm.nih.gov/12902394/                                           (PMID 12902394)
```

Every URL is canonical and resolvable. No invented DOIs or PMIDs.

### Static checks

- `pnpm typecheck` — clean
- `pnpm lint` — clean
- No console errors

## Anti-theater self-checks

- **No fake DOIs.** Every DOI rendered comes from `neuron.reference_doi` populated upstream by NeuroMorpho.org. Same for PMIDs.
- **No fake firing trace.** `FiringPlot` shows axes only and an explicit "phase 4 wires hodgkin-huxley" caption. No `Math.sin(t)` masquerading as a membrane potential.
- **No filler metadata.** When a field is missing upstream (e.g., empty `cell_type`), the inspector renders "—" instead of inventing a value. Verified in code path; not exercised in this neuron because all fields are present.
- **No type drift.** `NeuronInspector` only consumes properties already declared on `NeuronResponse` (which mirrors the backend pydantic model). No `any` casts.

## Honest limitations

1. **Click-to-update SELECTION still requires real mouse input.** The state plumbing is in place (`NeuronCanvas` → `setSelected` → `NeuronInspector.selected` → renders id/type/parent rows), and the empty-state branch is verified, but the "user clicked a real segment" path was not exercised by automation for the same R3F-raycaster reason described in Phase 2's audit. Test: open `:3000`, click a dendrite, watch SELECTION populate with a numeric id and the SWC type label.

2. **No frontend unit tests.** Vitest still not wired. Phase 3 components are pure-presentational and would be straightforward to snapshot-test; this can be batched with Phase 4 when the firing plot starts receiving live data.

3. **Citation card does not yet attempt to verify DOIs at request time.** A `scripts/verify_dois.py` CI job is described in `ARCHITECTURE.md` for the polish phase but is not implemented yet; Phase 3 trusts upstream.

## Cross-model audit checklist (for Alex to run)

> Audit this diff for: hardcoded fake citations, fabricated DOIs/PMIDs, dead code, claims of functionality that don't match implementation, type drift, any rendered text that wasn't sourced from the live `NeuronResponse`. Specifically: do all hrefs in `CitationCard` come from `neuron.reference_doi` / `neuron.reference_pmid` / `neuron.source_url` / `neuron.swc_url`? Does `FiringPlot` render any synthetic curve, or only static axes + an explicit "not yet implemented" caption? Does `NeuronInspector` ever pass through values from anywhere other than the `neuron` prop and `selected` prop?
>
> Plus a manual step: open `http://localhost:3000`, click any dendrite or the soma, confirm the SELECTION block updates with a numeric point id and a human-readable SWC type. Click each citation link and confirm they resolve to real pages (DOI resolves to a journal article, PMID resolves to a PubMed entry, NeuroMorpho links resolve to the actual neuron's page and the actual SWC file).
>
> Report only theater. Be brutal.

### Verdict

_Pending Alex's cross-model audit + manual click + link-resolution check._
