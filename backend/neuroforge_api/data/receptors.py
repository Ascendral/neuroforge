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
    role: str          # plain-language: what does this receptor DO?
    pharmacology: str  # plain-language: which drugs target it?


RECEPTORS: tuple[ReceptorEntry, ...] = (
    ReceptorEntry(
        key="D1",
        name="Dopamine D1 receptor",
        system="dopamine",
        role="Excitatory dopamine receptor — when dopamine binds, the target neuron's activity goes UP. Dominates the 'direct pathway' of basal ganglia, which promotes movement and reward-driven action.",
        pharmacology="Targeted by some experimental cognition-enhancers; reduced binding seen in Parkinson's disease and schizophrenia.",
        tracer="[11C]SCH23390",
        n_subjects=13,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/D1_SCH23390_hc13_kaller.nii",
        citation="Kaller S et al. Test-retest measurements of dopamine D1-type receptors. Eur J Nucl Med Mol Imaging. 2017. Aggregated in Hansen 2022, doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="D2",
        name="Dopamine D2 receptor",
        system="dopamine",
        role="Inhibitory dopamine receptor — when dopamine binds, the target neuron's activity goes DOWN. Dominates the 'indirect pathway' of basal ganglia (movement suppression). Densest in striatum.",
        pharmacology="MAIN TARGET of all antipsychotics (haloperidol, olanzapine, risperidone). Also blocked by metoclopramide. Stimulated by L-DOPA's metabolites.",
        tracer="[11C]raclopride",
        n_subjects=7,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/D2_raclopride_hc7_alakurtti.nii",
        citation="Alakurtti K et al. Long-term test-retest reliability of striatal and extrastriatal dopamine D2/3 receptor binding. J Cereb Blood Flow Metab. 2015. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="DAT",
        name="Dopamine transporter",
        system="dopamine",
        role="Pumps dopamine BACK into the neuron after release, ending the signal. Highest density in striatum (where dopamine release is dense).",
        pharmacology="Blocked by COCAINE and AMPHETAMINE — they prevent dopamine reuptake, raising synaptic dopamine. Also blocked by methylphenidate (Ritalin). Reduced binding is the gold-standard imaging marker for Parkinson's disease.",
        tracer="[123I]FP-CIT (SPECT)",
        n_subjects=174,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/DAT_fpcit_hc174_dukart_spect.nii",
        citation="Dukart J et al. Cerebral blood flow predicts differential neurotransmitter activity. Sci Rep. 2018. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="5HT1a",
        name="Serotonin 5-HT1A receptor",
        system="serotonin",
        role="Inhibitory serotonin receptor. On serotonin neurons themselves it acts as an autoreceptor — silencing the neuron when serotonin levels rise (negative feedback). Densest in raphe nuclei + hippocampus.",
        pharmacology="Targeted by buspirone (Buspar, anxiety) and vilazodone. Partial agonism here is one mechanism of newer antidepressants.",
        tracer="[11C]WAY-100635",
        n_subjects=36,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/5HT1a_way_hc36_savli.nii",
        citation="Savli M et al. Normative database of the serotonergic system in healthy subjects. NeuroImage. 2012. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="5HT2a",
        name="Serotonin 5-HT2A receptor",
        system="serotonin",
        role="Excitatory serotonin receptor in cortex (especially layer 5 pyramidals). Strongly modulates perception, mood, and cognition.",
        pharmacology="ACTIVATED BY classic psychedelics: LSD, psilocybin (mushrooms), DMT, mescaline — their hallucinogenic effect is via this receptor. BLOCKED by atypical antipsychotics (clozapine, olanzapine, quetiapine) — this is part of why they cause less motor side-effect than D2-only blockers.",
        tracer="[11C]MDL-100907",
        n_subjects=19,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/5HT2a_alt_hc19_savli.nii",
        citation="Savli M et al. NeuroImage. 2012. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="5HTT",
        name="Serotonin transporter",
        system="serotonin",
        role="Pumps serotonin back into the neuron after release. Densest in raphe nuclei + thalamus + striatum. Sets baseline serotonin tone in cortex.",
        pharmacology="THE TARGET of SSRIs: fluoxetine (Prozac), sertraline (Zoloft), citalopram (Celexa), escitalopram (Lexapro), paroxetine (Paxil). Also blocked by MDMA (releases serotonin in addition to blocking reuptake).",
        tracer="[11C]DASB",
        n_subjects=30,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/5HTT_dasb_hc30_savli.nii",
        citation="Savli M et al. NeuroImage. 2012. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="GABAa",
        name="GABA-A receptor (benzodiazepine site)",
        system="GABA",
        role="The MAIN INHIBITORY receptor in the brain. When GABA binds, chloride flows in and the neuron's activity drops. The brain's brake pedal — without it, runaway excitation = seizures.",
        pharmacology="Enhanced by BENZODIAZEPINES (diazepam, alprazolam, lorazepam) — they don't activate it directly but boost GABA's effect (anxiolytic, sedative, anticonvulsant). Also enhanced by ALCOHOL, barbiturates, propofol, zolpidem (Ambien). General anesthetics work mostly here.",
        tracer="[11C]flumazenil",
        n_subjects=6,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/GABAa_flumazenil_hc6_dukart.nii",
        citation="Dukart J et al. Sci Rep. 2018. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="MU",
        name="Mu-opioid receptor",
        system="opioid",
        role="Inhibitory receptor that produces analgesia, euphoria, and respiratory depression when activated. The brain's natural endorphins and enkephalins act here. Densest in striatum, thalamus, brainstem.",
        pharmacology="THE TARGET of MORPHINE, heroin, fentanyl, oxycodone, methadone, codeine. Activation = pain relief + euphoria + addiction risk + respiratory depression (cause of overdose deaths). Blocked by naloxone (Narcan, opioid-overdose reversal) and naltrexone (addiction treatment).",
        tracer="[11C]carfentanil",
        n_subjects=204,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/MU_carfentanil_hc204_kantonen.nii",
        citation="Kantonen T et al. Interindividual variability and lateralization of mu-opioid receptors in the human brain. NeuroImage. 2020. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="FDOPA",
        name="L-DOPA uptake (dopamine synthesis)",
        system="dopamine",
        role="Not strictly a receptor — measures the rate at which the brain TAKES UP L-DOPA and converts it to dopamine. A direct map of dopamine SYNTHESIS capacity. Densest in striatum where dopamine terminals from SNc/VTA project.",
        pharmacology="The same molecular pathway L-DOPA (Sinemet) uses to treat Parkinson's: oral L-DOPA crosses the blood-brain barrier, gets converted to dopamine inside surviving neurons. Reduced FDOPA uptake = degeneration of dopamine neurons.",
        tracer="[18F]fluorodopa",
        n_subjects=12,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/FDOPA_fluorodopa_hc12_gomez.nii",
        citation="García-Gómez FJ, García-Solís D, Luis-Simón FJ, et al. Elaboración de una plantilla de SPM para la normalización de imágenes de PET con 18F-DOPA. Imagen Diagnóstica. 2018;9(1). doi:10.33588/imagendiagnostica.901.2 (healthy-control template, n=12); distributed via Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="NET",
        name="Norepinephrine transporter",
        system="norepinephrine",
        role="Pumps norepinephrine back into the neuron after release. Densest in thalamus, locus coeruleus, and cortex. Sets baseline arousal/attention tone via the ascending noradrenergic system.",
        pharmacology="THE TARGET of SNRIs (venlafaxine/Effexor, duloxetine/Cymbalta) and atomoxetine (Strattera, non-stimulant ADHD treatment). Also blocked by tricyclic antidepressants and amphetamine.",
        tracer="[11C]MRB",
        n_subjects=10,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/NAT_MRB_hc10_hesse.nii",
        citation="Hesse S, Becker GA, Rullmann M, et al. Central noradrenaline transporter availability in highly obese, non-depressed individuals. Eur J Nucl Med Mol Imaging. 2017;44(6):1056-1064. doi:10.1007/s00259-016-3590-3 (healthy-control map, n=10); distributed via Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="CB1",
        name="Cannabinoid CB1 receptor",
        system="cannabinoid",
        role="Inhibitory receptor — when activated, suppresses neurotransmitter release at the presynaptic terminal. The brain's natural anandamide and 2-AG act here. Densest in cortex, hippocampus, basal ganglia, cerebellum (fewer in brainstem — that's why cannabis isn't lethal in overdose).",
        pharmacology="THE TARGET of THC (cannabis/marijuana) — that's how it produces its psychoactive effects. Also activated by synthetic cannabinoids (K2/Spice). Blocked by rimonabant (withdrawn drug for obesity due to depression side effects).",
        tracer="[11C]FMPEP-d2",
        n_subjects=22,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/CB1_FMPEPd2_hc22_laurikainen.nii",
        citation="Laurikainen H et al. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="A4B2",
        name="Nicotinic ACh α4β2 receptor",
        system="acetylcholine",
        role="Excitatory ionotropic acetylcholine receptor (the most common nicotinic subtype in brain). Modulates attention, memory, and reward-related dopamine release. Densest in thalamus + cortex.",
        pharmacology="THE TARGET of NICOTINE — the chief reason cigarettes are addictive (activation here in the VTA → triggers dopamine release in NAC). Also activated by varenicline (Chantix, smoking cessation) as a partial agonist. Reduced expression in Alzheimer's disease.",
        tracer="[18F]flubatine",
        n_subjects=30,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/A4B2_flubatine_hc30_hillmer.nii.gz",
        citation="Hillmer AT et al. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="M1",
        name="Muscarinic ACh M1 receptor",
        system="acetylcholine",
        role="Excitatory metabotropic acetylcholine receptor in cortex + hippocampus + striatum. Critical for learning and memory; activation enhances cortical pyramidal cell firing.",
        pharmacology="Blocked by atropine and scopolamine (both cause confusion + amnesia — anti-cholinergic delirium). Also blocked by many antidepressants (TCAs) and antihistamines (Benadryl) — explains their cognitive side effects. M1 agonists are an Alzheimer's treatment target (xanomeline + KarXT).",
        tracer="[11C]LSN3172176",
        n_subjects=24,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/M1_lsn_hc24_naganawa.nii.gz",
        citation="Naganawa M et al. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="NMDA",
        name="NMDA glutamate receptor",
        system="glutamate",
        role="Excitatory ionotropic glutamate receptor — the molecular substrate of LONG-TERM POTENTIATION (LTP), the cellular basis of learning and memory. Densest in hippocampus + cortex. Coincidence detector: needs both glutamate AND postsynaptic depolarization to open.",
        pharmacology="BLOCKED by KETAMINE (anesthetic + rapid antidepressant), PCP (angel dust), dextromethorphan, and memantine (Namenda, Alzheimer's treatment). Excessive activation causes excitotoxic cell death — major mechanism of stroke damage.",
        tracer="[18F]GE-179",
        n_subjects=29,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/NMDA_ge179_hc29_galovic.nii.gz",
        citation="Galovic M et al. Hansen 2022 doi:10.1038/s41593-022-01186-3",
    ),
    ReceptorEntry(
        key="H3",
        name="Histamine H3 receptor",
        system="histamine",
        role="Inhibitory autoreceptor on histamine neurons — when activated, suppresses histamine release. Histamine itself is critical for wakefulness and arousal (which is why classic antihistamines cause drowsiness). Densest in striatum + cortex.",
        pharmacology="BLOCKED by pitolisant (Wakix) — a wakefulness-promoting drug for narcolepsy. Blocking H3 disinhibits histamine release → more arousal. Indirectly relevant to all sedating antihistamines (diphenhydramine, doxylamine) which act on H1.",
        tracer="[11C]CBAN",
        n_subjects=8,
        url="https://github.com/netneurolab/hansen_receptors/raw/main/data/PET_nifti_images/H3_cban_hc8_gallezot.nii.gz",
        citation="Gallezot JD et al. Hansen 2022 doi:10.1038/s41593-022-01186-3",
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
