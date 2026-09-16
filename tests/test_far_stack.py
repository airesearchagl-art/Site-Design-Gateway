"""P10-PROJ / P10-CON: explicit synthetic caps, never legal rule inputs."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

import pytest

from bve._schemas import schema_validator
from bve.constraints import ConstraintError, compute_constraints, load_constraint_result, load_project
from bve.constraints.export import canonical_json_bytes, project_bytes, result_bytes
from bve.constraints.model import REVIEW_STATUSES
from bve.geometry import load_normalized_geometry, read_geojson
from bve.geometry.export import json_bytes, normalized_feature
from bve.validation import validate_json, validate_project

CASE = Path(__file__).resolve().parents[1] / "cases/example-urban-office"


def project():
    return json.loads((CASE / "project-far-stack.json").read_bytes())


def cap(id="road-width-cap", value=400, status="user_provided", kind="road_width_derived"):
    return {"id": id, "kind": kind, "value": value, "unit": "percent", "status": status}


def evaluate(document, *, basis="declared_project_area"):
    geometry = load_normalized_geometry(json_bytes(normalized_feature(read_geojson((CASE / "site.geojson").read_bytes()))))
    validated = load_project(canonical_json_bytes(document))
    result = compute_constraints(validated, geometry, area_basis=basis)
    return geometry, load_constraint_result(result_bytes(result))


@pytest.mark.parametrize("caps", [[], [cap()], [cap(), cap("district-cap", 300, kind="district_plan_explicit")]])
def test_project_v2_valid_explicit_stacks(caps):
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"] = caps
    before = deepcopy(value)
    assert validate_project(value).valid
    assert validate_json(json.dumps(value)).valid
    assert load_project(json.dumps(value)).schema_version == "0.2"
    assert value == before


def test_duplicate_cap_id_semantic_guard():
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"] = [cap(), cap(value=300)]
    assert schema_validator("project_v2").is_valid(value)  # Identity uniqueness is semantic.
    assert validate_project(value).code == "duplicate_cap_id"
    with pytest.raises(ConstraintError, match="^DUPLICATE_CAP_ID$"):
        load_project(json.dumps(value))


@pytest.mark.parametrize("change", [
    {"id": "base-zoning"}, {"id": "UPPER"}, {"id": "a" * 81}, {"id": "cap\n"},
    {"value": -1}, {"unit": "m"}, {"kind": "inferred_rule"}, {"description": "synthetic"},
    {"value": None, "status": "user_provided"}, {"value": None, "status": "llm_researched"},
])
def test_project_v2_rejects_invalid_entry(change):
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"][0].update(change)
    assert not validate_project(value).valid
    with pytest.raises(ConstraintError, match="^PROJECT_SCHEMA_INVALID$"):
        load_project(json.dumps(value))


@pytest.mark.parametrize("status", ["unknown", "review_required"])
def test_null_cap_requires_explicit_review(status):
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"] = [cap(value=None, status=status)]
    assert validate_project(value).valid


def test_project_v2_max16_and_no_hidden_default():
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"] = [cap(f"cap-{i}") for i in range(16)]
    assert validate_project(value).valid
    value["zoning"]["additionalFloorAreaRatioCaps"].append(cap("cap-16"))
    assert not validate_project(value).valid
    del value["zoning"]["additionalFloorAreaRatioCaps"]
    assert not validate_project(value).valid


@pytest.mark.parametrize("version", ["0.3", "latest", None, 2])
def test_project_unknown_version_never_falls_back(version):
    value = project()
    value["schemaVersion"] = version
    assert not validate_project(value).valid
    with pytest.raises(ConstraintError, match="^PROJECT_SCHEMA_INVALID$"):
        load_project(json.dumps(value))


@pytest.mark.parametrize("caps,expected,ids", [
    ([], 600, ["base-zoning"]), ([cap(value=400)], 400, ["road-width-cap"]),
    ([cap(value=800)], 600, ["base-zoning"]), ([cap(value=600)], 600, ["base-zoning", "road-width-cap"]),
    ([cap("z-cap", 200), cap("a-cap", 200), cap("middle", 300)], 200, ["z-cap", "a-cap"]),
    ([cap(value=0)], 0, ["road-width-cap"]),
])
def test_effective_min_and_tie_order(caps, expected, ids):
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"] = caps
    _, result = evaluate(value)
    far = result.result.to_dict()["constraints"]["floorAreaRatio"]
    assert far["state"] == "COMPUTED"
    assert far["effectiveCapPercent"] == Decimal(expected)
    assert type(far["effectiveCapPercent"]) is Decimal
    assert far["maxTotalFloorAreaM2"] == Decimal(expected) * 2
    assert far["effectiveCapIds"] == ids
    assert far["calculationId"] == "floor_area_cap_stack_v0.2"
    assert [entry["id"] for entry in far["capStack"]] == ["base-zoning", *(entry["id"] for entry in caps)]


@pytest.mark.parametrize("where", ["base", "first", "last"])
def test_unknown_cap_fails_closed(where):
    value = project()
    caps = [cap("a", 400), cap("b", 300)]
    value["zoning"]["additionalFloorAreaRatioCaps"] = caps
    condition = value["zoning"]["floorAreaRatio"] if where == "base" else caps[0 if where == "first" else 1]
    condition.update(value=None, status="unknown")
    _, result = evaluate(value)
    far = result.result.to_dict()["constraints"]["floorAreaRatio"]
    assert far["state"] == "UNAVAILABLE"
    assert far["effectiveCapPercent"] is None and far["maxTotalFloorAreaM2"] is None
    assert far["effectiveCapIds"] == [] and len(far["capStack"]) == 3
    assert far["reviewRequired"] is True


def test_decimal_equivalence_and_exact_comparison():
    value = project()
    outputs = []
    for number in [Decimal("400"), Decimal("400.00"), Decimal("4e2")]:
        value["zoning"]["additionalFloorAreaRatioCaps"][0]["value"] = number
        with localcontext() as context:
            context.prec = 2
            _, result = evaluate(value)
            outputs.append(result_bytes(result.result))
    assert outputs[0] == outputs[1] == outputs[2]
    value["zoning"]["floorAreaRatio"]["value"] = Decimal("400.0000000000000000001")
    value["zoning"]["additionalFloorAreaRatioCaps"][0]["value"] = Decimal("400.0000000000000000000")
    _, result = evaluate(value)
    assert result.result.floor_area_ratio.effective_cap_ids == ("road-width-cap",)


def test_provenance_preserves_order_kind_status_and_canonical_project_hash():
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"] = [cap("z", 300, "drawing_derived"), cap("a", 400, "user_provided", "other_explicit")]
    loaded = load_project(json.dumps(value, indent=4))
    expected = "sha256:" + sha256(project_bytes(json.dumps(value))).hexdigest()
    assert loaded.reference == expected
    _, result = evaluate(value)
    stack = result.result.to_dict()["constraints"]["floorAreaRatio"]["capStack"]
    assert [e["id"] for e in stack] == ["base-zoning", "z", "a"]
    assert [e["kind"] for e in stack] == ["base_zoning", "road_width_derived", "other_explicit"]
    assert [e["condition"]["status"] for e in stack[1:]] == ["drawing_derived", "user_provided"]
    assert all(e["reference"] == expected for e in stack)
    assert stack[0]["input"] == "zoning.floorAreaRatio"
    assert all(e["input"] == "zoning.additionalFloorAreaRatioCaps" for e in stack[1:])
    before = project_bytes(json.dumps(value))
    value["zoning"]["additionalFloorAreaRatioCaps"].reverse()
    assert project_bytes(json.dumps(value)) != before


@pytest.mark.parametrize("status,review", [("official_verified", False), ("user_provided", False),
    ("drawing_derived", False), ("llm_researched", True), ("assumed", True), ("unknown", True), ("review_required", True)])
@pytest.mark.parametrize("where", ["base", "additional"])
def test_v2_far_review_policy(status, review, where):
    value = project()
    value["site"]["area"]["status"] = "official_verified"
    for key in ("buildingCoverageRatio", "floorAreaRatio", "heightLimit"):
        value["zoning"][key]["status"] = "official_verified"
    source = value["zoning"]["floorAreaRatio"] if where == "base" else value["zoning"]["additionalFloorAreaRatioCaps"][0]
    source["status"] = status
    _, result = evaluate(value)
    far = result.result.to_dict()["constraints"]["floorAreaRatio"]
    assert far["reviewRequired"] == review
    entry = far["capStack"][0 if where == "base" else 1]
    assert entry["reviewRequired"] == review and entry["condition"]["status"] == status
    assert REVIEW_STATUSES == {"assumed", "unknown", "review_required"}


@pytest.mark.parametrize("field,replacement", [("effectiveCapPercent", 300), ("effectiveCapIds", ["base-zoning"]),
    ("maxTotalFloorAreaM2", 600), ("reviewRequired", False)])
def test_constraint_v2_reader_recomputes_effective_fields(field, replacement):
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"][0]["status"] = "assumed"
    _, result = evaluate(value)
    data = result.result.to_dict()
    data["constraints"]["floorAreaRatio"][field] = replacement
    with pytest.raises(ConstraintError, match="^CONSTRAINT_SEMANTIC_MISMATCH$"):
        load_constraint_result(canonical_json_bytes(data))


def test_legacy_project_and_review_policy_are_unchanged():
    raw = (CASE / "project.json").read_bytes()
    data = json.loads(raw)
    assert data["schemaVersion"] == "0.1" and validate_json(raw).valid
    data["zoning"]["floorAreaRatio"]["status"] = "llm_researched"
    _, result = evaluate(data)
    assert result.result.schema_version == "0.1"
    far = result.result.to_dict()["constraints"]["floorAreaRatio"]
    assert far["calculationId"] == "floor_area_cap_v0.1" and "capStack" not in far
    assert result.result.floor_area_ratio.provenance[1].review_required is False
