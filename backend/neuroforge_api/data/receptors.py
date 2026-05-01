"""Hansen 2022 neurotransmitter receptor PET maps.

Reference (umbrella citation):
    Hansen JY et al. Mapping neurotransmitter systems to the structural
    and functional organization of the human neocortex.
    Nat Neurosci. 2022;25(11):1569-1581.
    doi:10.1038/s41593-022-01186-3
    Data: github.com/netneurolab/hansen_receptors

Each NIfTI volume below is the averaged PET signal in MNI152 space across
the cited tracer study. We pick small (≤ 2 MB) versions for fast first-run
download. nibabel loads them; we resample to the Harvard-Oxford atlas
resolution and compute the mean signal within each region's mask.

Per CLAUDE.md anti-theater: we do not synthesize, average across tracers
silently, or pretend a tracer maps to a different receptor than its
binding site. Each entry's `tracer` field names the actual radioligand;
each entry's `n_subjects` is the headcount in the original study.
"""

from __future__ import annotations

import shutil
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import nibabel as nib
import numpy as np
from nilearn.image import resample_to_img

from neuroforge_api.data.atlas import (
    _load_atlas_image,
    harvard_oxford_cortical_atlas,
    harvard_oxford_subcortical_atlas,
)

CACHE_DIR = Path.home() / "nilearn_data" / "hansen_receptors_cache"


@dataclass(frozen=True, slots=True)
class ReceptorEntry:
    key: str           # short stable id
    name: str          # human-readable name
    system: str        # e.g. "dopamine", "serotonin", "GABA"
    tracer: str
    n_subjects: int
    url: str
    citation: str


RECEPTORS: tuple[ReceptorEntry, ...] = (
    ReceptorEntry(
        key="D1",
        name="Dopamine D1 receptor",
        system="dopamine",
        tracer="[11C]SCH23390",
        n_subjects=13,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/D1_SCH23390_hc13_kaller.nii",
        citation="Kaller S et al. Test-retest measurements of dopamine D1-type receptors. Eur J Nucl Med Mol Imaging. 2017. Aggregated in Hansen 2022, doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="D2",
        name="Dopamine D2 receptor",
        system="dopamine",
        tracer="[11C]raclopride",
        n_subjects=7,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/D2_raclopride_hc7_alakurtti.nii",
        citation="Alakurtti K et al. Long-term test-retest reliability of striatal and extrastriatal dopamine D2/3 receptor binding. J Cereb Blood Flow Metab. 2015. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="DAT",
        name="Dopamine transporter",
        system="dopamine",
        tracer="[123I]FP-CIT (SPECT)",
        n_subjects=174,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/DAT_fpcit_hc174_dukart_spect.nii",
        citation="Dukart J et al. Cerebral blood flow predicts differential neurotransmitter activity. Sci Rep. 2018. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="5HT1a",
        name="Serotonin 5-HT1A receptor",
        system="serotonin",
        tracer="[11C]WAY-100635",
        n_subjects=36,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/5HT1a_way_hc36_savli.nii",
        citation="Savli M et al. Normative database of the serotonergic system in healthy subjects. NeuroImage. 2012. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="5HT2a",
        name="Serotonin 5-HT2A receptor",
        system="serotonin",
        tracer="[11C]MDL-100907",
        n_subjects=19,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/5HT2a_alt_hc19_savli.nii",
        citation="Savli M et al. NeuroImage. 2012. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="5HTT",
        name="Serotonin transporter",
        system="serotonin",
        tracer="[11C]DASB",
        n_subjects=30,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/5HTT_dasb_hc30_savli.nii",
        citation="Savli M et al. NeuroImage. 2012. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="GABAa",
        name="GABA-A receptor (benzodiazepine site)",
        system="GABA",
        tracer="[11C]flumazenil",
        n_subjects=6,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/GABAa_flumazenil_hc6_dukart.nii",
        citation="Dukart J et al. Sci Rep. 2018. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="MU",
        name="Mu-opioid receptor",
        system="opioid",
        tracer="[11C]carfentanil",
        n_subjects=204,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/MU_carfentanil_hc204_kantonen.nii",
        citation="Kantonen T et al. Interindividual variability and lateralization of mu-opioid receptors in the human brain. NeuroImage. 2020. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
)


def _download(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with urllib.request.urlopen(url, timeout=60) as response, open(tmp, "wb") as f:
        shutil.copyfileobj(response, f)
    tmp.rename(dest)
    return dest


def _local_path(receptor: ReceptorEntry) -> Path:
    fname = receptor.url.rsplit("/", 1)[-1]
    return CACHE_DIR / fname


@lru_cache(maxsize=32)
def _per_region_mean_for(
    receptor_key: str,
    atlas_kind: str,
) -> dict[int, float]:
    """Compute mean PET intensity within each HO region for one receptor.

    Returns {label_id: mean_value}. label_id 0 (background) is excluded.
    """
    receptor = next((r for r in RECEPTORS if r.key == receptor_key), None)
    if receptor is None:
        raise ValueError(f"unknown receptor: {receptor_key}")
    if atlas_kind == "cortical":
        atlas = harvard_oxford_cortical_atlas()
    elif atlas_kind == "subcortical":
        atlas = harvard_oxford_subcortical_atlas()
    else:
        raise ValueError("atlas_kind must be 'cortical' or 'subcortical'")

    pet_path = _download(receptor.url, _local_path(receptor))
    pet_img = nib.load(pet_path)
    atlas_img = _load_atlas_image(atlas["maps"])

    # Resample PET volume to atlas resolution+affine.
    pet_resampled = resample_to_img(pet_img, atlas_img, interpolation="linear")

    pet_data = np.asarray(pet_resampled.dataobj)
    atlas_data = np.asarray(atlas_img.dataobj)
    # If 4D, take first volume.
    if pet_data.ndim == 4:
        pet_data = pet_data[..., 0]

    out: dict[int, float] = {}
    for label_id in range(1, len(atlas["labels"])):
        mask = atlas_data == label_id
        if not mask.any():
            continue
        vals = pet_data[mask]
        # Replace NaNs with 0 for the average; report 0 if entirely missing.
        vals = vals[~np.isnan(vals)]
        if vals.size == 0:
            out[label_id] = 0.0
        else:
            out[label_id] = float(vals.mean())
    return out


def receptor_per_region(receptor_key: str) -> dict[str, list[dict]]:
    """Public API: returns per-region means + normalized 0-1 intensity.

    Output: {"cortical": [{label, mean, normalized}, ...], "subcortical": [...]}
    """
    out: dict[str, list[dict]] = {"cortical": [], "subcortical": []}
    for kind in ("cortical", "subcortical"):
        means = _per_region_mean_for(receptor_key, kind)
        atlas = (
            harvard_oxford_cortical_atlas() if kind == "cortical" else harvard_oxford_subcortical_atlas()
        )
        labels = atlas["labels"]
        # Normalize to [0,1] across this atlas
        if means:
            mn = min(means.values())
            mx = max(means.values())
            span = (mx - mn) if mx > mn else 1.0
        else:
            mn, span = 0.0, 1.0
        for lid, m in sorted(means.items()):
            normalized = float((m - mn) / span)
            out[kind].append({
                "label": labels[lid],
                "mean": float(m),
                "normalized": normalized,
            })
    return out
