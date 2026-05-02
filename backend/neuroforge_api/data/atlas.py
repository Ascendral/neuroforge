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


# Cognitive functions → brain regions, with foundational citations.
# Each entry is curated by hand from neuroscience literature; visible here so
# anyone can audit the source. Anti-theater: no inferred or aggregated maps,
# every claim ties to a specific paper. atlas_labels are Harvard-Oxford
# region names so they match what /api/brain/regions returns.
COGNITIVE_FUNCTIONS: list[dict] = [
    {
        "name": "episodic memory",
        "description": "Formation and retrieval of memories of specific events.",
        "atlas_labels": ["Left Hippocampus", "Right Hippocampus"],
        "citation": (
            "Scoville WB, Milner B. Loss of recent memory after bilateral "
            "hippocampal lesions. J Neurol Neurosurg Psychiatry. "
            "1957;20(1):11-21. doi:10.1136/jnnp.20.1.11"
        ),
    },
    {
        "name": "fear and emotion",
        "description": "Detection of threat and emotional salience; classical fear conditioning.",
        "atlas_labels": ["Left Amygdala", "Right Amygdala"],
        "citation": (
            "LeDoux JE. Emotion and the amygdala. Annu Rev Neurosci. "
            "1992;15:353-75. doi:10.1146/annurev.ne.15.030192.000543"
        ),
    },
    {
        "name": "reward and motivation",
        "description": "Dopaminergic reward-prediction-error signaling drives learning.",
        "atlas_labels": [
            "Left Caudate", "Right Caudate",
            "Left Putamen", "Right Putamen",
            "Left Accumbens", "Right Accumbens",
        ],
        "citation": (
            "Schultz W, Dayan P, Montague PR. A neural substrate of prediction "
            "and reward. Science. 1997;275(5306):1593-9. "
            "doi:10.1126/science.275.5306.1593"
        ),
    },
    {
        "name": "working memory",
        "description": "Active maintenance and manipulation of information over seconds.",
        "atlas_labels": [
            "Frontal Pole",
            "Middle Frontal Gyrus",
            "Inferior Frontal Gyrus, pars triangularis",
        ],
        "citation": (
            "Goldman-Rakic PS. Cellular basis of working memory. "
            "Annu Rev Neurosci. 1995;18:477-98. "
            "doi:10.1146/annurev.ne.18.030195.001541"
        ),
    },
    {
        "name": "visual perception",
        "description": "Primary visual cortex extracts oriented edges from retinal input.",
        "atlas_labels": ["Intracalcarine Cortex", "Supracalcarine Cortex", "Occipital Pole"],
        "citation": (
            "Hubel DH, Wiesel TN. Receptive fields, binocular interaction "
            "and functional architecture in the cat's visual cortex. "
            "J Physiol. 1962;160(1):106-54. doi:10.1113/jphysiol.1962.sp006837"
        ),
    },
    {
        "name": "motor planning and execution",
        "description": "Voluntary movement initiation, somatotopic motor homunculus.",
        "atlas_labels": ["Precentral Gyrus"],
        "citation": (
            "Penfield W, Boldrey E. Somatic motor and sensory representation "
            "in the cerebral cortex of man as studied by electrical "
            "stimulation. Brain. 1937;60(4):389-443. doi:10.1093/brain/60.4.389"
        ),
    },
    {
        "name": "default mode / self-reference",
        "description": "Active when not task-engaged: mind-wandering, autobiographical thought.",
        "atlas_labels": [
            "Cingulate Gyrus, posterior division",
            "Frontal Medial Cortex",
        ],
        "citation": (
            "Raichle ME, MacLeod AM, Snyder AZ, Powers WJ, Gusnard DA, "
            "Shulman GL. A default mode of brain function. Proc Natl Acad "
            "Sci USA. 2001;98(2):676-82. doi:10.1073/pnas.98.2.676"
        ),
    },
    {
        "name": "language production (Broca)",
        "description": "Speech production, grammatical processing; classically left-lateralized.",
        "atlas_labels": [
            "Inferior Frontal Gyrus, pars opercularis",
            "Inferior Frontal Gyrus, pars triangularis",
        ],
        "citation": (
            "Broca P. Remarques sur le siège de la faculté du langage "
            "articulé. Bulletin de la Société Anatomique. 1861;36:330-57. "
            "(foundational classic; no DOI)"
        ),
    },
    {
        "name": "attention orienting",
        "description": "Top-down spatial attention; frontoparietal control network.",
        "atlas_labels": ["Superior Parietal Lobule", "Frontal Pole"],
        "citation": (
            "Posner MI. Orienting of attention. Q J Exp Psychol. "
            "1980;32(1):3-25. doi:10.1080/00335558008248231"
        ),
    },
    {
        "name": "arousal and wakefulness",
        "description": "Brainstem reticular activating system regulates cortical arousal.",
        "atlas_labels": ["Brain-Stem"],
        "citation": (
            "Moruzzi G, Magoun HW. Brain stem reticular formation and "
            "activation of the EEG. Electroencephalogr Clin Neurophysiol. "
            "1949;1(4):455-73. doi:10.1016/0013-4694(49)90219-9"
        ),
    },
    {
        "name": "pain perception",
        "description": "Affective dimension of pain via anterior cingulate + insula.",
        "atlas_labels": [
            "Insular Cortex",
            "Cingulate Gyrus, anterior division",
        ],
        "citation": (
            "Apkarian AV, Bushnell MC, Treede RD, Zubieta JK. Human brain "
            "mechanisms of pain perception and regulation in health and "
            "disease. Eur J Pain. 2005;9(4):463-84. "
            "doi:10.1016/j.ejpain.2004.11.001"
        ),
    },
    {
        "name": "executive control / conflict monitoring",
        "description": "ACC monitors response conflict; dlPFC implements top-down control.",
        "atlas_labels": [
            "Cingulate Gyrus, anterior division",
            "Middle Frontal Gyrus",
        ],
        "citation": (
            "Miller EK, Cohen JD. An integrative theory of prefrontal cortex "
            "function. Annu Rev Neurosci. 2001;24:167-202. "
            "doi:10.1146/annurev.neuro.24.1.167"
        ),
    },
    {
        "name": "face recognition",
        "description": "The Fusiform Face Area (FFA) responds preferentially to faces — discovered by Kanwisher et al.",
        "atlas_labels": [
            "Temporal Fusiform Cortex, posterior division",
            "Occipital Fusiform Gyrus",
        ],
        "citation": (
            "Kanwisher N, McDermott J, Chun MM. The fusiform face area: a module "
            "in human extrastriate cortex specialized for face perception. "
            "J Neurosci. 1997;17(11):4302-11. "
            "doi:10.1523/JNEUROSCI.17-11-04302.1997"
        ),
    },
    {
        "name": "reading / visual word form",
        "description": "The Visual Word Form Area (left occipitotemporal cortex) recognizes written words across font and case.",
        "atlas_labels": [
            "Temporal Occipital Fusiform Cortex",
        ],
        "citation": (
            "Cohen L, Lehéricy S, Chochon F, Lemer C, Rivaud S, Dehaene S. "
            "Language-specific tuning of visual cortex? Functional properties "
            "of the Visual Word Form Area. Brain. 2002;125(5):1054-69. "
            "doi:10.1093/brain/awf094"
        ),
    },
    {
        "name": "place / scene recognition",
        "description": "The Parahippocampal Place Area (PPA) responds to environmental scenes and spatial layouts.",
        "atlas_labels": [
            "Parahippocampal Gyrus, posterior division",
            "Lingual Gyrus",
        ],
        "citation": (
            "Epstein R, Kanwisher N. A cortical representation of the local "
            "visual environment. Nature. 1998;392(6676):598-601. "
            "doi:10.1038/33402"
        ),
    },
    {
        "name": "number processing",
        "description": "The Intraparietal Sulcus represents quantity and approximate number magnitude.",
        "atlas_labels": [
            "Superior Parietal Lobule",
        ],
        "citation": (
            "Dehaene S, Piazza M, Pinel P, Cohen L. Three parietal circuits for "
            "number processing. Cognit Neuropsychol. 2003;20(3-6):487-506. "
            "doi:10.1080/02643290244000239"
        ),
    },
    {
        "name": "auditory perception",
        "description": "Heschl's Gyrus is the primary auditory cortex — first cortical stage of hearing.",
        "atlas_labels": [
            "Heschl's Gyrus (includes H1 and H2)",
        ],
        "citation": (
            "Hackett TA. Anatomical organization of the auditory cortex. "
            "J Am Acad Audiol. 2008;19(10):774-89. "
            "doi:10.3766/jaaa.19.10.5"
        ),
    },
    {
        "name": "empathy / pain affect",
        "description": "Watching another person in pain activates the same anterior insula and ACC as feeling pain yourself.",
        "atlas_labels": [
            "Insular Cortex",
            "Cingulate Gyrus, anterior division",
        ],
        "citation": (
            "Singer T, Seymour B, O'Doherty J, Kaube H, Dolan RJ, Frith CD. "
            "Empathy for pain involves the affective but not sensory components "
            "of pain. Science. 2004;303(5661):1157-62. "
            "doi:10.1126/science.1093535"
        ),
    },
    {
        "name": "theory of mind / social cognition",
        "description": "Reasoning about others' mental states activates the temporoparietal junction and medial prefrontal cortex.",
        "atlas_labels": [
            "Frontal Pole",
            "Superior Temporal Gyrus, posterior division",
            "Angular Gyrus",
        ],
        "citation": (
            "Saxe R, Kanwisher N. People thinking about thinking people: the "
            "role of the temporo-parietal junction in 'theory of mind'. "
            "NeuroImage. 2003;19(4):1835-42. doi:10.1016/S1053-8119(03)00230-1"
        ),
    },
    {
        "name": "subjective value / decision making",
        "description": "Ventromedial prefrontal cortex (vmPFC) computes subjective value during choice.",
        "atlas_labels": [
            "Frontal Medial Cortex",
            "Subcallosal Cortex",
        ],
        "citation": (
            "Kable JW, Glimcher PW. The neural correlates of subjective value "
            "during intertemporal choice. Nat Neurosci. 2007;10(12):1625-33. "
            "doi:10.1038/nn2007"
        ),
    },
    {
        "name": "autobiographical memory",
        "description": "Recalling personal past events recruits a network including mPFC, posterior cingulate, and lateral temporal cortex.",
        "atlas_labels": [
            "Frontal Medial Cortex",
            "Cingulate Gyrus, posterior division",
            "Middle Temporal Gyrus, posterior division",
        ],
        "citation": (
            "Svoboda E, McKinnon MC, Levine B. The functional neuroanatomy of "
            "autobiographical memory: a meta-analysis. Neuropsychologia. "
            "2006;44(12):2189-2208. doi:10.1016/j.neuropsychologia.2006.05.023"
        ),
    },
    {
        "name": "language comprehension (Wernicke)",
        "description": "Speech comprehension classically localized to left posterior superior temporal gyrus.",
        "atlas_labels": [
            "Superior Temporal Gyrus, posterior division",
        ],
        "citation": (
            "Wernicke C. Der aphasische Symptomencomplex. Breslau: M. Cohn "
            "& Weigert; 1874. (foundational classic; no DOI)"
        ),
    },
    {
        "name": "mirror system / action observation",
        "description": "Watching another's action engages premotor + parietal regions overlapping with one's own action production.",
        "atlas_labels": [
            "Precentral Gyrus",
            "Supramarginal Gyrus, anterior division",
        ],
        "citation": (
            "Rizzolatti G, Craighero L. The mirror-neuron system. Annu Rev "
            "Neurosci. 2004;27:169-92. "
            "doi:10.1146/annurev.neuro.27.070203.144230"
        ),
    },
    {
        "name": "time perception",
        "description": "Subjective time intervals are tracked by the anterior insula and ACC, with cerebellum + basal ganglia for sub-second timing.",
        "atlas_labels": [
            "Insular Cortex",
            "Cingulate Gyrus, anterior division",
        ],
        "citation": (
            "Wittmann M. The inner experience of time. Philos Trans R Soc Lond "
            "B Biol Sci. 2009;364(1525):1955-67. doi:10.1098/rstb.2009.0029"
        ),
    },
]


