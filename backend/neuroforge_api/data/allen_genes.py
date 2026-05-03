"""Allen Human Brain Atlas gene expression, mapped onto Desikan-Killiany regions.

Reference:
    Hawrylycz MJ, Lein ES, Guillozet-Bongaarts AL, ..., Jones AR.
    An anatomically comprehensive atlas of the adult human brain
    transcriptome. Nature. 2012;489(7416):391-9. doi:10.1038/nature11405

    Pipeline:
    Markello RD, Arnatkeviciute A, Poline J-B, Fulcher BD, Fornito A,
    Misic B. Standardizing workflows in imaging transcriptomics with
    the abagen toolbox. eLife. 2021;10:e72129. doi:10.7554/eLife.72129

Source data: Allen Institute microarray dataset, 6 post-mortem donors,
58,692 microarray probes covering ~20,000 genes, 3,702 tissue samples
distributed across both hemispheres.

We use the abagen toolbox (Markello 2021) to:
  1. Fetch the 6-donor microarray release (~4 GB cached locally).
  2. Reannotate probes using the latest gene definitions (Arnatkevic̆iūtė 2019).
  3. Filter probes by intensity-based threshold (≥0.5 above background).
  4. Collapse probes to genes via differential stability metric.
  5. Match each tissue sample to a Desikan-Killiany region by MNI coords.
  6. Aggregate samples within region (mean), interpolate missing labels.

Output: a (83 regions × ~15,600 genes) DataFrame, cached as a pickle in
`backend/data_cache/allen_dk_expression.pkl`. Region IDs match the
Desikan-Killiany atlas info table (abagen.fetch_desikan_killiany()['info']).

We expose a curated list of neurochemically meaningful genes (dopamine,
serotonin, glutamate, GABA, ACh, NE, opioid, plus a few neurotrophic /
neurodegenerative markers) along with each region's expression value
(donor-normalized, 0-1 scale per gene). The full 15,600-gene matrix is
also queryable.

Per CLAUDE.md anti-theater: every value here is the empirical mean
microarray intensity across Allen donors for that gene in that region,
processed by abagen's published pipeline. No values are imputed beyond
abagen's own nearest-region interpolation (clearly disclosed in the API).
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

CACHE_FILE = Path(__file__).resolve().parents[2] / "data_cache" / "allen_dk_expression.pkl"


# Curated set of plain-language gene descriptions: receptors, transporters,
# enzymes that map cleanly to neurotransmitter systems + a few markers.
# Each entry: (symbol, system, role, plain_description)
CURATED_GENES: tuple[tuple[str, str, str, str], ...] = (
    # Dopamine
    ("DRD1",   "Dopamine",      "D1 receptor",
     "Excitatory dopamine receptor — Gs-coupled. Densest in striatum (D1 direct pathway)."),
    ("DRD2",   "Dopamine",      "D2 receptor",
     "Inhibitory dopamine receptor — Gi-coupled. Target of all antipsychotics. Densest in striatum."),
    ("SLC6A3", "Dopamine",      "DAT (dopamine transporter)",
     "Recycles dopamine back into the presynaptic neuron. Cocaine + methylphenidate target."),
    ("TH",     "Dopamine",      "tyrosine hydroxylase",
     "Rate-limiting enzyme that synthesizes L-DOPA → dopamine. Marks dopaminergic neurons."),
    ("COMT",   "Dopamine",      "COMT enzyme",
     "Breaks down dopamine in PFC. Val158Met polymorphism affects working memory."),
    # Serotonin
    ("HTR1A",  "Serotonin",     "5-HT1A receptor",
     "Inhibitory serotonin autoreceptor. Densest in raphe + hippocampus. Anxiolytic target."),
    ("HTR2A",  "Serotonin",     "5-HT2A receptor",
     "Excitatory serotonin receptor. Densest in cortex. Target of psychedelics + atypical antipsychotics."),
    ("SLC6A4", "Serotonin",     "SERT (serotonin transporter)",
     "Recycles serotonin back. SSRI target (fluoxetine, sertraline)."),
    # Glutamate
    ("GRIN1",  "Glutamate",     "NMDA receptor (NR1)",
     "Obligatory subunit of the NMDA receptor — central to long-term potentiation + memory."),
    ("GRIN2A", "Glutamate",     "NMDA receptor (NR2A)",
     "Adult-form NMDA subunit — fast kinetics, dominates mature cortex."),
    ("GRIA1",  "Glutamate",     "AMPA receptor (GluA1)",
     "Fast-excitatory AMPA subunit. Trafficking is the molecular basis of LTP."),
    # GABA
    ("GABRA1", "GABA",          "GABA-A α1 subunit",
     "Most common GABA-A subunit. Benzodiazepine binding site."),
    ("GAD1",   "GABA",          "GAD67 enzyme",
     "Synthesizes GABA from glutamate. Marks inhibitory interneurons."),
    # Acetylcholine
    ("CHRM1",  "Acetylcholine", "M1 muscarinic receptor",
     "Postsynaptic excitatory ACh receptor. Densest in cortex + hippocampus. Memory."),
    ("CHRNA4", "Acetylcholine", "α4 nicotinic subunit",
     "High-affinity nicotine target. Mutations → autosomal dominant nocturnal frontal lobe epilepsy."),
    # Norepinephrine
    ("SLC6A2", "Norepinephrine","NET (norepinephrine transporter)",
     "Recycles norepinephrine. Target of atomoxetine + many antidepressants."),
    ("ADRA1A", "Norepinephrine","α1A adrenergic receptor",
     "Excitatory NE receptor. Vasoconstriction + cortical arousal."),
    # Opioid
    ("OPRM1",  "Opioid",        "μ-opioid receptor",
     "Target of morphine, fentanyl, endogenous β-endorphin. Reward + analgesia."),
    # Cannabinoid
    ("CNR1",   "Cannabinoid",   "CB1 receptor",
     "THC binding site. Densest in striatum, hippocampus, cerebellum. Retrograde signaling."),
    # Neurotrophic / disease markers
    ("BDNF",   "Neurotrophic",  "brain-derived neurotrophic factor",
     "Synaptic plasticity + neurogenesis. Reduced in depression."),
    ("MAOA",   "Catabolism",    "monoamine oxidase A",
     "Breaks down DA, 5-HT, NE in mitochondria. MAOI target."),
    ("APOE",   "Disease marker","apolipoprotein E",
     "ε4 allele = strongest genetic risk for Alzheimer's. Lipid transport in brain."),
    ("SNCA",   "Disease marker","α-synuclein",
     "Aggregates → Lewy bodies in Parkinson's + DLB. Densest in synaptic terminals."),
    ("MAPT",   "Disease marker","microtubule-associated protein tau",
     "Hyperphosphorylated tau → tangles in Alzheimer's, FTD, PSP."),
    ("HTT",    "Disease marker","huntingtin",
     "CAG-repeat expansion → Huntington's disease. Striatal neurons most vulnerable."),
)
CURATED_SYMBOLS = tuple(g[0] for g in CURATED_GENES)


@dataclass(frozen=True, slots=True)
class GeneInfo:
    symbol: str
    system: str
    role: str
    description: str


@dataclass(frozen=True, slots=True)
class RegionInfo:
    region_id: int      # DK label id (1-83)
    label: str          # DK plain-name e.g. 'caudalmiddlefrontal'
    hemisphere: str     # 'L' or 'R'
    structure: str      # 'cortex' / 'subcortex' / 'cerebellum'
    centroid_mni_mm: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class GeneExpressionMap:
    gene: GeneInfo
    # per-region normalized expression (0-1 within this gene), with region_id as key
    region_values: dict[int, float]
    # raw value range (min, max) before normalization
    raw_min: float
    raw_max: float


@lru_cache(maxsize=1)
def _expression_df() -> pd.DataFrame | None:
    if not CACHE_FILE.exists():
        return None
    with open(CACHE_FILE, "rb") as f:
        return pickle.load(f)


@lru_cache(maxsize=1)
def _dk_atlas_info() -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Returns (info_df, label_volume, affine) for Desikan-Killiany."""
    import abagen
    import nibabel as nib

    atlas = abagen.fetch_desikan_killiany()
    info = pd.read_csv(atlas["info"])
    img = nib.load(atlas["image"])
    arr = np.asarray(img.dataobj).astype(np.int32)
    return info, arr, img.affine


