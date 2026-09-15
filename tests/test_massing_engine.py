"""Full synthetic candidate and independent integer arithmetic oracles."""
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, FloatOperation, Inexact, localcontext
from fractions import Fraction
import json

import pytest

from bve._schemas import schema_validator
from bve.constraints import compute_constraints, load_constraint_result, load_project
from bve.constraints.export import _encode, result_bytes
from bve.geometry import load_normalized_geometry
from bve.massing import MassingError, generate_massing_candidate
from bve.massing import engine
from bve.massing.export import candidate_bytes


def make(project, normalized, floor_height=4):
    site = load_normalized_geometry(json.dumps(normalized))
    constraints = compute_constraints(load_project(_encode(project)), site, area_basis="declared_project_area")
    return generate_massing_candidate(site, load_constraint_result(result_bytes(constraints)), floor_height_m=floor_height)


def test_synthetic_candidate(project_document, normalized_document):
    candidate = make(project_document, normalized_document)
    assert candidate.target_footprint_area_m2 == 160
    assert Decimal("159.999999999") < candidate.footprint_area_m2 <= 160
    assert candidate.footprint_area_m2 == Decimal(str(candidate.footprint.area))
    assert candidate.floor_count == 7 and candidate.floor_height_m == 4 and candidate.height_m == 28
    assert candidate.gross_floor_area_m2 == candidate.footprint_area_m2 * 7 <= 1200
    assert candidate.site.polygon.covers(candidate.footprint)
    assert candidate.review_required is True
    data = candidate.to_dict()
    schema_validator("massing").validate(data)
    assert data["generator"] == {"strategy": "max_footprint_stack_v0.1",
        "footprintMethod": "convex_homothetic_footprint_v0.1", "floorHeightM": Decimal(4),
        "floorHeightStatus": "user_provided"}
    assert data["inputReferences"]["geometry"] == candidate.site.source_reference
    assert data["inputReferences"]["project"] == candidate.constraints.result.project_reference
    assert data["inputReferences"]["constraints"] == candidate.constraints.reference


def test_no_default_floor_height_in_public_api(project_document, normalized_document):
    candidate = make(project_document, normalized_document)
    with pytest.raises(MassingError, match="^FLOOR_HEIGHT_REQUIRED$"):
        generate_massing_candidate(candidate.site, candidate.constraints)


def test_footprint_cap_above_site_never_expands(project_document, normalized_document):
    project_document["site"]["area"]["value"] = 1000
    candidate = make(project_document, normalized_document)
    assert candidate.constraints.result.building_coverage.value == 800
    assert candidate.footprint.equals(candidate.site.polygon)
    assert candidate.target_footprint_area_m2 == candidate.footprint_area_m2 == 200


def test_far_smaller_than_bcr_limits_first_floor(project_document, normalized_document):
    project_document["zoning"]["floorAreaRatio"]["value"] = 20
    candidate = make(project_document, normalized_document)
    assert candidate.target_footprint_area_m2 == 40
    assert candidate.footprint_area_m2 <= 40
    assert candidate.floor_count == 1 and candidate.gross_floor_area_m2 <= 40


@pytest.mark.parametrize("field", ["buildingCoverageRatio", "floorAreaRatio"])
def test_zero_capacity(project_document, normalized_document, field):
    project_document["zoning"][field]["value"] = 0
    with pytest.raises(MassingError, match="^NO_MASSING_CAPACITY$"):
        make(project_document, normalized_document)


def test_no_feasible_floor(project_document, normalized_document):
    with pytest.raises(MassingError, match="^NO_FEASIBLE_MASSING$"):
        make(project_document, normalized_document, 32)


@pytest.mark.parametrize("cap,divisor", [("1200", "159.99999999999997"), ("31", "4"),
    ("30.999999999999999999999999999999999999999", "1"),
    ("0.99999999999999999999999999999", "1"), ("1e-1024", "3e-1024"),
    ("1e1024", "3e-1024"), ("7", "0.1"), ("1.4", "0.2")])
def test_floor_quotient_independent_fraction_oracle(cap, divisor):
    expected = Fraction(cap) // Fraction(divisor)
    with localcontext() as context:
        context.prec, context.Emin, context.Emax = 1, -1, 1
        context.traps[Inexact] = context.traps[FloatOperation] = True
        assert engine._floor_quotient(Decimal(cap), Decimal(divisor)) == expected


@pytest.mark.parametrize("height", [".1", "3.75", "4.429", "31", "0.00000001"])
def test_floors_match_independent_caps(project_document, normalized_document, height):
    candidate = make(project_document, normalized_document, height)
    by_far = Fraction(1200) // Fraction(candidate.footprint_area_m2)
    by_height = Fraction(31) // Fraction(height)
    assert candidate.floor_count == min(by_far, by_height)


