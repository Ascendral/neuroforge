"""GET /api/brain/* — atlas surface mesh + region catalog + module mapping."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from neuroforge_api.data import atlas as atlas_module
from neuroforge_api.data import receptors as receptors_module

router = APIRouter(prefix="/api/brain", tags=["brain"])

ATLAS_CITATION = (
    "Surface: Fischl B et al. fsaverage template. Hum Brain Mapp. 1999;8(4):272-84. "
    "doi:10.1002/(SICI)1097-0193(1999)8:4<272::AID-HBM10>3.0.CO;2-4. "
    "Cortical parcellation: Destrieux C et al. NeuroImage. 2010;53(1):1-15. "
    "doi:10.1016/j.neuroimage.2010.06.010. "
    "Subcortical parcellation: Desikan RS et al. (Harvard-Oxford / FSL). "
    "NeuroImage. 2006;31(3):968-980. doi:10.1016/j.neuroimage.2006.01.021"
)


class HemisphereMesh(BaseModel):
    hemisphere: str
    vertex_count: int
    face_count: int
    vertices_flat: list[float]      # (N*3,) flat — x0,y0,z0,x1,y1,z1,...
    faces_flat: list[int]           # (M*3,) flat
    destrieux_label_id: list[int]   # (N,) per-vertex


class CorticalMeshResponse(BaseModel):
    left: HemisphereMesh
    right: HemisphereMesh
    destrieux_labels: list[str]
    citation: str


class SubcorticalMesh(BaseModel):
    label: str
    vertex_count: int
    face_count: int
    vertices_flat: list[float]
    faces_flat: list[int]


class SubcorticalMeshResponse(BaseModel):
    meshes: list[SubcorticalMesh]
    citation: str


class RegionSummary(BaseModel):
    region_id: int
    label: str
    atlas: str
    centroid_mni_mm: list[float] | None
    voxel_count: int | None


class ModuleMapping(BaseModel):
    module: str
    atlas: str | None
    labels: list[str]
    note: str
    has_anatomical_anchor: bool


class RegionCatalogResponse(BaseModel):
    cortical: list[RegionSummary]
    subcortical: list[RegionSummary]
    module_mapping: list[ModuleMapping]
    citation: str


class FunctionRegionCentroid(BaseModel):
    label: str
    centroid_mni_mm: list[float] | None
    found: bool


class CognitiveFunction(BaseModel):
    name: str
    description: str
    atlas_labels: list[str]
    citation: str
    region_centroids: list[FunctionRegionCentroid]


class CognitiveFunctionsResponse(BaseModel):
    functions: list[CognitiveFunction]
    note: str


class ReceptorRegionValue(BaseModel):
    label: str
    centroid_mni_mm: list[float] | None
    mean: float
    normalized: float  # 0-1 within this atlas


class ReceptorEntry(BaseModel):
    key: str
    name: str
    system: str
    tracer: str
    n_subjects: int
    citation: str


class ReceptorListResponse(BaseModel):
    receptors: list[ReceptorEntry]
    umbrella_citation: str


class ReceptorMapResponse(BaseModel):
    receptor: ReceptorEntry
    cortical: list[ReceptorRegionValue]
    subcortical: list[ReceptorRegionValue]


class WhiteMatterTract(BaseModel):
    name: str
    description: str
    color: str
    start_label: str
    end_label: str
    start_mni_mm: list[float] | None
    end_mni_mm: list[float] | None
    midpoint_mni_mm: list[float] | None


class WhiteMatterTractsResponse(BaseModel):
    tracts: list[WhiteMatterTract]
    citation: str
    note: str


@router.get("/mesh", response_model=CorticalMeshResponse)
def get_cortical_mesh() -> CorticalMeshResponse:
    """Return fsaverage5 pial mesh + Destrieux per-vertex labels for both hemispheres.

    ~20k vertices total, ~1MB JSON. Cached client-side after first fetch.
    """
    try:
        left = atlas_module.fsaverage_pial("left")
        right = atlas_module.fsaverage_pial("right")
        labels = atlas_module.destrieux_labels()
    except Exception as exc:  # noqa: BLE001  — surface real network/asset errors honestly
        raise HTTPException(status_code=502, detail=f"atlas asset error: {exc}") from exc

    def _hemi_payload(surf: atlas_module.CorticalSurface) -> HemisphereMesh:
        return HemisphereMesh(
            hemisphere=surf.hemisphere,
            vertex_count=int(surf.vertices.shape[0]),
            face_count=int(surf.faces.shape[0]),
            vertices_flat=surf.vertices.astype(float).flatten().tolist(),
            faces_flat=surf.faces.astype(int).flatten().tolist(),
            destrieux_label_id=surf.destrieux_label_id.astype(int).tolist(),
        )

    return CorticalMeshResponse(
        left=_hemi_payload(left),
        right=_hemi_payload(right),
        destrieux_labels=list(labels),
        citation=ATLAS_CITATION,
    )


# Which Harvard-Oxford subcortical regions to surface as meshes inside the
# cortical shell. These give the brain visual extension below + medial to
# the cortex (where the cortical mesh ends) and provide an anatomically
# correct container for cells placed in those regions.
SUBCORTICAL_MESHES_TO_INCLUDE: tuple[str, ...] = (
    "Brain-Stem",
    "Left Hippocampus",
    "Right Hippocampus",
    "Left Amygdala",
    "Right Amygdala",
    "Left Thalamus",
    "Right Thalamus",
    "Left Caudate",
    "Right Caudate",
    "Left Putamen",
    "Right Putamen",
)


@router.get("/subcortical-meshes", response_model=SubcorticalMeshResponse)
def get_subcortical_meshes() -> SubcorticalMeshResponse:
    """Triangulated subcortical region surfaces (marching cubes from HO masks)."""
    out: list[SubcorticalMesh] = []
    for label in SUBCORTICAL_MESHES_TO_INCLUDE:
        result = atlas_module.subcortical_region_mesh(label)
        if result is None:
            continue
        verts, faces = result
        out.append(
            SubcorticalMesh(
                label=label,
                vertex_count=int(verts.shape[0]),
                face_count=int(faces.shape[0]),
                vertices_flat=verts.flatten().astype(float).tolist(),
                faces_flat=faces.flatten().astype(int).tolist(),
            )
        )
    return SubcorticalMeshResponse(meshes=out, citation=ATLAS_CITATION)


@router.get("/regions", response_model=RegionCatalogResponse)
def get_region_catalog() -> RegionCatalogResponse:
    """Region catalog: HO cortical + HO subcortical + module-to-region mapping."""
    try:
        cortical = atlas_module.harvard_oxford_cortical_regions()
        subcortical = atlas_module.harvard_oxford_subcortical_regions()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"atlas asset error: {exc}") from exc

    def _to_summary(r: atlas_module.AtlasRegion) -> RegionSummary:
        return RegionSummary(
            region_id=r.region_id,
            label=r.label,
            atlas=r.atlas,
            centroid_mni_mm=list(r.centroid_mni_mm) if r.centroid_mni_mm else None,
            voxel_count=r.voxel_count,
        )

    mappings = [
        ModuleMapping(
            module=name,
            atlas=info["atlas"],
            labels=list(info["labels"]),
            note=info["note"],
            has_anatomical_anchor=info["atlas"] is not None,
        )
        for name, info in atlas_module.MODULE_TO_REGION.items()
    ]

    return RegionCatalogResponse(
        cortical=[_to_summary(r) for r in cortical],
        subcortical=[_to_summary(r) for r in subcortical],
        module_mapping=mappings,
        citation=ATLAS_CITATION,
    )


@router.get("/functions", response_model=CognitiveFunctionsResponse)
def get_cognitive_functions() -> CognitiveFunctionsResponse:
    """Curated cognitive-function → brain-region registry with foundational citations."""
    cortical = atlas_module.harvard_oxford_cortical_regions()
    subcortical = atlas_module.harvard_oxford_subcortical_regions()
    by_label: dict[str, atlas_module.AtlasRegion] = {r.label: r for r in cortical + subcortical}

    out: list[CognitiveFunction] = []
    for f in atlas_module.COGNITIVE_FUNCTIONS:
        centroids: list[FunctionRegionCentroid] = []
        for lbl in f["atlas_labels"]:
            r = by_label.get(lbl)
            if r and r.centroid_mni_mm:
                centroids.append(
                    FunctionRegionCentroid(
                        label=lbl,
                        centroid_mni_mm=list(r.centroid_mni_mm),
                        found=True,
                    )
                )
            else:
                centroids.append(
                    FunctionRegionCentroid(label=lbl, centroid_mni_mm=None, found=False)
                )
        out.append(
            CognitiveFunction(
                name=f["name"],
                description=f["description"],
                atlas_labels=list(f["atlas_labels"]),
                citation=f["citation"],
                region_centroids=centroids,
            )
        )

    return CognitiveFunctionsResponse(
        functions=out,
        note=(
            "Each function-region mapping is curated from primary neuroscience "
            "literature with the foundational citation listed. See "
            "neuroforge_api.data.atlas.COGNITIVE_FUNCTIONS for the source."
        ),
    )


HANSEN_UMBRELLA = (
    "Hansen JY et al. Mapping neurotransmitter systems to the structural and "
    "functional organization of the human neocortex. Nat Neurosci. "
    "2022;25(11):1569-1581. doi:10.1038/s41593-022-01186-3. "
    "Data: github.com/netneurolab/hansen_receptors"
)


def _receptor_to_pydantic(r: receptors_module.ReceptorEntry) -> ReceptorEntry:
    return ReceptorEntry(
        key=r.key,
        name=r.name,
        system=r.system,
        tracer=r.tracer,
        n_subjects=r.n_subjects,
        citation=r.citation,
    )


@router.get("/receptors", response_model=ReceptorListResponse)
def list_receptors() -> ReceptorListResponse:
    return ReceptorListResponse(
        receptors=[_receptor_to_pydantic(r) for r in receptors_module.RECEPTORS],
        umbrella_citation=HANSEN_UMBRELLA,
    )


@router.get("/receptors/{key}", response_model=ReceptorMapResponse)
def receptor_map(key: str) -> ReceptorMapResponse:
    receptor = next((r for r in receptors_module.RECEPTORS if r.key == key), None)
    if receptor is None:
        raise HTTPException(status_code=404, detail=f"unknown receptor: {key}")
    try:
        per_region = receptors_module.receptor_per_region(key)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"receptor data error: {exc}") from exc

    # Look up centroids
    cortical_regions = atlas_module.harvard_oxford_cortical_regions()
    subcortical_regions = atlas_module.harvard_oxford_subcortical_regions()
    cort_by_label = {r.label: r for r in cortical_regions}
    sub_by_label = {r.label: r for r in subcortical_regions}

    def _to_value(d: dict, by_label: dict) -> ReceptorRegionValue:
        label = d["label"]
        region = by_label.get(label)
        return ReceptorRegionValue(
            label=label,
            centroid_mni_mm=list(region.centroid_mni_mm) if region and region.centroid_mni_mm else None,
            mean=d["mean"],
            normalized=d["normalized"],
        )

    return ReceptorMapResponse(
        receptor=_receptor_to_pydantic(receptor),
        cortical=[_to_value(d, cort_by_label) for d in per_region["cortical"]],
        subcortical=[_to_value(d, sub_by_label) for d in per_region["subcortical"]],
    )


CATANI_CITATION = (
    "Catani M, Thiebaut de Schotten M. A diffusion tensor imaging "
    "tractography atlas for virtual in vivo dissections. Cortex. "
    "2008;44(8):1105-1132. doi:10.1016/j.cortex.2008.05.004. "
    "Catani M, Thiebaut de Schotten M. Atlas of Human Brain Connections. "
    "Oxford University Press, 2012."
)


@router.get("/tracts", response_model=WhiteMatterTractsResponse)
def list_white_matter_tracts() -> WhiteMatterTractsResponse:
    """Schematic centerlines of major white-matter bundles."""
    cortical_regions = atlas_module.harvard_oxford_cortical_regions()
    subcortical_regions = atlas_module.harvard_oxford_subcortical_regions()
    by_label: dict[str, atlas_module.AtlasRegion] = {
        r.label: r for r in cortical_regions + subcortical_regions
    }

    out: list[WhiteMatterTract] = []
    for t in atlas_module.WHITE_MATTER_TRACTS:
        start_region = by_label.get(t["start_label"])
        end_region = by_label.get(t["end_label"])
        start_mni = list(start_region.centroid_mni_mm) if start_region and start_region.centroid_mni_mm else None
        end_mni = list(end_region.centroid_mni_mm) if end_region and end_region.centroid_mni_mm else None

        if "midpoint_override_mm" in t:
            midpoint = list(t["midpoint_override_mm"])
        elif start_mni and end_mni:
            ox, oy, oz = t["midpoint_offset_mm"]
            midpoint = [
                (start_mni[0] + end_mni[0]) / 2 + ox,
                (start_mni[1] + end_mni[1]) / 2 + oy,
                (start_mni[2] + end_mni[2]) / 2 + oz,
            ]
        else:
            midpoint = None

        # For corpus-callosum-style "left to right of same label" tracts, the
        # endpoints need to be split L/R of the midline since both labels are
        # the same atlas record (single bilateral centroid). Apply ±25mm
        # x-offset to give a real bilateral curve.
        if start_mni and end_mni and t["start_label"] == t["end_label"]:
            start_mni = [start_mni[0] - 25, start_mni[1], start_mni[2]]
            end_mni = [end_mni[0] + 25, end_mni[1], end_mni[2]]

        out.append(
            WhiteMatterTract(
                name=t["name"],
                description=t["description"],
                color=t["color"],
                start_label=t["start_label"],
                end_label=t["end_label"],
                start_mni_mm=start_mni,
                end_mni_mm=end_mni,
                midpoint_mni_mm=midpoint,
            )
        )

    return WhiteMatterTractsResponse(
        tracts=out,
        citation=CATANI_CITATION,
        note=(
            "Each tract is rendered as a single Bezier curve between two "
            "Harvard-Oxford region centroids — a SCHEMATIC centerline, not "
            "fiber-resolved tractography. Real DTI streamlines would be tens "
            "of thousands of polylines per bundle (Yeh HCP-1065 / FSL XTRACT)."
        ),
    )
