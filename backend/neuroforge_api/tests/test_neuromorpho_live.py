"""Live integration tests against neuromorpho.org.

Per CLAUDE.md anti-theater rules, we test against the real public API rather
than mock responses. These tests are skipped automatically if the network is
unreachable, but in CI they MUST run and pass — a green build with these
skipped is meaningless.

Tag: requires public network egress to neuromorpho.org.
"""

from __future__ import annotations

import pytest
import requests

from neuroforge_api.parsers.swc import parse_swc
from neuroforge_api.sources.neuromorpho import (
    NeuroMorphoError,
    download_swc,
    get_neuron,
    list_neurons,
    swc_url,
)


def _network_available() -> bool:
    try:
        requests.get("https://neuromorpho.org/api/neuron/id/1", timeout=10)
        return True
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not _network_available(),
    reason="neuromorpho.org unreachable; live integration tests skipped",
)


def test_get_neuron_returns_real_record_for_id_1():
    """Neuron 1 (cnic_001) is a Wearne_Hof Rhesus monkey prefrontal pyramidal.

    These values are stable upstream metadata; if the test fails, either the
    upstream API changed or our parser dropped a field.
    """
    neuron = get_neuron(1)
    assert neuron.neuron_id == 1
    assert neuron.neuron_name == "cnic_001"
    assert neuron.archive == "Wearne_Hof"
    assert neuron.species == "monkey"
    assert "neocortex" in neuron.brain_region
    assert "pyramidal" in neuron.cell_type
    assert "10.1093/cercor/13.9.950" in neuron.reference_doi


def test_list_neurons_returns_a_page():
    page = list_neurons(page=0, size=3)
    assert len(page) == 3
    assert all(n.neuron_id > 0 for n in page)
    assert all(n.neuron_name for n in page)
    assert all(n.archive for n in page)


def test_swc_url_format():
    assert swc_url("cnic_001", "Wearne_Hof") == (
        "https://neuromorpho.org/dableFiles/wearne_hof/CNG%20version/cnic_001.CNG.swc"
    )


def test_download_and_parse_real_swc_for_neuron_1():
    text = download_swc("cnic_001", "Wearne_Hof")
    assert text.strip().startswith("#") or text.strip()[0].isdigit()
    morphology = parse_swc(text)
    assert len(morphology) > 100
    assert len(morphology.soma_points) >= 1
    # neuron 1 is "Dendrites, Soma, No Axon" per upstream metadata
    assert len(morphology.axon_points) == 0
    assert len(morphology.dendrite_points) > 100


def test_download_swc_404_raises():
    with pytest.raises(NeuroMorphoError):
        download_swc("definitely-not-a-real-neuron-zzz", "nonexistent_archive")
