"""Consumer integrity checks against real Phase 2 synthetic exports."""
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext
from hashlib import sha256
import json

import pytest

from bve._schemas import schema_validator
from bve.constraints import ConstraintError, compute_constraints, load_constraint_result, load_project
from bve.constraints.export import _encode, result_bytes
from bve.geometry import load_normalized_geometry


def exported(project_document, normalized_document, basis="declared_project_area"):
    return compute_constraints(load_project(_encode(project_document)),
                               load_normalized_geometry(json.dumps(normalized_document)), area_basis=basis)


@pytest.mark.parametrize("basis", ["declared_project_area", "geometry_area"])
def test_reader_roundtrip_and_canonical_reference(project_document, normalized_document, basis):
    result = exported(project_document, normalized_document, basis)
    raw = result_bytes(result)
    validated = load_constraint_result(raw)
    assert validated.result == result
    assert validated.reference == "sha256:" + sha256(raw).hexdigest()
    assert load_constraint_result(json.dumps(json.loads(raw), indent=4)) == validated
    with pytest.raises(FrozenInstanceError):
        validated.reference = "changed"
    with pytest.raises(FrozenInstanceError):
        validated.result.height.value = 0


@pytest.mark.parametrize("key,value_key", [("buildingCoverage", "maxFootprintAreaM2"),
    ("floorAreaRatio", "maxTotalFloorAreaM2"), ("height", "maxHeightM")])
def test_schema_valid_derived_tampering_rejected(project_document, normalized_document, key, value_key):
    data = exported(project_document, normalized_document).to_dict()
    data["constraints"][key][value_key] += Decimal(1)
    assert schema_validator("constraints").is_valid(data)
    with pytest.raises(ConstraintError, match="^CONSTRAINT_SEMANTIC_MISMATCH$"):
        load_constraint_result(_encode(data))


def test_reader_preserves_extreme_phase2_derived_output(project_document, normalized_document):
    project_document["site"]["area"]["value"] = Decimal("1e-1024")
    project_document["zoning"]["floorAreaRatio"]["value"] = Decimal("1e-1024")
    result = exported(project_document, normalized_document)
    assert result.floor_area_ratio.value == Decimal("1e-2050")
    with localcontext() as context:
        context.prec, context.Emin, context.Emax = 2, -2, 2
        assert load_constraint_result(result_bytes(result)).result == result


@pytest.mark.parametrize("path,value", [
    (("areaBasis", "basisAreaM2"), 201),
    (("areaBasis", "declaredAreaM2"), 201),
    (("areaBasis", "geometryAreaM2"), 201),
    (("areaBasis", "differenceM2"), 1),
    (("areaBasis", "provenance", 0, "reference"), "sha256:" + "f" * 64),
    (("areaBasis", "provenance", 1, "reference"), "sha256:" + "f" * 64),
    (("constraints", "buildingCoverage", "provenance", 1, "reference"), "sha256:" + "f" * 64),
    (("constraints", "floorAreaRatio", "provenance", 0, "condition", "status"), "official_verified"),
    (("constraints", "height", "provenance", 0, "reference"), "sha256:" + "f" * 64),
    (("constraints", "height", "provenance", 0, "condition", "value"), 32),
    (("constraints", "buildingCoverage", "reviewRequired"), False),
    (("constraints", "floorAreaRatio", "reviewRequired"), True),
    (("constraints", "height", "reviewRequired"), False),
    (("reviewRequired",), False),
    (("inputReferences", "geometry"), "sha256:" + "f" * 64),
    (("inputReferences", "project"), "sha256:" + "f" * 64),
])
def test_schema_valid_semantic_tampering(project_document, normalized_document, path, value):
    data = exported(project_document, normalized_document).to_dict()
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert schema_validator("constraints").is_valid(data)
    with pytest.raises(ConstraintError, match="^CONSTRAINT_SEMANTIC_MISMATCH$"):
        load_constraint_result(_encode(data))


@pytest.mark.parametrize("key", ["buildingCoverage", "floorAreaRatio", "height"])
@pytest.mark.parametrize("change", ["calculationId", "state", "unit", "extra"])
def test_structural_tampering(project_document, normalized_document, key, change):
    data = exported(project_document, normalized_document).to_dict()
    item = data["constraints"][key]
    if change == "unit":
        item["provenance"][-1]["condition"]["unit"] = "mm"
    elif change == "extra":
        item["extra"] = True
    else:
        item[change] = "ABSENT" if change == "state" else "other_v0.1"
    with pytest.raises(ConstraintError, match="^CONSTRAINT_SCHEMA_INVALID$"):
        load_constraint_result(_encode(data))


@pytest.mark.parametrize("field", ["buildingCoverageRatio", "floorAreaRatio", "heightLimit", "absent", "area"])
def test_unavailable_absent_and_unselected_null_are_valid(project_document, normalized_document, field):
    if field == "absent":
        del project_document["zoning"]["heightLimit"]
    elif field == "area":
        project_document["site"]["area"].update(value=None, status="unknown")
    else:
        project_document["zoning"][field].update(value=None, status="unknown")
    result = exported(project_document, normalized_document, "geometry_area")
    assert load_constraint_result(result_bytes(result)).result == result


@pytest.mark.parametrize("payload,code", [(b'{"a":1,"a":2}', "INVALID_JSON"),
    (b'{"a":NaN}', "INVALID_JSON"), (b'{"a":Infinity}', "INVALID_JSON"),
    (b'\xef\xbb\xbf{}', "INVALID_JSON"), (b'\xff', "INVALID_JSON"),
    ('{"a":"\\ud800"}', "INVALID_JSON"), ('[' * 33 + '0' + ']' * 33, "INVALID_JSON"),
    ('{"a":1e8193}', "NUMERIC_RANGE"), ('{"a":' + '1' * 8193 + '}', "NUMERIC_RANGE"),
    (b' ' * (4 * 1024 * 1024 + 1), "INPUT_TOO_LARGE"), ({}, "INVALID_JSON"),
    ('{}', "CONSTRAINT_SCHEMA_INVALID")], ids=["duplicate", "nan", "infinity", "bom", "utf8",
        "surrogate", "depth", "exponent", "digits", "size", "type", "schema"])
def test_reader_bounded_strict_json(payload, code):
    with pytest.raises(ConstraintError, match=f"^{code}$"):
        load_constraint_result(payload)
