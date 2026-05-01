"""Yeo 2011 7-network functional parcellation of human cortex.

Reference:
    Yeo BTT, Krienen FM, Sepulcre J, Sabuncu MR, Lashkari D, Hollinshead M,
    Roffman JL, Smoller JW, Zöllei L, Polimeni JR, Fischl B, Liu H,
    Buckner RL. The organization of the human cerebral cortex estimated by
    intrinsic functional connectivity. J Neurophysiol. 2011;106(3):1125-65.
    doi:10.1152/jn.00338.2011

Seven canonical large-scale networks derived from resting-state fMRI in
1000 healthy subjects. The cortex partitions into discrete networks whose
function is well-established:
  1. Visual           — primary + extrastriate visual cortex
  2. Somatomotor      — central sulcus motor + sensory strips
  3. Dorsal Attention — top-down spatial attention (FEF, IPS)
  4. Ventral Attention — salience + reorienting (TPJ, ant. insula)
  5. Limbic           — orbitofrontal + temporal pole
  6. Frontoparietal   — executive control (dlPFC, IPL)
  7. Default Mode     — internal/self-referential thought (mPFC, PCC, AG)

This module provides per-network MNI centroids + triangulated surface
meshes (via marching cubes from the volumetric mask), so the brain shell
can be visually partitioned into 7 colored functional shells.

Per CLAUDE.md anti-theater: every voxel-label, centroid, and mesh comes
from the real Yeo 2011 NIfTI atlas (downloaded by nilearn from the original
publication's data release). Colors below are the canonical 7-network
palette used in the paper itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import nibabel as nib
import numpy as np
from nilearn import datasets

# Canonical Yeo 2011 7-network palette (from the original paper figures).
YEO_NETWORKS: tuple[dict, ...] = (
    {"id": 1, "key": "visual",            "name": "Visual",            "color": "#781285",
     "description": "Primary + extrastriate visual cortex (V1, V2, V3, V4, MT/MST). Processes seen-world information from retina via thalamus."},
    {"id": 2, "key": "somatomotor",       "name": "Somatomotor",       "color": "#4682b4",
     "description": "Pre/postcentral gyri + supplementary motor area. Voluntary movement and primary somatosensation."},
    {"id": 3, "key": "dorsal_attention",  "name": "Dorsal Attention",  "color": "#00760e",
     "description": "Top-down spatial attention. FEF + IPS. Active when directing attention to specific locations."},
    {"id": 4, "key": "ventral_attention", "name": "Ventral Attention", "color": "#c43afa",
     "description": "Salience + reorienting (TPJ, anterior insula, dACC). Detects unexpected stimuli, switches attention."},
    {"id": 5, "key": "limbic",            "name": "Limbic",            "color": "#ddcfb6",
     "description": "Orbitofrontal cortex + temporal pole. Emotion, motivation, memory-emotion integration."},
    {"id": 6, "key": "frontoparietal",    "name": "Frontoparietal",    "color": "#e69422",
     "description": "Executive control / cognitive flexibility. dlPFC + IPL + dACC. Goal-directed behavior."},
    {"id": 7, "key": "default_mode",      "name": "Default Mode",      "color": "#cd3e4e",
     "description": "Internal/self-referential thought. mPFC + PCC + angular gyrus. Active when mind is wandering, not on-task."},
)


@dataclass(frozen=True, slots=True)
class NetworkMesh:
    network_id: int
    name: str
    key: str
    color: str
    description: str
    voxel_count: int
    centroid_mni_mm: tuple[float, float, float]
    vertices: np.ndarray  # (V, 3) float32 in MNI mm
    faces: np.ndarray     # (F, 3) int32


@lru_cache(maxsize=1)
def _yeo_atlas():
    return datasets.fetch_atlas_yeo_2011()


@lru_cache(maxsize=1)
def _yeo_volume_and_affine() -> tuple[np.ndarray, np.ndarray]:
    atlas = _yeo_atlas()
    img = nib.load(atlas["maps"])
    arr = np.asarray(img.dataobj)
    if arr.ndim == 4:
        arr = arr[..., 0]
    return arr.astype(np.int16), img.affine


@lru_cache(maxsize=8)
def network_mesh(network_id: int) -> NetworkMesh | None:
    """Extract a triangulated surface mesh for one Yeo network via marching cubes."""
    from scipy.ndimage import gaussian_filter
    from skimage import measure

    spec = next((n for n in YEO_NETWORKS if n["id"] == network_id), None)
    if spec is None:
        return None
    arr, affine = _yeo_volume_and_affine()
    mask = (arr == network_id).astype(np.float32)
    if not mask.any():
        return None

    # Smooth slightly so the mesh isn't a stair-stepped voxel cube.
    smoothed = gaussian_filter(mask, sigma=0.9)
    verts, faces, _, _ = measure.marching_cubes(smoothed, level=0.3)

    # Voxel indices → MNI mm via affine.
    homog = np.column_stack([verts, np.ones(len(verts))])
    mni = (affine @ homog.T).T[:, :3]

    coords = np.argwhere(mask > 0).astype(np.float64).mean(axis=0)
    centroid_homog = np.array([coords[0], coords[1], coords[2], 1.0])
    centroid_mni = (affine @ centroid_homog)[:3]

    return NetworkMesh(
        network_id=spec["id"],
        name=spec["name"],
        key=spec["key"],
        color=spec["color"],
        description=spec["description"],
        voxel_count=int(mask.sum()),
        centroid_mni_mm=(float(centroid_mni[0]), float(centroid_mni[1]), float(centroid_mni[2])),
        vertices=mni.astype(np.float32),
        faces=faces.astype(np.int32),
    )


def all_network_meshes() -> list[NetworkMesh]:
    out: list[NetworkMesh] = []
    for spec in YEO_NETWORKS:
        m = network_mesh(spec["id"])
        if m is not None:
            out.append(m)
    return out
