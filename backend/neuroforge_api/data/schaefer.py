"""Schaefer 2018 100-region cortical parcellation.

Reference:
    Schaefer A, Kong R, Gordon EM, Laumann TO, Zuo XN, Holmes AJ,
    Eickhoff SB, Yeo BTT. Local-global parcellation of the human cerebral
    cortex from intrinsic functional connectivity MRI.
    Cereb Cortex. 2018;28(9):3095-3114. doi:10.1093/cercor/bhx179

100 cortical parcels obtained by sub-dividing the 7 Yeo 2011 networks via
local gradient + global similarity. Each parcel inherits its parent
network's tag (Vis / SomMot / DorsAttn / SalVentAttn / Limbic / Cont /
Default) plus L/R hemisphere + index. The parcellation is in MNI152
space; centroids are computed from the volumetric atlas.

Per CLAUDE.md anti-theater: every parcel's name + centroid + network
membership comes from the original Schaefer-Kong-Yeo 2018 release on
ThomasYeoLab/CBIG GitHub. No invented parcels.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import nibabel as nib
import numpy as np
from nilearn import datasets

from neuroforge_api.data.atlas import _load_atlas_image
from neuroforge_api.data.networks import YEO_NETWORKS

# Map Schaefer label fragments → Yeo network ids and colors.
NET_FRAGMENT_TO_NET_ID = {
    "Vis": 1,
    "SomMot": 2,
    "DorsAttn": 3,
    "SalVentAttn": 4,
    "Limbic": 5,
    "Cont": 6,
    "Default": 7,
}
NET_ID_TO_COLOR = {n["id"]: n["color"] for n in YEO_NETWORKS}
NET_ID_TO_NAME = {n["id"]: n["name"] for n in YEO_NETWORKS}


@dataclass(frozen=True, slots=True)
class SchaeferParcel:
    parcel_id: int
    name: str           # full Schaefer label e.g. '7Networks_LH_Vis_1'
    short_name: str     # hemi + network + index e.g. 'L Vis 1'
    hemisphere: str     # 'L' or 'R'
    network_id: int
    network_name: str
    color: str
    voxel_count: int
    centroid_mni_mm: tuple[float, float, float]


def _decode(label: object) -> str:
    if isinstance(label, bytes):
        return label.decode("utf-8", errors="replace")
    return str(label)


def _parse_short_name(full: str) -> tuple[str, int, str]:
    """Return (hemisphere, network_id, short_name) parsed from a Schaefer label."""
    # Examples: '7Networks_LH_Vis_1', '7Networks_RH_Default_5'
    parts = full.split("_")
    hemisphere = "L" if any(p == "LH" for p in parts) else "R"
    network_id = 0
    for fragment, nid in NET_FRAGMENT_TO_NET_ID.items():
        if fragment in parts:
            network_id = nid
            break
    # The short name: take the last 2 components after hemisphere
    try:
        idx = parts.index("LH") if "LH" in parts else parts.index("RH")
        rest = "_".join(parts[idx + 1 :])
    except ValueError:
        rest = full
    return hemisphere, network_id, f"{hemisphere} {rest}"


@lru_cache(maxsize=1)
def _schaefer_atlas():
    return datasets.fetch_atlas_schaefer_2018(n_rois=100, yeo_networks=7, resolution_mm=2)


@lru_cache(maxsize=1)
def schaefer_parcels() -> list[SchaeferParcel]:
    atlas = _schaefer_atlas()
    img = _load_atlas_image(atlas["maps"])
    if isinstance(img, str):
        img = nib.load(img)
    arr = np.asarray(img.dataobj)
    affine = img.affine
    # Schaefer labels include a 'Background' entry at index 0.
    out: list[SchaeferParcel] = []
    for parcel_id in range(1, len(atlas["labels"])):
        full = _decode(atlas["labels"][parcel_id])
        mask = arr == parcel_id
        if not mask.any():
            continue
        coords = np.argwhere(mask).astype(np.float64).mean(axis=0)
        homog = np.array([coords[0], coords[1], coords[2], 1.0])
        mni = (affine @ homog)[:3]
        hemi, nid, short = _parse_short_name(full)
        if nid == 0:
            continue  # safety: skip if we can't parse network
        out.append(
            SchaeferParcel(
                parcel_id=parcel_id,
                name=full,
                short_name=short,
                hemisphere=hemi,
                network_id=nid,
                network_name=NET_ID_TO_NAME[nid],
                color=NET_ID_TO_COLOR[nid],
                voxel_count=int(mask.sum()),
                centroid_mni_mm=(float(mni[0]), float(mni[1]), float(mni[2])),
            )
        )
    return out
