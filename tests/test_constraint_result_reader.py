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