@lru_cache(maxsize=1)
def _dk_region_centroids() -> dict[int, tuple[float, float, float]]:
    """Per-region MNI mm centroid from the DK volumetric label map."""
    _, arr, affine = _dk_atlas_info()
    out: dict[int, tuple[float, float, float]] = {}
    for rid in np.unique(arr):
        if rid == 0:
            continue
        coords = np.argwhere(arr == rid).astype(np.float64).mean(axis=0)
        homog = np.array([coords[0], coords[1], coords[2], 1.0])
        mni = (affine @ homog)[:3]
        out[int(rid)] = (float(mni[0]), float(mni[1]), float(mni[2]))
    return out


def all_regions() -> list[RegionInfo]:
    info, _, _ = _dk_atlas_info()
    centroids = _dk_region_centroids()
    out: list[RegionInfo] = []
    for _, row in info.iterrows():
        rid = int(row["id"])
        c = centroids.get(rid, (0.0, 0.0, 0.0))
        out.append(
            RegionInfo(
                region_id=rid,
                label=str(row["label"]),
                hemisphere=str(row["hemisphere"]),
                structure=str(row["structure"]),
                centroid_mni_mm=c,
            )
        )
    return out


def curated_genes() -> list[GeneInfo]:
    return [GeneInfo(symbol=s, system=sys, role=r, description=d) for s, sys, r, d in CURATED_GENES]


def gene_expression(symbol: str) -> GeneExpressionMap | None:
    df = _expression_df()
    if df is None or symbol not in df.columns:
        return None
    spec = next((g for g in CURATED_GENES if g[0] == symbol), None)
    if spec is None:
        # Allow fetching any gene from the matrix, not just curated ones.
        spec = (symbol, "Other", symbol, "")
    series = df[symbol].dropna()
    if series.empty:
        return None
    raw_min = float(series.min())
    raw_max = float(series.max())
    rng = raw_max - raw_min
    norm = (series - raw_min) / rng if rng > 1e-9 else series * 0.0
    region_values = {int(rid): float(v) for rid, v in norm.items()}
    return GeneExpressionMap(
        gene=GeneInfo(symbol=spec[0], system=spec[1], role=spec[2], description=spec[3]),
        region_values=region_values,
        raw_min=raw_min,
        raw_max=raw_max,
    )


def expression_available() -> bool:
    return _expression_df() is not None
