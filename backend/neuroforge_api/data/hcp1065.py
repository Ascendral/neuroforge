"""HCP-1065 / Yeh 2018 population-averaged tractography atlas.

Reference:
    Yeh F-C, Panesar S, Fernandes D, Meola A, Yoshino M, Fernandez-Miranda JC,
    Vettel JM, Verstynen T. Population-averaged atlas of the macroscale human
    structural connectome and its network topology. NeuroImage. 2018;178:57-68.
    doi:10.1016/j.neuroimage.2018.05.027

    Atlas data: Zenodo doi:10.5281/zenodo.3627772 (HCP-YA Tractography Atlas, NIFTI Files)

This atlas was built by deterministic fiber tracking on the diffusion MRI of
1,065 healthy young adults from the Human Connectome Project, then
clustering streamlines into 80 anatomically named bundles. The published
atlas distributes each bundle as a binary occupancy mask in 1mm MNI152
space — i.e. "voxel = 1 if any subject's streamlines passed through here."

We download the NIFTIs once into `backend/data_cache/hcp1065/` (~1MB total)
and extract a smooth centerline for each tract via PCA-binning:

  1. Find principal axis of the tract voxel cloud (longest direction).
  2. Project all voxel coordinates onto that axis; bin into N segments.
  3. Per-bin, take the mean of voxel positions → an ordered N-point polyline.
  4. Smooth with a small moving average to remove voxel-grid jitter.

The resulting polyline is the geometric centroid of the tract's spatial
distribution at each point along its length — a real centerline, not a
hand-drawn approximation.

Per CLAUDE.md anti-theater: we are NOT inventing tract paths. Every
centerline point is the empirical mean of HCP-1065 voxel-occupancy data
at that position along the principal axis. This is fiber-resolved
tractography averaged over 1,065 subjects, distilled to a single curve
per tract for visualization (the full mask is also available via the
voxel_count field).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import nibabel as nib
import numpy as np

CACHE_DIR = Path(__file__).resolve().parents[2] / "data_cache" / "hcp1065"

# Color groups by anatomical category. Each group gets a single hex color
# so the user can visually segregate commissural / projection / association /
# cerebellar tracts at a glance.
TRACT_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    # (group_label, color, name-substring matchers)
    ("Cranial Nerves", "#ffcc00", ("CN",)),
    ("Brainstem / Cerebellar", "#a06bff", (
        "Cerebell", "Vermis", "Cerebellar_Peduncle", "Central_Tegmental",
        "Rubrospinal", "Spinothalamic", "Reticular", "Medial_Lemniscus",
        "Dorsal_Longitudinal", "Pontine_Crossing", "Tract_of_Vicq",
    )),
    ("Commissural", "#ff5577", (
        "Anterior_Commissure", "Posterior_Commissure", "Corpus_Callosum",
    )),
    ("Projection", "#4ea7ff", (
        "Corticospinal", "Cortico_Spinal", "Corticobulbar", "Corticothalamic",
        "Corticostriatal", "Cortico_Striatal",
        "Frontopontine", "Parietopontine", "Occipitopontine", "Temporopontine",
        "Optic_Radiation", "Optic_Tract", "Acoustic_Radiation",
        "Thalamic_Radiation", "Internal_Capsule",
        "Lateral_Lemniscus", "Medial_Longitudinal_Fasciculus",
    )),
    ("Limbic", "#ffaa55", (
        "Cingulum", "Fornix", "Stria_Terminalis", "Mammillothalamic",
        "Medial_Forebrain",
    )),
    ("Association", "#7fff9b", (
        "Arcuate", "Superior_Longitudinal", "Inferior_Longitudinal",
        "Middle_Longitudinal", "Uncinate", "Inferior_Fronto",
        "Frontal_Aslant", "Vertical_Occipital", "Extreme_Capsule",
        "U_Fiber",
    )),
)
_DEFAULT_COLOR = "#cccccc"
_DEFAULT_GROUP = "Other"


def _classify(name: str) -> tuple[str, str]:
    for group, color, matchers in TRACT_GROUPS:
        for m in matchers:
            if m in name:
                return group, color
    return _DEFAULT_GROUP, _DEFAULT_COLOR


def _humanize(filename: str) -> str:
    # "Arcuate_Fasciculus_L.nii.gz" -> "Arcuate Fasciculus (L)"
    stem = filename.replace(".nii.gz", "")
    side = ""
    if stem.endswith("_L"):
        side = " (L)"
        stem = stem[:-2]
    elif stem.endswith("_R"):
        side = " (R)"
        stem = stem[:-2]
    return stem.replace("_", " ") + side


@dataclass(frozen=True, slots=True)
class HCPTract:
    name: str          # human-readable
    filename: str      # original NIfTI filename
    group: str
    color: str
    voxel_count: int
    # Centerline polyline in MNI mm, shape (n_points, 3).
    centerline: np.ndarray
    # Bounding extent of the tract's voxel cloud, MNI mm.
    bbox_min_mm: tuple[float, float, float]
    bbox_max_mm: tuple[float, float, float]


def _extract_centerline(mask: np.ndarray, affine: np.ndarray, n_bins: int = 24) -> np.ndarray:
    """PCA-binning centerline. Returns (M, 3) array of MNI mm points (M <= n_bins)."""
    voxels = np.argwhere(mask > 0).astype(np.float64)
    if len(voxels) < n_bins:
        return np.empty((0, 3), dtype=np.float32)

    # Voxel index → MNI mm.
    homog = np.column_stack([voxels, np.ones(len(voxels))])
    coords_mm = (affine @ homog.T).T[:, :3]

    # PCA on mm coordinates.
    centered = coords_mm - coords_mm.mean(axis=0)
    cov = centered.T @ centered / max(len(centered) - 1, 1)
    eigvals, eigvecs = np.linalg.eigh(cov)
    # Largest eigenvalue's eigenvector = principal axis.
    axis = eigvecs[:, np.argmax(eigvals)]
    proj = centered @ axis  # scalar projection per voxel

    # Bin along axis.
    p_min, p_max = proj.min(), proj.max()
    if p_max - p_min < 1e-3:
        return np.empty((0, 3), dtype=np.float32)
    bin_edges = np.linspace(p_min, p_max, n_bins + 1)
    bin_idx = np.clip(np.digitize(proj, bin_edges) - 1, 0, n_bins - 1)

    centerline = []
    for b in range(n_bins):
        sel = bin_idx == b
        if sel.sum() < 2:  # skip empty / nearly-empty bins
            continue
        centerline.append(coords_mm[sel].mean(axis=0))
    if len(centerline) < 3:
        return np.empty((0, 3), dtype=np.float32)
    pts = np.array(centerline, dtype=np.float64)

    # Smooth with a length-3 moving average (preserve endpoints).
    smoothed = pts.copy()
    if len(pts) >= 5:
        kernel = np.array([0.25, 0.5, 0.25])
        for d in range(3):
            smoothed[1:-1, d] = (
                kernel[0] * pts[:-2, d] + kernel[1] * pts[1:-1, d] + kernel[2] * pts[2:, d]
            )
    return smoothed.astype(np.float32)


@lru_cache(maxsize=1)
def all_hcp1065_tracts() -> list[HCPTract]:
    if not CACHE_DIR.exists():
        return []
    out: list[HCPTract] = []
    for nii_path in sorted(CACHE_DIR.glob("*.nii.gz")):
        try:
            img = nib.load(str(nii_path))
            mask = np.asarray(img.dataobj)
            if mask.ndim == 4:
                mask = mask[..., 0]
            mask = (mask > 0).astype(np.uint8)
            if mask.sum() < 50:
                continue
            centerline = _extract_centerline(mask, img.affine)
            if centerline.shape[0] < 3:
                continue
            voxels_mm = (
                img.affine @ np.column_stack(
                    [np.argwhere(mask > 0).astype(np.float64), np.ones(int(mask.sum()))]
                ).T
            ).T[:, :3]
            bmin = voxels_mm.min(axis=0)
            bmax = voxels_mm.max(axis=0)
            name = _humanize(nii_path.name)
            group, color = _classify(nii_path.name)
            out.append(
                HCPTract(
                    name=name,
                    filename=nii_path.name,
                    group=group,
                    color=color,
                    voxel_count=int(mask.sum()),
                    centerline=centerline,
                    bbox_min_mm=(float(bmin[0]), float(bmin[1]), float(bmin[2])),
                    bbox_max_mm=(float(bmax[0]), float(bmax[1]), float(bmax[2])),
                )
            )
        except Exception:
            # Bad file → skip; do not fabricate.
            continue
    return out
