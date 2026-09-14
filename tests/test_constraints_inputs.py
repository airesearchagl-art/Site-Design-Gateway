"""Project input retains exact decimals and requires an explicit area source."""
from dataclasses import FrozenInstanceError
from decimal import Decimal
from hashlib import sha256
import json

import pytest

from bve.constraints import ConstraintError, load_project
from bve.constraints.inputs import select_area
from bve.geometry import load_normalized_geometry


@pytest.mark.parametrize("as_bytes", [False, True])
@pytest.mark.parametrize("indent", [None, 2])
def test_project_exact_bytes_and_private_metadata_stripped(project_document, as_bytes, indent):
    project_document["project"]["name"] = "合成・非公開マーカー"
    text = json.dumps(project_document, ensure_ascii=False, indent=indent) + "\r\n"
    raw = text.encode("utf-8")
    project = load_project(raw if as_bytes else text)
    assert project.reference == "sha256:" + sha256(raw).hexdigest()
    assert project.area.value == Decimal(200)
    assert type(project.coverage.value) is Decimal
    assert "合成" not in repr(project)
    with pytest.raises(FrozenInstanceError):
        project.area.value = Decimal(1)


def test_project_decimal_lexeme_preserved(project_document):
    text = json.dumps(project_document).replace('"value": 80', '"value": 80.12345678901234567890123456789')
    assert load_project(text).coverage.value == Decimal("80.12345678901234567890123456789")


@pytest.mark.parametrize("basis", ["declared_project_area", "geometry_area"])
def test_selected_area(project_document, normalized_document, basis):
    selected = select_area(load_project(json.dumps(project_document)),
                           load_normalized_geometry(json.dumps(normalized_document)), basis)
    assert selected.basis_area_m2 == selected.declared_area_m2 == selected.geometry_area_m2 == 200
    assert selected.selected_basis == basis


@pytest.mark.parametrize("basis,code", [(None, "AREA_BASIS_REQUIRED"), ("", "INVALID_AREA_BASIS"),
    ("auto", "INVALID_AREA_BASIS"), ([], "INVALID_AREA_BASIS"), (False, "INVALID_AREA_BASIS")])
def test_basis_never_selected_implicitly(project_document, normalized_document, basis, code):
    with pytest.raises(ConstraintError, match=f"^{code}$"):
        select_area(load_project(json.dumps(project_document)), load_normalized_geometry(json.dumps(normalized_document)), basis)


def test_selected_null_area_rejects_but_geometry_basis_remains_available(project_document, normalized_document):
    project_document["site"]["area"].update(value=None, status="unknown")
    project = load_project(json.dumps(project_document))
    geometry = load_normalized_geometry(json.dumps(normalized_document))
    with pytest.raises(ConstraintError, match="^AREA_BASIS_UNAVAILABLE$"):
        select_area(project, geometry, "declared_project_area")
    selection = select_area(project, geometry, "geometry_area")
    assert selection.declared_area_m2 is None and selection.basis_area_m2 == 200


@pytest.mark.parametrize("field,value", [("value", -1), ("value", True), ("value", None),
                                       ("unit", "acre"), ("status", "verified")])
def test_project_schema_is_authoritative(project_document, field, value):
    project_document["site"]["area"][field] = value
    with pytest.raises(ConstraintError, match="^PROJECT_SCHEMA_INVALID$"):
        load_project(json.dumps(project_document))


@pytest.mark.parametrize("payload,code", [(None, "INVALID_JSON"), (b"\xff", "INVALID_JSON"),
    ('{"x":1,"x":2}', "INVALID_JSON"), ('{"x":"\\ud800"}', "INVALID_JSON"),
    ('{"x":NaN}', "INVALID_JSON"), ('{"x":1e-1025}', "NUMERIC_RANGE"),
    ('{"x":' + "1" * 1025 + '}', "NUMERIC_RANGE"), (b" " * (256 * 1024 + 1), "INPUT_TOO_LARGE")],
    ids=["type", "utf8", "duplicate-key", "surrogate", "nan", "exponent", "digits", "size"])
def test_project_input_limits(payload, code):
    with pytest.raises(ConstraintError, match=f"^{code}$"):
        load_project(payload)
