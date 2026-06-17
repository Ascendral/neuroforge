# Path 4 — Phase A1: Atlas Acquisition (real-numbers report)

**Date:** 2026-04-30
**Initiative:** Honest atlas fusion — human brain shell with no theater, labeled approximations only

This is a **discovery** doc. No backend code, no rendering. Real probes, real numbers.

## Stack chosen

After probing fsaverage, Allen, AAL, Harvard-Oxford, MNI152:

| Layer                      | Source                            | What it gives                                                                  | Rationale                                                        |
| -------------------------- | --------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| **Brain mesh**             | fsaverage5 from `nilearn` package | 20,484 vertices, 40,960 triangle faces (both hemispheres, pial surface)        | Standard FreeSurfer template, MNI-aligned, browser-friendly size |
| **Cortical parcellation**  | Destrieux 2010                    | 76 cortical regions per hemisphere, per-vertex labels                          | Peer-reviewed, ships with FreeSurfer, downloadable from NITRC    |
| **Subcortical structures** | Harvard-Oxford subcortical        | 22 regions including Left/Right Hippocampus, Amygdala, Thalamus, Caudate, etc. | Covers what Destrieux doesn't (hippocampus is subcortical!)      |
| **V1 anatomical anchor**   | Harvard-Oxford cortical           | Intracalcarine Cortex = V1 / Brodmann 17                                       | Maps cleanly to NeuroMorpho `brain_region:"primary visual"`      |

## Probes (real, executed 2026-04-30)

### fsaverage5 surface

```python
from nilearn import datasets
import nibabel as nib
data = datasets.fetch_surf_fsaverage(mesh='fsaverage5')
img = nib.load(data['pial_left'])
verts = img.darrays[0].data   # (10242, 3)
faces = img.darrays[1].data   # (20480, 3)
# bbox: x=-68.8..1.2  y=-104.7..68.9  z=-48.3..78.1  (mm in MNI space)
```

Bundled inside the `nilearn` Python package (BSD-licensed). No external download needed at runtime. Files live in `.venv/lib/python3.12/site-packages/nilearn/datasets/data/fsaverage5/` — ~390 KB compressed, ~2 MB uncompressed.

### Destrieux 2010 parcellation

```python
des = datasets.fetch_atlas_surf_destrieux()
# 76 labels per hemisphere
# downloaded from nitrc.org/frs/download.php/9343 + 9342 (lh/rh.aparc.a2009s.annot)
# Citation: Destrieux et al. 2010, NeuroImage 53:1-15. doi:10.1016/j.neuroimage.2010.06.010
```

First 8 labels: `Unknown, G_and_S_frontomargin, G_and_S_occipital_inf, G_and_S_paracentral, G_and_S_subcentral, G_and_S_transv_frontopol, G_and_S_cingul-Ant, G_and_S_cingul-Mid-Ant`.

### Harvard-Oxford atlas

```python
ho_sub = datasets.fetch_atlas_harvard_oxford('sub-maxprob-thr25-2mm')
# 22 subcortical regions, includes Left/Right Hippocampus
ho_cort = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
# 49 cortical regions, includes Intracalcarine Cortex (V1)
```

Source: `nitrc.org/frs/download.php/9902/HarvardOxford.tgz` — 25.7 MB tarball, downloads cleanly. Cached in `~/nilearn_data/fsl/` after first run.

V1-relevant cortical labels: `Intracalcarine Cortex, Supracalcarine Cortex, Occipital Pole, Lingual Gyrus, Lateral Occipital Cortex (sup/inf), Occipital Fusiform Gyrus, …`.

Subcortical full list: `Background, L Cerebral White Matter, L Cerebral Cortex, L Lateral Ventricle, L Thalamus, L Caudate, L Putamen, L Pallidum, Brain-Stem, L Hippocampus, L Amygdala, L Accumbens, R… (mirror)`.

## Mapping our 6 modules to atlas regions (no fuzz, exact)

