"""Human brain atlas — fsaverage5 surface + Destrieux + Harvard-Oxford.

Sources (all peer-reviewed, all free for academic / non-commercial use):

  Surface mesh:
    Fischl B et al. High-resolution intersubject averaging and a
    coordinate system for the cortical surface. Hum Brain Mapp.
    1999;8(4):272-284.   doi:10.1002/(SICI)1097-0193(1999)8:4<272::AID-HBM10>3.0.CO;2-4
    (fsaverage template, ships with FreeSurfer / nilearn)

  Cortical parcellation:
    Destrieux C, Fischl B, Dale A, Halgren E. Automatic parcellation of
    human cortical gyri and sulci using standard anatomical nomenclature.
    NeuroImage. 2010;53(1):1-15.   doi:10.1016/j.neuroimage.2010.06.010

  Subcortical (and complementary cortical) parcellation:
    Desikan RS et al. An automated labeling system for subdividing the
    human cerebral cortex on MRI scans into gyral based regions of
    interest. NeuroImage. 2006;31(3):968-980.
    doi:10.1016/j.neuroimage.2006.01.021
    (Harvard-Oxford atlas, distributed with FSL.)

Per CLAUDE.md anti-theater rules: every byte of geometry returned here
either is bundled in nilearn (BSD) or is downloaded from the cited NITRC /
FSL distribution paths on first use. No fabricated meshes, no synthetic
labels, no hidden mappings.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import nibabel as nib
import numpy as np
from nilearn import datasets

# Mapping from NeuroForge module names to atlas-region anchors. Curated by
# hand — visible here so it can be audited (anti-theater: no silent mapping).
# Each entry says: when the user clicks this module, which atlas region(s) is
# the module's anatomical home, and what NeuroMorpho query surfaces real
# reconstructions for that region.
MODULE_TO_REGION = {
    "hubel_wiesel": {
        "atlas": "harvard_oxford_cortical",
        "labels": ["Intracalcarine Cortex"],
        "neuromorpho_filter": {"brain_region": ["primary visual"]},
        "note": "V1 / Brodmann area 17 — primary visual cortex. Where Hubel-Wiesel 1962 first recorded simple/complex cell tuning in cat V1.",
    },
    "hebbian": {
        "atlas": "harvard_oxford_subcortical",
        "labels": ["Left Hippocampus", "Right Hippocampus"],
        "neuromorpho_filter": {"brain_region": ["hippocampus"], "cell_type": ["pyramidal"]},
        "note": "Hippocampal pyramidal cells — where Bliss & Lømo 1973 first demonstrated LTP, the cellular correlate of Hebb's rule.",
    },
    "hopfield": {
        "atlas": "harvard_oxford_subcortical",
        "labels": ["Left Hippocampus", "Right Hippocampus"],
        "neuromorpho_filter": {"brain_region": ["CA3"], "cell_type": ["pyramidal"]},
        "note": "Hippocampal CA3 pyramidals — recurrent collaterals are the canonical biological substrate for Hopfield-style attractor recall. (Note: Harvard-Oxford labels the whole hippocampus as one region; CA3 vs CA1 subfields require Iglesias 2015 — flagged.)",
    },
    "stdp": {
        "atlas": "harvard_oxford_subcortical",
        "labels": ["Left Hippocampus", "Right Hippocampus"],
        "neuromorpho_filter": {"brain_region": ["hippocampus"], "cell_type": ["pyramidal"]},
        "note": "STDP was first measured in hippocampal pyramidal pairs (Bi & Poo 1998). Same anatomical region as Hebbian.",
    },
    "hodgkin_huxley": {
        "atlas": None,
        "labels": [],
        "neuromorpho_filter": None,
        "note": "No human anatomical anchor — Hodgkin-Huxley 1952 used the SQUID GIANT AXON (Loligo). The model is universal, but its original anatomy is invertebrate.",
    },
    "mcp": {
        "atlas": None,
        "labels": [],
        "neuromorpho_filter": None,
        "note": "No anatomical anchor — McCulloch-Pitts 1943 is a symbolic threshold-logic model, the historical-abstraction predecessor of biophysical neurons.",
    },
}


@dataclass(frozen=True, slots=True)
class CorticalSurface:
    """Fsaverage5 pial surface for one hemisphere."""

    hemisphere: str  # "left" or "right"
    vertices: np.ndarray   # (N, 3) float32
    faces: np.ndarray      # (M, 3) int32
    destrieux_label_id: np.ndarray  # (N,) int — per-vertex Destrieux region id


@dataclass(frozen=True, slots=True)
class AtlasRegion:
    """A single named region in the curated atlas."""

    region_id: int
    label: str
    atlas: str  # "destrieux" / "harvard_oxford_cortical" / "harvard_oxford_subcortical"
    centroid_mni_mm: tuple[float, float, float] | None
    voxel_count: int | None  # for volumetric regions; None for surface


@lru_cache(maxsize=1)
def fsaverage_pial(hemisphere: str) -> CorticalSurface:
    """Load fsaverage5 pial surface + Destrieux per-vertex labels."""
    if hemisphere not in ("left", "right"):
        raise ValueError("hemisphere must be 'left' or 'right'")

    fs = datasets.fetch_surf_fsaverage(mesh="fsaverage5")
    pial_path = fs[f"pial_{hemisphere}"]
    surf = nib.load(pial_path)
    verts = np.asarray(surf.darrays[0].data, dtype=np.float32)
    faces = np.asarray(surf.darrays[1].data, dtype=np.int32)

    des = datasets.fetch_atlas_surf_destrieux()
    label_map = np.asarray(des[f"map_{hemisphere}"], dtype=np.int32)
    if label_map.shape[0] != verts.shape[0]:
        raise RuntimeError(
            f"Destrieux label count {label_map.shape[0]} != vertex count {verts.shape[0]}"
        )

    return CorticalSurface(
        hemisphere=hemisphere,
        vertices=verts,
        faces=faces,
        destrieux_label_id=label_map,
    )


@lru_cache(maxsize=1)
def destrieux_labels() -> list[str]:
    """Per-id Destrieux region names. Index 0 is 'Unknown'."""
    return list(datasets.fetch_atlas_surf_destrieux()["labels"])


@lru_cache(maxsize=1)
def harvard_oxford_subcortical_atlas():
    return datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr25-2mm")


@lru_cache(maxsize=1)
def harvard_oxford_cortical_atlas():
    return datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr25-2mm")


def _voxel_centroid_mni_mm(atlas_img, label_id: int) -> tuple[float, float, float] | None:
    """Compute MNI-mm centroid of all voxels with the given integer label."""
    arr = np.asarray(atlas_img.dataobj)
    mask = arr == label_id
    if not mask.any():
        return None
    coords = np.argwhere(mask).astype(np.float64).mean(axis=0)
    affine = atlas_img.affine
    homog = np.array([coords[0], coords[1], coords[2], 1.0])
    mni = (affine @ homog)[:3]
    return float(mni[0]), float(mni[1]), float(mni[2])


def _voxel_count(atlas_img, label_id: int) -> int:
    arr = np.asarray(atlas_img.dataobj)
    return int(np.sum(arr == label_id))


def _load_atlas_image(maps):
    """nilearn returns either a path or an already-loaded Nifti1Image."""
    if isinstance(maps, str):
        return nib.load(maps)
    return maps


def harvard_oxford_subcortical_regions() -> list[AtlasRegion]:
    """All Harvard-Oxford subcortical regions with centroid + voxel count."""
    atlas = harvard_oxford_subcortical_atlas()
    img = _load_atlas_image(atlas["maps"])
    out: list[AtlasRegion] = []
    for idx, label in enumerate(atlas["labels"]):
        out.append(
            AtlasRegion(
                region_id=idx,
                label=label,
                atlas="harvard_oxford_subcortical",
                centroid_mni_mm=_voxel_centroid_mni_mm(img, idx),
                voxel_count=_voxel_count(img, idx),
            )
        )
    return out


def harvard_oxford_cortical_regions() -> list[AtlasRegion]:
    atlas = harvard_oxford_cortical_atlas()
    img = _load_atlas_image(atlas["maps"])
    out: list[AtlasRegion] = []
    for idx, label in enumerate(atlas["labels"]):
        out.append(
            AtlasRegion(
                region_id=idx,
                label=label,
                atlas="harvard_oxford_cortical",
                centroid_mni_mm=_voxel_centroid_mni_mm(img, idx),
                voxel_count=_voxel_count(img, idx),
            )
        )
    return out
