"""Explicit design input and immutable input binding, all synthetic."""
from dataclasses import replace
from decimal import Decimal
import json

import pytest

from bve.constraints import compute_constraints, load_constraint_result, load_project
from bve.constraints.export import result_bytes
from bve.geometry import load_normalized_geometry
from bve.massing.engine import _validate_inputs
from bve.massing.errors import MassingError


def inputs(project_document, normalized_document):
    site = load_normalized_geometry(json.dumps(normalized_document))
    result = compute_constraints(load_project(json.dumps(project_document)), site, area_basis="declared_project_area")
    return site, load_constraint_result(result_bytes(result))


def test_geometry_reference_mismatch_even_same_shape(project_document, normalized_document):
    site, result = inputs(project_document, normalized_document)
    different = load_normalized_geometry(json.dumps(normalized_document, indent=4))
    assert different.area_m2 == site.area_m2 and different.bounds == site.bounds
    with pytest.raises(MassingError, match="^INPUT_REFERENCE_MISMATCH$"):
        _validate_inputs(different, result, 4)


def test_binding_includes_geometry_status(project_document, normalized_document):
    site, result = inputs(project_document, normalized_document)
    with pytest.raises(MassingError, match="^INPUT_GEOMETRY_MISMATCH$"):
        _validate_inputs(replace(site, source_status="official_verified"), result, 4)


@pytest.mark.parametrize("value", [0, -1, "NaN", "Infinity", "-Infinity", float("nan"),
    float("inf"), Decimal("sNaN"), True, [], {}, "", "4 m", "4_0", " 4", "1e1025", "1" * 1025])
def test_invalid_floor_height(project_document, normalized_document, value):
    with pytest.raises(MassingError, match="^INVALID_FLOOR_HEIGHT$"):
        _validate_inputs(*inputs(project_document, normalized_document), value)


def test_missing_floor_height(project_document, normalized_document):
    with pytest.raises(MassingError, match="^FLOOR_HEIGHT_REQUIRED$"):
        _validate_inputs(*inputs(project_document, normalized_document), None)


@pytest.mark.parametrize("value", [4, 4.0, Decimal("4.00"), "4e0", "+4.0", ".4e1"])
def test_explicit_floor_height(project_document, normalized_document, value):
    assert _validate_inputs(*inputs(project_document, normalized_document), value)[0] == 4


@pytest.mark.parametrize("field", ["buildingCoverageRatio", "floorAreaRatio", "heightLimit", "absent"])
def test_required_constraints(project_document, normalized_document, field):
    if field == "absent":
        del project_document["zoning"]["heightLimit"]
    else:
        project_document["zoning"][field].update(value=None, status="unknown")
    with pytest.raises(MassingError, match="^REQUIRED_CONSTRAINT_UNAVAILABLE$"):
        _validate_inputs(*inputs(project_document, normalized_document), 4)


def test_raw_dict_and_unvalidated_model_rejected(project_document, normalized_document):
    site, validated = inputs(project_document, normalized_document)
    for raw in (validated.result, validated.result.to_dict(), None):
        with pytest.raises(MassingError, match="^INVALID_ARGUMENTS$"):
            _validate_inputs(site, raw, 4)