@pytest.mark.parametrize("floors,ok", [(10000, True), (10001, False)])
def test_resource_floor_limit_not_silent_clamp(project_document, normalized_document, floors, ok):
    project_document["zoning"]["floorAreaRatio"]["value"] = floors * 100
    project_document["zoning"]["heightLimit"]["value"] = floors
    if ok:
        assert make(project_document, normalized_document, 1).floor_count == floors
    else:
        with pytest.raises(MassingError, match="^RESOURCE_LIMIT$"):
            make(project_document, normalized_document, 1)


def test_final_bcr_cap_guard_survives_faulty_geometry_stage(project_document, normalized_document, monkeypatch):
    candidate = make(project_document, normalized_document)
    # Fault injection makes the geometry stage return a plausible positive
    # actual area above BCR, while other final caps/floor count still fit.
    monkeypatch.setattr(engine, "_check_footprint", lambda *args: Decimal(161))
    with pytest.raises(MassingError, match="^GEOMETRY_GENERATION_FAILED$"):
        engine._validate_candidate(candidate)


def test_final_far_cap_guard_survives_faulty_floor_count(project_document, normalized_document, monkeypatch):
    candidate = replace(make(project_document, normalized_document, floor_height=3), floor_count=8)
    result = candidate.constraints.result
    actual = candidate.footprint_area_m2
    assert actual.is_finite() and 0 < actual <= result.building_coverage.value
    assert candidate.footprint.is_valid and not candidate.footprint.interiors
    assert candidate.footprint.equals(candidate.footprint.convex_hull)
    assert candidate.site.polygon.covers(candidate.footprint)
    assert candidate.target_footprint_area_m2 == min(
        Decimal(str(candidate.site.area_m2)), result.building_coverage.value, result.floor_area_ratio.value)
    assert actual <= candidate.target_footprint_area_m2
    assert candidate.height_m == 24 < result.height.value
    assert candidate.gross_floor_area_m2 == actual * 8 > result.floor_area_ratio.value
    assert candidate.site.source_reference == result.geometry_reference
    assert type(candidate.floor_count) is int and 1 <= candidate.floor_count <= engine.MAX_FLOORS
    # Only neutralize floor-count consistency; the final FAR cap must still reject.
    monkeypatch.setattr(engine, "_floor_count", lambda *args: 8)
    assert engine._floor_count(result, actual, candidate.floor_height_m) == candidate.floor_count
    with pytest.raises(MassingError, match="^GEOMETRY_GENERATION_FAILED$"):
        engine._validate_candidate(candidate)


def test_final_height_cap_guard_survives_faulty_floor_count(project_document, normalized_document, monkeypatch):
    candidate = replace(make(project_document, normalized_document, floor_height=Decimal("4.5")), floor_count=7)
    result = candidate.constraints.result
    actual = candidate.footprint_area_m2
    assert actual.is_finite() and 0 < actual <= result.building_coverage.value
    assert candidate.footprint.is_valid and not candidate.footprint.interiors
    assert candidate.footprint.equals(candidate.footprint.convex_hull)
    assert candidate.site.polygon.covers(candidate.footprint)
    assert candidate.target_footprint_area_m2 == min(
        Decimal(str(candidate.site.area_m2)), result.building_coverage.value, result.floor_area_ratio.value)
    assert actual <= candidate.target_footprint_area_m2
    assert candidate.gross_floor_area_m2 == actual * 7 < result.floor_area_ratio.value
    assert candidate.height_m == Decimal("31.5") > result.height.value
    assert candidate.site.source_reference == result.geometry_reference
    assert type(candidate.floor_count) is int and 1 <= candidate.floor_count <= engine.MAX_FLOORS
    # Only neutralize floor-count consistency; the final height cap must still reject.
    monkeypatch.setattr(engine, "_floor_count", lambda *args: 7)
    assert engine._floor_count(result, actual, candidate.floor_height_m) == candidate.floor_count
    with pytest.raises(MassingError, match="^GEOMETRY_GENERATION_FAILED$"):
        engine._validate_candidate(candidate)


def test_metrics_and_export_independent_of_ambient_context(project_document, normalized_document):
    original = make(project_document, normalized_document, "4.00000000000000000000001")
    baseline = candidate_bytes(original)
    with localcontext() as context:
        context.prec, context.Emin, context.Emax = 1, -1, 1
        context.traps[Inexact] = context.traps[FloatOperation] = True
        before = str(context)
        actual = make(project_document, normalized_document, "4.00000000000000000000001")
        assert candidate_bytes(actual) == baseline
        assert str(context) == before


def test_candidate_immutable_and_export_rechecks_caps(project_document, normalized_document):
    candidate = make(project_document, normalized_document)
    with pytest.raises(FrozenInstanceError):
        candidate.floor_count = 8
    with pytest.raises(MassingError, match="^GEOMETRY_GENERATION_FAILED$"):
        candidate_bytes(replace(candidate, floor_count=8))
    detached = candidate.to_dict()
    detached["candidate"]["reviewRequired"] = False
    assert candidate.review_required
