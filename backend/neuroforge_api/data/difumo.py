"""DiFuMo functional dictionary atlas (Dadi et al. 2020).

Reference:
    Dadi K, Varoquaux G, Machlouzarides-Shalit A, Gorgolewski KJ,
    Wassermann D, Thirion B, Mensch A. Fine-grain atlases of functional
    modes for fMRI analysis. NeuroImage. 2020;221:117126.
    doi:10.1016/j.neuroimage.2020.117126

64-component dictionary learned from 2,192 healthy-subject fMRI scans
(HCP, OASIS, Connectome). Each component is a probabilistic map of a
'functional mode' — a coactivating brain region with a human-readable
name (e.g. 'Superior frontal sulcus', 'Calcarine cortex posterior').
Each component is also tagged with its dominant Yeo 7-network membership.

We compute the centroid of each component and render as a sphere with
the Yeo network color. The plain-language `difumo_name` becomes the
region label.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import nibabel as nib
import numpy as np
from nilearn import datasets

from neuroforge_api.data.networks import YEO_NETWORKS

# Map DiFuMo's Yeo7 names → our network ids (DiFuMo uses different name
# strings than Yeo's atlas labels — this is the documented crosswalk).
DIFUMO_TO_YEO_ID = {
    "VisCent": 1, "VisPeri": 1,
    "SomMotA": 2, "SomMotB": 2,
    "DorsAttnA": 3, "DorsAttnB": 3,
    "SalVentAttnA": 4, "SalVentAttnB": 4,
    "LimbicA": 5, "LimbicB": 5, "Limbic": 5,
    "ContA": 6, "ContB": 6, "ContC": 6,
    "DefaultA": 7, "DefaultB": 7, "DefaultC": 7,
}
NET_ID_TO_COLOR = {n["id"]: n["color"] for n in YEO_NETWORKS}
NET_ID_TO_NAME = {n["id"]: n["name"] for n in YEO_NETWORKS}

NO_NETWORK_COLOR = "#777777"


@dataclass(frozen=True, slots=True)
class DifumoComponent:
    component_id: int
    name: str            # e.g. "Superior frontal sulcus"
    yeo_network_id: int  # 0 if no clear network
    yeo_network_name: str
    color: str
    voxel_count: int
    centroid_mni_mm: tuple[float, float, float]


@lru_cache(maxsize=1)
def difumo_components() -> list[DifumoComponent]:
    atlas = datasets.fetch_atlas_difumo(dimension=64, resolution_mm=2)
    img = atlas["maps"]
    if isinstance(img, str):
        img = nib.load(img)
    arr = np.asarray(img.dataobj)  # (X, Y, Z, n_components)
    affine = img.affine
    labels_df = atlas["labels"]

    out: list[DifumoComponent] = []
    for c in range(arr.shape[3]):
        comp = arr[..., c]
        # Use a mild threshold to define the component's spatial support.
        thresh = max(comp.max() * 0.25, 1e-6) if comp.max() > 0 else 1.0
        mask = comp > thresh
        if not mask.any():
            continue
        # Probability-weighted centroid for accuracy.
        coords = np.argwhere(mask).astype(np.float64)
        weights = comp[mask].astype(np.float64)
        if weights.sum() == 0:
            continue
        centroid = (coords * weights[:, None]).sum(axis=0) / weights.sum()
        homog = np.array([centroid[0], centroid[1], centroid[2], 1.0])
        mni = (affine @ homog)[:3]

        row = labels_df.iloc[c]
        name = str(row.get("difumo_names", f"Component {c + 1}"))
        yeo_str = str(row.get("yeo_networks7", "")).strip()
        net_id = DIFUMO_TO_YEO_ID.get(yeo_str, 0)
        net_name = NET_ID_TO_NAME.get(net_id, "no network")
        color = NET_ID_TO_COLOR.get(net_id, NO_NETWORK_COLOR)

        out.append(
            DifumoComponent(
                component_id=c + 1,
                name=name,
                yeo_network_id=net_id,
                yeo_network_name=net_name,
                color=color,
                voxel_count=int(mask.sum()),
                centroid_mni_mm=(float(mni[0]), float(mni[1]), float(mni[2])),
            )
        )
    return out
