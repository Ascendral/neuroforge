"""Atlas data + brain endpoints tests.

These exercise nilearn's actual asset loaders and require network on first run
(to download Harvard-Oxford from NITRC if not yet cached). After first run,
nilearn caches to ~/nilearn_data/ and tests run offline.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from neuroforge_api.data import atlas
from neuroforge_api.main import app


def test_fsaverage_left_pial_has_expected_shape():
    surf = atlas.fsaverage_pial("left")
    assert surf.hemisphere == "left"
    # Known fsaverage5: 10242 vertices, 20480 faces per hemisphere
    assert surf.vertices.shape == (10242, 3)
    assert surf.faces.shape == (20480, 3)
    assert surf.destrieux_label_id.shape == (10242,)


def test_fsaverage_right_pial_has_expected_shape():
    surf = atlas.fsaverage_pial("right")
    assert surf.vertices.shape == (10242, 3)
    assert surf.faces.shape == (20480, 3)


def test_fsaverage_invalid_hemisphere():
    with pytest.raises(ValueError):
        atlas.fsaverage_pial("middle")


def test_destrieux_labels_present():
    labels = atlas.destrieux_labels()
    # Standard Destrieux 2010 has 76 entries (incl. 'Unknown')
    assert len(labels) == 76
    assert labels[0] == "Unknown"


def test_harvard_oxford_subcortical_includes_hippocampus():
    regions = atlas.harvard_oxford_subcortical_regions()
    labels = [r.label for r in regions]
    assert "Left Hippocampus" in labels
    assert "Right Hippocampus" in labels
    # The hippocampus should have a real centroid + voxel count
    hippo = next(r for r in regions if r.label == "Left Hippocampus")
    assert hippo.centroid_mni_mm is not None
    assert hippo.voxel_count is not None and hippo.voxel_count > 0


def test_harvard_oxford_cortical_includes_v1():
    regions = atlas.harvard_oxford_cortical_regions()
    labels = [r.label for r in regions]
    assert "Intracalcarine Cortex" in labels
    v1 = next(r for r in regions if r.label == "Intracalcarine Cortex")
    assert v1.centroid_mni_mm is not None
    # Sanity: V1 sits in the posterior occipital pole, MNI y ≈ -75
    assert -100 < v1.centroid_mni_mm[1] < -50


def test_module_mapping_covers_all_modules():
    assert set(atlas.MODULE_TO_REGION) == {
        "hubel_wiesel", "hebbian", "hopfield", "stdp", "hodgkin_huxley", "mcp"
    }
    # Anatomical-anchor modules MUST point at concrete labels
    for m in ("hubel_wiesel", "hebbian", "hopfield", "stdp"):
        assert atlas.MODULE_TO_REGION[m]["atlas"] is not None
        assert len(atlas.MODULE_TO_REGION[m]["labels"]) > 0
    # Non-anchor modules MUST be honestly null
    for m in ("hodgkin_huxley", "mcp"):
        assert atlas.MODULE_TO_REGION[m]["atlas"] is None
        assert atlas.MODULE_TO_REGION[m]["labels"] == []


def test_brain_mesh_endpoint_round_trip():
    client = TestClient(app)
    response = client.get("/api/brain/mesh")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["left"]["vertex_count"] == 10242
    assert body["left"]["face_count"] == 20480
    assert len(body["left"]["vertices_flat"]) == 10242 * 3
    assert len(body["left"]["faces_flat"]) == 20480 * 3
    assert len(body["destrieux_labels"]) == 76
    assert "Destrieux" in body["citation"]
    assert "10.1016/j.neuroimage.2010.06.010" in body["citation"]


def test_brain_regions_endpoint():
    client = TestClient(app)
    response = client.get("/api/brain/regions")
    assert response.status_code == 200, response.text
    body = response.json()
    assert any(r["label"] == "Left Hippocampus" for r in body["subcortical"])
    assert any(r["label"] == "Intracalcarine Cortex" for r in body["cortical"])
    # Module mapping is present and well-formed
    modules = {m["module"]: m for m in body["module_mapping"]}
    assert modules["hubel_wiesel"]["has_anatomical_anchor"] is True
    assert modules["hodgkin_huxley"]["has_anatomical_anchor"] is False
    assert "Intracalcarine Cortex" in modules["hubel_wiesel"]["labels"]
