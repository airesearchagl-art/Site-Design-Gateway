"""Synthetic numeric/state cases with independent expected values."""
from dataclasses import FrozenInstanceError
from decimal import Decimal, FloatOperation, ROUND_FLOOR, localcontext
import json

import pytest

from bve._schemas import schema_validator
from bve.constraints import compute_constraints, load_project
from bve.geometry import load_normalized_geometry


def compute(project, geometry, basis="declared_project_area"):
    return compute_constraints(load_project(json.dumps(project)), load_normalized_geometry(json.dumps(geometry)),
                               area_basis=basis)


@pytest.mark.parametrize("basis", ["declared_project_area", "geometry_area"])
def test_synthetic_caps_and_output_schema(project_document, normalized_document, basis):
    result = compute(project_document, normalized_document, basis)
    assert result.building_coverage.value == Decimal(160)
    assert result.floor_area_ratio.value == Decimal(1200)
    assert result.height.value == Decimal(31)
    assert result.review_required is True
    assert result.difference_m2 == 0
    schema_validator("constraints").validate(result.to_dict())
    assert [item.calculation_id for item in (result.building_coverage, result.floor_area_ratio, result.height)] == [
        "coverage_area_cap_v0.1", "floor_area_cap_v0.1", "height_cap_v0.1"]


@pytest.mark.parametrize("basis,area,footprint,floor", [
    ("declared_project_area", "200", "160", "1200"), ("geometry_area", "198", "158.4", "1188")])
def test_area_divergence_preserves_explicit_selection(project_document, normalized_document, basis, area, footprint, floor):
    normalized_document["geometry"]["coordinates"] = [[[0, 0], [9.9, 0], [9.9, 20], [0, 20], [0, 0]]]
    normalized_document["properties"].update(areaM2=198, bounds=[0, 0, 9.9, 20])
    result = compute(project_document, normalized_document, basis)
    assert result.area.declared_area_m2 == 200 and result.area.geometry_area_m2 == 198
    assert result.area.basis_area_m2 == Decimal(area) and result.difference_m2 == Decimal(2)
    assert result.building_coverage.value == Decimal(footprint)
    assert result.floor_area_ratio.value == Decimal(floor)


def test_difference_is_signed_evidence_with_no_threshold(project_document, normalized_document):
    project_document["site"]["area"].update(value=198, status="official_verified")
    for condition in project_document["zoning"].values():
        condition["status"] = "official_verified"
    normalized_document["properties"]["sourceStatus"] = "official_verified"
    result = compute(project_document, normalized_document)
    assert result.difference_m2 == -2 and result.area.basis_area_m2 == 198
    assert result.review_required is False


@pytest.mark.parametrize("field,attribute", [("buildingCoverageRatio", "building_coverage"),
    ("floorAreaRatio", "floor_area_ratio"), ("heightLimit", "height")])
def test_null_constraint_is_individually_unavailable(project_document, normalized_document, field, attribute):
    project_document["zoning"][field].update(value=None, status="unknown")
    result = compute(project_document, normalized_document)
    constraint = getattr(result, attribute)
    assert constraint.state == "UNAVAILABLE" and constraint.value is None and constraint.review_required
    assert constraint.provenance[-1].condition.value is None
    others = {"building_coverage", "floor_area_ratio", "height"} - {attribute}
    assert all(getattr(result, name).state == "COMPUTED" for name in others)
    schema_validator("constraints").validate(result.to_dict())


def test_missing_height_is_absent(project_document, normalized_document):
    del project_document["zoning"]["heightLimit"]
    result = compute(project_document, normalized_document)
    assert result.height.state == "ABSENT" and result.height.value is None
    assert result.height.provenance == () and result.height.review_required is False
    schema_validator("constraints").validate(result.to_dict())


def test_null_unselected_declared_area_is_preserved(project_document, normalized_document):
    project_document["site"]["area"].update(value=None, status="review_required")
    result = compute(project_document, normalized_document, "geometry_area")
    assert result.area.declared_area_m2 is None and result.difference_m2 is None
    assert result.building_coverage.value == 160 and result.review_required
    schema_validator("constraints").validate(result.to_dict())


def test_zero_ratios_are_computed(project_document, normalized_document):
    for field in ("buildingCoverageRatio", "floorAreaRatio"):
        project_document["zoning"][field]["value"] = 0
    result = compute(project_document, normalized_document)
    assert result.building_coverage.state == result.floor_area_ratio.state == "COMPUTED"
    assert result.building_coverage.value == result.floor_area_ratio.value == 0


def test_decimal_arithmetic_not_float_or_ambient_precision(project_document, normalized_document):
    payload = json.dumps(project_document).replace('"value": 80', '"value": 80.12345678901234567890123456789')
    project, geometry = load_project(payload), load_normalized_geometry(json.dumps(normalized_document))
    baseline = compute_constraints(project, geometry, area_basis="declared_project_area")
    assert baseline.building_coverage.value == Decimal("160.24691357802469135780246913578")
    with localcontext() as context:
        context.prec = 2
        context.Emax, context.Emin = 2, -2
        context.rounding = ROUND_FLOOR
        context.traps[FloatOperation] = True
        before = str(context)
        result = compute_constraints(project, geometry, area_basis="declared_project_area")
        assert result == baseline
        assert str(context) == before


def test_result_and_nested_provenance_are_immutable(project_document, normalized_document):
    result = compute(project_document, normalized_document)
    with pytest.raises(FrozenInstanceError):
        result.building_coverage.value = Decimal(999)
    with pytest.raises(FrozenInstanceError):
        result.building_coverage.provenance[1].condition.status = "official_verified"
    detached = result.to_dict()
    detached["constraints"]["floorAreaRatio"]["provenance"][1]["condition"]["status"] = "official_verified"
    assert result.to_dict()["constraints"]["floorAreaRatio"]["provenance"][1]["condition"]["status"] == "llm_researched"
