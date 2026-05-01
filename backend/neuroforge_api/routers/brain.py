"""GET /api/brain/* — atlas surface mesh + region catalog + module mapping."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from neuroforge_api.data import atlas as atlas_module

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
