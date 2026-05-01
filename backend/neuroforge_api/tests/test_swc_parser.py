"""Unit tests for the SWC parser using real NeuroMorpho data.

The SWC sample below is the first 12 data points of neuron_id=1 (cnic_001,
Wearne_Hof archive) downloaded from
https://neuromorpho.org/dableFiles/wearne_hof/CNG%20version/cnic_001.CNG.swc
on 2026-04-30. These are real reconstructed coordinates, not invented.
"""

from __future__ import annotations

import pytest

from neuroforge_api.parsers.swc import SwcParseError, parse_swc

REAL_CNIC_001_HEAD = """\
# Original file cnic_001.swc edited using StdSwc version 1.31 on 9/25/13.
# Irregularities and fixes documented in cnic_001.swc.std.
#
1 1 0.0 0.0 0.0 8.1498 -1
2 1 0.67 8.12 0.0 8.1498 1
3 1 -0.67 -8.12 0.0 8.1498 1
4 3 1.84 8.82 -6.15 0.76016 1
5 3 2.67 13.15 -6.15 0.78125 4
6 3 3.99 16.64 -6.15 0.78125 5
7 3 5.18 21.35 -7.59 0.78125 6
8 3 5.49 22.63 -8.0 0.28681 7
9 3 7.64 25.9 -8.0 0.3125 8
10 3 8.26 27.73 -8.0 0.3125 9
11 3 8.68 28.94 -8.0 0.3125 10
12 3 9.66 32.14 -8.07 0.3125 11
"""


def test_parse_real_neuromorpho_head():
    morphology = parse_swc(REAL_CNIC_001_HEAD)
    assert len(morphology) == 12

    root = morphology.points[0]
    assert root.id == 1
    assert root.type == 1
    assert root.parent_id == -1
    assert root.x == 0.0 and root.y == 0.0 and root.z == 0.0
    assert root.radius == pytest.approx(8.1498)

    assert len(morphology.soma_points) == 3
    assert len(morphology.dendrite_points) == 9
    assert len(morphology.axon_points) == 0


def test_parse_skips_blank_and_comment_lines():
    text = "# header\n\n   \n1 1 0 0 0 1.0 -1\n"
    morphology = parse_swc(text)
    assert len(morphology) == 1


def test_parse_rejects_wrong_field_count():
    with pytest.raises(SwcParseError, match="7"):
        parse_swc("1 1 0 0 0 1.0\n")


def test_parse_rejects_non_numeric():
    with pytest.raises(SwcParseError, match="numeric"):
        parse_swc("1 1 oops 0 0 1.0 -1\n")


def test_parse_rejects_duplicate_id():
    with pytest.raises(SwcParseError, match="duplicate"):
        parse_swc("1 1 0 0 0 1.0 -1\n1 1 1 1 1 1.0 -1\n")


def test_parse_rejects_forward_parent_reference():
    with pytest.raises(SwcParseError, match="parent_id"):
        parse_swc("1 1 0 0 0 1.0 99\n")


def test_parse_rejects_empty_input():
    with pytest.raises(SwcParseError, match="no data"):
        parse_swc("# only a comment\n\n")
