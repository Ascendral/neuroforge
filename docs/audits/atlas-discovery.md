# Brain Atlas Pivot — Discovery Report

**Date:** 2026-04-30
**Initiative:** "Huge map in the shape of an actual brain, zoomable to functional regions and individual neurons"
**Decision blocker:** Source of the human brain mesh + parcellation
**Stance promised:** No fuzz — single authoritative source preferred

This is a discovery doc. Nothing was rendered, scaffolded, or claimed to work. Real numbers from real probes only.

## Probes

### Allen Brain Atlas API — `api.brain-map.org`

| Probe                                             | Result                                                                                                                                                                            |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Ontology/query.json` (list ontologies)           | 200 OK. 17+ ontologies returned. **Ontology id 7 = "Human Brain Atlas"**, id 1 = "Mouse Brain Atlas".                                                                             |
| `Structure/query.json?criteria=[ontology_id$eq7]` | 200 OK. **1,839 human-atlas structures** in the ontology.                                                                                                                         |
| Sample human structures at depth 3                | Real, canonical: `Cx` cerebral cortex, `CxN` cerebral nuclei, `TH` thalamus, `SbT` subthalamus, `ET` epithalamus, `Hy` hypothalamus, `Cb` cerebellum, `MTg` midbrain tegmentum, … |

### Allen mesh download — `download.alleninstitute.org/informatics-archive/current-release/`

| Path                                                     | HTTP       | Notes                                                                         |
| -------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------- |
| `current-release/` (directory listing)                   | 200        | Children: `brain_observatory/`, `mouse_annotation/`, `mouse_ccf/`, `rna_seq/` |
| `mouse_ccf/annotation/ccf_2017/structure_meshes/997.obj` | 200 (HEAD) | Mouse CCF root structure mesh — exists.                                       |
| **`human_brain_atlas/`**                                 | —          | **Does not exist.** No `human_*` directory at this path.                      |

### Verdict on "Allen all the way down" for human brain

**Not possible** as a no-fuzz unified source.

- The Allen mouse atlas publishes 3D structure meshes per region — perfect for our use case if we wanted mouse.
- The Allen human atlas exists as a richly tagged ontology and 2D atlas plates (with reference images, MR volumes for the 6 microarray donor brains, gene expression maps), but **no equivalent downloadable per-structure 3D mesh archive**.
- This is consistent with how Allen's pipelines were funded: the Mouse Common Coordinate Framework (CCF) v3 was built to support whole-brain integration; the Human Brain Atlas was built around microarray sampling of donor brains and has no analogous CCF mesh release.

I did not invent this finding. I probed and the directory either exists or doesn't.

## Three honest paths from here

### Path 1 — Pivot to mouse, stay no-fuzz

Use Allen Mouse CCFv3 throughout: per-region 3D meshes, atlas ontology, mouse-specific cell types from Allen Cell Types Database, mouse SWC reconstructions (already heavily represented in NeuroMorpho — neuron 102367 from the V1 module is mouse, from the Allen Cell Types archive). Single coordinate system, single ontology. Works perfectly.

**Cost:** the project ships as a _mouse_ brain atlas, not a human one. The user asked for "human brain" — going mouse instead is a meaningful scope change, but it's the only no-fuzz option that delivers actual whole-brain 3D rendering with real region IDs and real cell drill-in.

### Path 2 — Human brain, accept atlas fusion

Use **MNI152** (or **fsaverage** from FreeSurfer) for the human brain surface mesh, plus a parcellation atlas (**AAL**, **Desikan-Killiany**, or **Glasser HCP MMP 1.0**). Map NeuroMorpho's free-text `brain_region` tags onto the parcellation labels through a hand-curated mapping table.

**Cost:** the mapping table is the fuzziness the user explicitly rejected. Free-text tags like `"neocortex / occipital / primary visual / layer 4"` and atlas labels like `Glasser_V1` or `AAL_Calcarine_R` need a translation layer. Some neurons land cleanly, others ambiguously. This is what the user's "no fuzz" rule explicitly rules out.

License notes (still unverified at network cost):

- MNI152 (BIC McGill ICBM152) — generally CC, requires citation
- fsaverage (FreeSurfer) — academic-free, NIH-funded
- AAL — academic-free
- Glasser HCP MMP 1.0 — Connectome Coordination Facility, requires DUA for full data

### Path 3 — Cancel the atlas pivot for now

Keep NeuroForge as the per-module deep-dive it currently is (6 modules, real cell metadata, real physics). Don't promise a whole-brain map at all. Document the discovery finding so a future contributor doesn't re-investigate.

**Cost:** does not deliver the visual map the user described. But it preserves the no-fuzz commitment without overpromising.

## Recommendation

**Path 3 short-term, Path 1 long-term.** Specifically:

1. **Now:** ship Phase 10 polish on the existing 6 modules (BibTeX export, README with screenshots, citation DOI verifier in CI) and Phase 11 module-to-3D wiring (clicking a listed neuron in V1/Hippocampus/CA3 panels actually renders that neuron's SWC). These are concrete, finishable, anti-theater wins.

2. **Later, if user still wants the brain-map experience:** pivot to Allen Mouse CCFv3. Document the human-brain disappointment honestly. The mouse atlas gives the same lineage demo (V1, hippocampus, CA3 all exist in mouse) with a clean unified data layer.

I am NOT pivoting unilaterally. This doc surfaces the choice. The user picks.

## What this doc deliberately does NOT do

- Claim Allen has human mesh data when it doesn't.
- Suggest scraping unofficial / academic sources to fake a unified atlas.
- Start scaffolding any frontend/backend code for a brain-shell viewer.
- Substitute Allen Mouse for Allen Human silently (theater).
- Hand-wave a NeuroMorpho free-text → atlas-region mapping as "good enough".
