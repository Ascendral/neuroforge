"""Diedrichsen 2009 SUIT-based cerebellar atlas.

Reference:
    Diedrichsen J, Balsters JH, Flavell J, Cussans E, Ramnani N. A
    probabilistic MR atlas of the human cerebellum. NeuroImage. 2009;46(1):
    39-46. doi:10.1016/j.neuroimage.2008.11.020

Distributed by the DiedrichsenLab on GitHub
(github.com/DiedrichsenLab/cerebellar_atlases). We use the deterministic
parcellation in MNI152 symmetric space.

The cerebellum splits into 28 lobular regions (Left/Right + Vermis I-X
plus Crus I/II). For first-cut visualization we extract a single mesh
covering the whole cerebellum so the brain shell finally has its missing
anatomical hindlimb.
"""

from __future__ import annotations

import shutil
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import nibabel as nib
import numpy as np

CACHE_DIR = Path.home() / "nilearn_data" / "diedrichsen_cerebellum"
DSEG_URL = (
    "https://github.com/DiedrichsenLab/cerebellar_atlases/raw/master/"
    "Diedrichsen_2009/atl-Anatom_space-MNI_dseg.nii"
)
DSEG_NAME = "atl-Anatom_space-MNI_dseg.nii"


def _download(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    tmp.rename(dest)
    return dest


@dataclass(frozen=True, slots=True)
class CerebellumMesh:
    label: str
    voxel_count: int
    centroid_mni_mm: tuple[float, float, float]
    vertices: np.ndarray
    faces: np.ndarray


@lru_cache(maxsize=1)
def cerebellum_mesh() -> CerebellumMesh | None:
    """Extract a single triangulated mesh covering the whole cerebellum."""
    from scipy.ndimage import gaussian_filter
    from skimage import measure

    path = _download(DSEG_URL, CACHE_DIR / DSEG_NAME)
    img = nib.load(path)
    arr = np.asarray(img.dataobj)
    if arr.ndim == 4:
        arr = arr[..., 0]
    affine = img.affine
    mask = (arr > 0).astype(np.float32)
    if not mask.any():
        return None
    # Mild smoothing so the mesh isn't a stair-stepped voxel cube.
    smoothed = gaussian_filter(mask, sigma=0.8)
    verts, faces, _, _ = measure.marching_cubes(smoothed, level=0.3)
    homog = np.column_stack([verts, np.ones(len(verts))])
    mni = (affine @ homog.T).T[:, :3]

    coords = np.argwhere(mask > 0).astype(np.float64).mean(axis=0)
    centroid_homog = np.array([coords[0], coords[1], coords[2], 1.0])
    centroid_mni = (affine @ centroid_homog)[:3]

    return CerebellumMesh(
        label="Cerebellum",
        voxel_count=int(mask.sum()),
        centroid_mni_mm=(float(centroid_mni[0]), float(centroid_mni[1]), float(centroid_mni[2])),
        vertices=mni.astype(np.float32),
        faces=faces.astype(np.int32),
    )
