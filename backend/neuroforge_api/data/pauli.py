"""Pauli 2017 probabilistic subcortical atlas.

Reference:
    Pauli WM, Nili AN, Tyszka JM. A high-resolution probabilistic in vivo
    atlas of human subcortical brain nuclei.
    Sci Data. 2018;5:180063. doi:10.1038/sdata.2018.63

16 deep subcortical nuclei in MNI152 space — finer-grained than Harvard-
Oxford. Includes structures that *aren't* in HO at all but are essential
to understanding reward, movement, sleep, memory:

  Pu / Ca / NAC      — striatum (input nuclei of basal ganglia)
  EXA                — extended amygdala
  GPe / GPi          — globus pallidus external / internal
  SNc                — substantia nigra pars compacta (DOPAMINE for movement)
  SNr                — substantia nigra pars reticulata (GABA output)
  PBP                — parabrachial pigmented nucleus
  VTA                — ventral tegmental area (DOPAMINE for reward)
  VeP                — ventral pallidum
  HN                 — habenular nuclei
  HTH                — hypothalamus
  MN                 — mammillary nucleus (Papez memory circuit)
  STH                — subthalamic nucleus
  RN                 — red nucleus

Per CLAUDE.md anti-theater: every label/centroid/mesh comes from the
real Pauli 2017 NIfTI atlas distributed by the authors via OSF.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import nibabel as nib
import numpy as np
from nilearn import datasets

# Per-nucleus full names + functional system-coloring.
PAULI_NUCLEI: dict[str, dict] = {
    "Pu":  {"full_name": "Putamen",                       "system": "striatum",      "color": "#5eebff"},
    "Ca":  {"full_name": "Caudate nucleus",               "system": "striatum",      "color": "#5eebff"},
    "NAC": {"full_name": "Nucleus accumbens",             "system": "striatum",      "color": "#5eebff"},
    "EXA": {"full_name": "Extended amygdala",             "system": "amygdala",      "color": "#ff6bd4"},
    "GPe": {"full_name": "Globus pallidus, external",     "system": "pallidum",      "color": "#c45eff"},
    "GPi": {"full_name": "Globus pallidus, internal",     "system": "pallidum",      "color": "#a64aee"},
    "SNc": {"full_name": "Substantia nigra pars compacta",
            "system": "dopaminergic",  "color": "#ff2d2d"},
    "RN":  {"full_name": "Red nucleus",                   "system": "midbrain",      "color": "#e0796b"},
    "SNr": {"full_name": "Substantia nigra pars reticulata",
            "system": "midbrain",      "color": "#ffae5e"},
    "PBP": {"full_name": "Parabrachial pigmented nucleus",
            "system": "dopaminergic",  "color": "#ff5e8c"},
    "VTA": {"full_name": "Ventral tegmental area",        "system": "dopaminergic",  "color": "#ff2d2d"},
    "VeP": {"full_name": "Ventral pallidum",              "system": "pallidum",      "color": "#bf80ff"},
    "HN":  {"full_name": "Habenular nuclei",              "system": "habenula",      "color": "#7fff9b"},
    "HTH": {"full_name": "Hypothalamus",                  "system": "hypothalamus",  "color": "#ffb96b"},
    "MN":  {"full_name": "Mammillary nucleus",            "system": "memory",        "color": "#ffd86b"},
    "STH": {"full_name": "Subthalamic nucleus",           "system": "basal_ganglia", "color": "#d99bff"},
}


@dataclass(frozen=True, slots=True)
class PauliNucleus:
    label_id: int
    abbrev: str
    full_name: str
    system: str
    color: str
    voxel_count: int
    centroid_mni_mm: tuple[float, float, float]
    vertices: np.ndarray
    faces: np.ndarray


@lru_cache(maxsize=1)
def _pauli_atlas():
    return datasets.fetch_atlas_pauli_2017(atlas_type="deterministic")


@lru_cache(maxsize=1)
def _pauli_volume_and_affine() -> tuple[np.ndarray, np.ndarray, list[str]]:
    atlas = _pauli_atlas()
    img = atlas["maps"]
    if isinstance(img, str):
        img = nib.load(img)
    arr = np.asarray(img.dataobj)
    if arr.ndim == 4:
        arr = arr[..., 0]
    return arr.astype(np.int16), img.affine, [str(label) for label in atlas["labels"]]


@lru_cache(maxsize=32)
def nucleus_mesh(label_id: int) -> PauliNucleus | None:
    from scipy.ndimage import gaussian_filter
    from skimage import measure

    arr, affine, labels = _pauli_volume_and_affine()
    if label_id < 1 or label_id >= len(labels):
        return None
    abbrev = labels[label_id]
    spec = PAULI_NUCLEI.get(abbrev)
    if spec is None:
        return None
    mask = (arr == label_id).astype(np.float32)
    if not mask.any():
        return None
    smoothed = gaussian_filter(mask, sigma=0.6)
    try:
        verts, faces, _, _ = measure.marching_cubes(smoothed, level=0.3)
    except (RuntimeError, ValueError):
        return None
    homog = np.column_stack([verts, np.ones(len(verts))])
    mni = (affine @ homog.T).T[:, :3]

    coords = np.argwhere(mask > 0).astype(np.float64).mean(axis=0)
    centroid_homog = np.array([coords[0], coords[1], coords[2], 1.0])
    centroid_mni = (affine @ centroid_homog)[:3]

    return PauliNucleus(
        label_id=label_id,
        abbrev=abbrev,
        full_name=spec["full_name"],
        system=spec["system"],
        color=spec["color"],
        voxel_count=int(mask.sum()),
        centroid_mni_mm=(float(centroid_mni[0]), float(centroid_mni[1]), float(centroid_mni[2])),
        vertices=mni.astype(np.float32),
        faces=faces.astype(np.int32),
    )


def all_pauli_nuclei() -> list[PauliNucleus]:
    _, _, labels = _pauli_volume_and_affine()
    out: list[PauliNucleus] = []
    for label_id in range(1, len(labels)):
        n = nucleus_mesh(label_id)
        if n is not None:
            out.append(n)
    return out