| Module          | NeuroMorpho region tag | Atlas anchor                                                                              | Coverage          |
| --------------- | ---------------------- | ----------------------------------------------------------------------------------------- | ----------------- |
| Hubel-Wiesel V1 | `primary visual`       | Harvard-Oxford **Intracalcarine Cortex** (and Supracalcarine, Occipital Pole as adjacent) | exact             |
| Hebbian / LTP   | `hippocampus`          | Harvard-Oxford **Hippocampus (L+R)**                                                      | exact             |
| Hopfield / CA3  | `CA3`                  | Harvard-Oxford **Hippocampus** (subfield-level mesh would need Iglesias 2015)             | region-level only |
| STDP            | `hippocampus` pair     | Harvard-Oxford **Hippocampus**                                                            | exact             |
| Hodgkin-Huxley  | (squid axon)           | — _no anatomical anchor_                                                                  | n/a               |
| McCulloch-Pitts | (symbolic 1943)        | — _no anatomical anchor_                                                                  | n/a               |

The two "no anchor" modules (HH, M-P) get explicit `no anatomical anchor` labels in the UI, not silent omission.

## License summary

| Asset                             | License                                        | Use            |
| --------------------------------- | ---------------------------------------------- | -------------- |
| `nilearn` Python package          | BSD 3-Clause                                   | unrestricted   |
| fsaverage (FreeSurfer template)   | FreeSurfer License (free for non-commercial)   | OK for our use |
| Destrieux parcellation            | FreeSurfer License                             | OK for our use |
| Harvard-Oxford (FSL distribution) | FSL License (free for non-commercial academic) | OK for our use |

**Commercial-use note:** if NeuroForge ever monetizes, the FreeSurfer + FSL licenses require checking — they're free for non-commercial / academic. Documented now so it doesn't get lost.

## Honest "where this is approximate" callouts (to be enforced in UI)

1. **Schematic placement:** NeuroMorpho neurons do NOT carry MNI stereotaxic coordinates. When we render an SWC inside a region's mesh, we will place it at the region's centroid (or sampled within the binary mask). The UI will show: _"schematic placement within {region_name}; original recording did not include MNI coordinates"_.
2. **Subfield granularity:** Harvard-Oxford labels the whole hippocampus as one region. CA3 vs CA1 vs DG distinctions inside it would require Iglesias 2015 hippocampal subfields atlas (a separate FreeSurfer add-on). Out of scope for Phase A1; flagged.
3. **Cortex parcellation choice:** Destrieux (76 regions) is the default. If we later want Glasser MMP 1.0 (360 regions), it's a separate acquisition + license.
4. **Surface vs volume:** fsaverage is a surface mesh (cortical sheet). Subcortical structures from Harvard-Oxford are volumetric (3D voxel masks). Rendering both in the same scene will require us to extract a triangulated surface from the subcortical binary masks (`scipy.ndimage` + marching cubes). Standard procedure, not theater, but it adds a build step.

## Phases ahead

| Phase  | Deliverable                                                                                                                                                                                                                                                      |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A2** | Backend `data/atlas.py`: lazy-load fsaverage + Destrieux + Harvard-Oxford. `GET /api/brain/mesh` returns vertices+faces+region labels per vertex. Tests verify sizes, label counts, mapping table integrity.                                                     |
| **A3** | Frontend brain-shell viewer (replaces or augments NeuronCanvas). Renders fsaverage pial mesh in R3F. Rotate/zoom/pan.                                                                                                                                            |
| **A4** | Region color-coding + click → inspector shows region info + Brodmann area + connected modules.                                                                                                                                                                   |
| **A5** | Module-to-region routing: clicking V1 region triggers Hubel-Wiesel module; clicking hippocampus triggers Hebbian/Hopfield/STDP.                                                                                                                                  |
| **A6** | Per-region neuron rendering: when a region is active, fetch `n` real reconstructions from NeuroMorpho with the matching brain_region tag, render their SWC inside the region mesh at sampled positions. Each cell labeled "schematic placement within {region}". |
| **A7** | Polish: search bar ("show me visual cortex"), region presets, "what does this region do" panel.                                                                                                                                                                  |

## What this doc does NOT do

- Download any atlas asset to the repo. Phase A1 is a probe.
- Promise a working brain shell. That's A3+.
- Commit any code. The next commit is Phase A2.
- Substitute mouse for human or fudge mappings to look complete.
