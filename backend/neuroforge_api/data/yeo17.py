"""Yeo 2011 17-network functional parcellation of human cortex.

Reference:
    Yeo BTT, Krienen FM, Sepulcre J, Sabuncu MR, Lashkari D, Hollinshead M,
    Roffman JL, Smoller JW, Zöllei L, Polimeni JR, Fischl B, Liu H,
    Buckner RL. The organization of the human cerebral cortex estimated by
    intrinsic functional connectivity. J Neurophysiol. 2011;106(3):1125-65.
    doi:10.1152/jn.00338.2011

Finer-grained 17-network solution from the same paper (the 7-network result
is a coarser clustering of the same data). The 17-network split separates,
for example, central vs peripheral visual, and partitions the Default Mode
into A/B/C subnetworks with distinct functional roles.

This module loads the Yeo 17-network volumetric atlas (already cached on
disk by nilearn at fetch time of the 7-network atlas — they ship together
in the same release tarball: `Yeo2011_17Networks_MNI152_FreeSurferConformed1mm.nii.gz`)
and extracts a triangulated surface mesh for each network via marching cubes.

Per CLAUDE.md anti-theater: every voxel-label, centroid, color, and mesh
comes from the real Yeo 2011 NIfTI atlas + its bundled ColorLUT.txt.
Network names are the canonical labels published in Yeo 2011 Figure 9
and used by every subsequent paper that cites this atlas.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import nibabel as nib
import numpy as np
from nilearn import datasets

# The 17-network volumetric atlas ships in the same nilearn yeo_2011 cache
# directory as the 7-network volume. Filename is fixed (defined in the
# original Yeo 2011 release).
_YEO17_VOLUME_NAME = "Yeo2011_17Networks_MNI152_FreeSurferConformed1mm.nii.gz"
_YEO17_LUT_NAME = "Yeo2011_17Networks_ColorLUT.txt"

# Canonical Yeo 2011 17-network names (from Yeo 2011 Figure 9 / paper text).
# Each is a subdivision of one of the 7 parent networks.
YEO17_NAMES: tuple[tuple[int, str, str, str], ...] = (
    # (network_id, short_name, full_name, parent_network)
    (1,  "VisCent",     "Visual Central",                    "Visual"),
    (2,  "VisPeri",     "Visual Peripheral",                 "Visual"),
    (3,  "SomMotA",     "Somatomotor A (dorsal)",            "Somatomotor"),
    (4,  "SomMotB",     "Somatomotor B (ventral)",           "Somatomotor"),
    (5,  "DorsAttnA",   "Dorsal Attention A (FEF/IPS)",      "Dorsal Attention"),
    (6,  "DorsAttnB",   "Dorsal Attention B (postcentral)",  "Dorsal Attention"),
    (7,  "SalVentAttnA","Salience / Ventral Attention A",    "Ventral Attention"),
    (8,  "SalVentAttnB","Salience / Ventral Attention B",    "Ventral Attention"),
    (9,  "LimbicA",     "Limbic A (Temporal Pole)",          "Limbic"),
    (10, "LimbicB",     "Limbic B (Orbitofrontal)",          "Limbic"),
    (11, "ContA",       "Control A (parietal)",              "Frontoparietal"),
    (12, "ContB",       "Control B (lateral PFC)",           "Frontoparietal"),
    (13, "ContC",       "Control C (cingulate)",             "Frontoparietal"),
    (14, "DefaultA",    "Default Mode A (mPFC/PCC core)",    "Default Mode"),
    (15, "DefaultB",    "Default Mode B (dlPFC/IPL)",        "Default Mode"),
    (16, "DefaultC",    "Default Mode C (RSC/parahipp.)",    "Default Mode"),
    (17, "TempPar",     "Temporo-Parietal",                  "Default Mode"),
)


@dataclass(frozen=True, slots=True)
class Yeo17Network:
    network_id: int
    short_name: str
    full_name: str
    parent_network: str
    color: str  # hex
    voxel_count: int
    centroid_mni_mm: tuple[float, float, float]
    vertices: np.ndarray  # (V, 3) float32 in MNI mm
    faces: np.ndarray     # (F, 3) int32


@lru_cache(maxsize=1)
def _yeo17_paths() -> tuple[Path, Path]:
    """Trigger nilearn fetch (which downloads the Yeo 2011 release tarball
    containing both 7- and 17-network volumes), then locate the 17-net file."""
    fetched = datasets.fetch_atlas_yeo_2011()  # ensures download / cache
    # nilearn's bunch exposes the 7-network volume as "maps"; the 17-network file sits in
    # the same release directory. Derive it from the fetched path so this
    # honours NILEARN_DATA / custom data_dir instead of a hardcoded ~ path.
    cache_dir = Path(str(fetched["maps"])).parent
    vol = cache_dir / _YEO17_VOLUME_NAME
    lut = cache_dir / _YEO17_LUT_NAME
    if not vol.exists():
        raise FileNotFoundError(f"Yeo17 volume not found at {vol}")
    if not lut.exists():
        raise FileNotFoundError(f"Yeo17 LUT not found at {lut}")
    return vol, lut


@lru_cache(maxsize=1)
def _yeo17_volume_and_affine() -> tuple[np.ndarray, np.ndarray]:
    vol_path, _ = _yeo17_paths()
    img = nib.load(str(vol_path))
    arr = np.asarray(img.dataobj)
    if arr.ndim == 4:
        arr = arr[..., 0]
    return arr.astype(np.int16), img.affine


@lru_cache(maxsize=1)
def _yeo17_colors() -> dict[int, str]:
    """Parse the bundled Yeo2011_17Networks_ColorLUT.txt for per-network RGB."""
    _, lut_path = _yeo17_paths()
    out: dict[int, str] = {}
    for line in lut_path.read_text().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            idx = int(parts[0])
            r, g, b = int(parts[2]), int(parts[3]), int(parts[4])
        except ValueError:
            continue
        if idx == 0:
            continue
        out[idx] = f"#{r:02x}{g:02x}{b:02x}"
    return out


@lru_cache(maxsize=32)
def network_mesh(network_id: int) -> Yeo17Network | None:
    """Extract a triangulated surface mesh for one Yeo17 network via marching cubes."""
    from scipy.ndimage import gaussian_filter
    from skimage import measure

    spec = next((n for n in YEO17_NAMES if n[0] == network_id), None)
    if spec is None:
        return None
    arr, affine = _yeo17_volume_and_affine()
    mask = (arr == network_id).astype(np.float32)
    if not mask.any():
        return None

    smoothed = gaussian_filter(mask, sigma=0.9)
    verts, faces, _, _ = measure.marching_cubes(smoothed, level=0.3)

    homog = np.column_stack([verts, np.ones(len(verts))])
    mni = (affine @ homog.T).T[:, :3]

    coords = np.argwhere(mask > 0).astype(np.float64).mean(axis=0)
    centroid_homog = np.array([coords[0], coords[1], coords[2], 1.0])
    centroid_mni = (affine @ centroid_homog)[:3]

    color = _yeo17_colors().get(network_id, "#888888")

    return Yeo17Network(
        network_id=spec[0],
        short_name=spec[1],
        full_name=spec[2],
        parent_network=spec[3],
        color=color,
        voxel_count=int(mask.sum()),
        centroid_mni_mm=(float(centroid_mni[0]), float(centroid_mni[1]), float(centroid_mni[2])),
        vertices=mni.astype(np.float32),
        faces=faces.astype(np.int32),
    )


def all_yeo17_networks() -> list[Yeo17Network]:
    out: list[Yeo17Network] = []
    for spec in YEO17_NAMES:
        m = network_mesh(spec[0])
        if m is not None:
            out.append(m)
    return out