# Major white-matter fiber bundles. Endpoints reference Harvard-Oxford labels;
# midpoints are anatomically-informed sag/cor offsets so the curve bows along
# the known anatomical course rather than going straight. Per Catani &
# Thiebaut de Schotten 2008 + 2012 atlases (the canonical clinical atlas of
# major human white-matter bundles).
#
# This is SCHEMATIC: each "tract" is rendered as a single Bezier curve, NOT
# as fiber-resolved tractography. Real DTI/HARDI streamlines (Yeh HCP-1065,
# FSL XTRACT) would be tens of thousands of polylines per bundle. Frontend
# UI calls these "schematic centerlines" honestly.
#
# Reference (clinical atlas):
#     Catani M, Thiebaut de Schotten M. A diffusion tensor imaging
#     tractography atlas for virtual in vivo dissections. Cortex.
#     2008;44(8):1105-1132. doi:10.1016/j.cortex.2008.05.004
#     Catani M, Thiebaut de Schotten M. Atlas of Human Brain Connections.
#     Oxford University Press, 2012.

WHITE_MATTER_TRACTS: list[dict] = [
    {
        "name": "Arcuate fasciculus (left)",
        "description": "Connects Broca's area (frontal speech production) to Wernicke's area (temporal language comprehension). Damage → conduction aphasia.",
        "start_label": "Inferior Frontal Gyrus, pars opercularis",
        "end_label": "Superior Temporal Gyrus, posterior division",
        "midpoint_offset_mm": [-30, -25, 25],
        "color": "#ffd86b",
    },
    {
        "name": "Cingulum (left)",
        "description": "Wraps around the corpus callosum within the cingulate gyrus. Limbic-cortical connectivity.",
        "start_label": "Cingulate Gyrus, anterior division",
        "end_label": "Cingulate Gyrus, posterior division",
        "midpoint_offset_mm": [-5, -10, 30],
        "color": "#9bd2ff",
    },
    {
        "name": "Corpus callosum (genu)",
        "description": "Anterior bridge between left and right prefrontal cortex. Largest white-matter commissure in the brain.",
        "start_label": "Frontal Pole",
        "end_label": "Frontal Pole",
        "midpoint_offset_mm": [0, 35, 15],
        "midpoint_override_mm": [0, 35, 15],
        "color": "#ff8c5e",
    },
    {
        "name": "Corpus callosum (splenium)",
        "description": "Posterior bridge connecting bilateral occipital + parietal cortex.",
        "start_label": "Lateral Occipital Cortex, superior division",
        "end_label": "Lateral Occipital Cortex, superior division",
        "midpoint_offset_mm": [0, -35, 25],
        "midpoint_override_mm": [0, -35, 25],
        "color": "#ff6bd4",
    },
    {
        "name": "Fornix",
        "description": "Major output of the hippocampus to the mammillary bodies (memory circuit / Papez circuit).",
        "start_label": "Left Hippocampus",
        "end_label": "Right Hippocampus",
        "midpoint_offset_mm": [0, -10, 5],
        "color": "#7fff9b",
    },
    {
        "name": "Uncinate fasciculus (left)",
        "description": "Hooks under the Sylvian fissure connecting orbitofrontal to anterior temporal cortex. Emotion + memory integration.",
        "start_label": "Frontal Orbital Cortex",
        "end_label": "Temporal Pole",
        "midpoint_offset_mm": [-25, 15, -15],
        "color": "#c45eff",
    },
    {
        "name": "Inferior longitudinal fasciculus (left)",
        "description": "Major occipito-temporal pathway for visual recognition and reading.",
        "start_label": "Lateral Occipital Cortex, inferior division",
        "end_label": "Temporal Pole",
        "midpoint_offset_mm": [-40, -30, -15],
        "color": "#ff2d2d",
    },
    {
        "name": "Corticospinal tract (left)",
        "description": "Voluntary motor commands from primary motor cortex to spinal cord. Damage → contralateral paralysis.",
        "start_label": "Precentral Gyrus",
        "end_label": "Brain-Stem",
        "midpoint_offset_mm": [-15, -10, 0],
        "color": "#ffe45e",
    },
]


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


@lru_cache(maxsize=8)
def subcortical_region_mesh(label: str) -> tuple[np.ndarray, np.ndarray] | None:
    """Extract a triangulated surface mesh from a Harvard-Oxford subcortical
    region's voxel mask using marching cubes.

    Returns (vertices_mni_mm, faces) or None if the label has no voxels.
    """
    from scipy.ndimage import gaussian_filter
    from skimage import measure

    atlas = harvard_oxford_subcortical_atlas()
    img = _load_atlas_image(atlas["maps"])
    arr = np.asarray(img.dataobj)
    if label not in atlas["labels"]:
        return None
    label_id = atlas["labels"].index(label)
    mask = (arr == label_id).astype(np.float32)
    if not mask.any():
        return None
    # Mild smoothing so the mesh isn't a stair-stepped voxel cube.
    smoothed = gaussian_filter(mask, sigma=0.7)
    verts, faces, _, _ = measure.marching_cubes(smoothed, level=0.3)
    # voxel indices → MNI mm via affine
    affine = img.affine
    homog = np.column_stack([verts, np.ones(len(verts))])
    mni = (affine @ homog.T).T[:, :3]
    return mni.astype(np.float32), faces.astype(np.int32)


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
