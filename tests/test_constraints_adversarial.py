"""Adversarial checks stay synthetic and never alter the public case."""
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import socket

import pytest

from bve._schemas import schema_validator
from bve.constraints import ConstraintError, compute_constraints, load_project
from bve.constraints.export import result_bytes, write_output
from bve.geometry import GeometryError, load_normalized_geometry
from bve.geometry.export import json_bytes, normalized_feature
from bve.geometry import read_dxf, read_geojson


def result(project, geometry):
    return compute_constraints(load_project(json.dumps(project)),
        load_normalized_geometry(json.dumps(geometry)), area_basis="declared_project_area")


@pytest.mark.parametrize("damage", ["computed-null", "unavailable-value", "absent-value", "promoted-null",
    "computed-null-input", "unavailable-numeric-input", "missing-trace", "bad-reference", "null-selected-area"])
def test_output_schema_rejects_state_and_trace_contradictions(project_document, normalized_document, damage):
    data = result(project_document, normalized_document).to_dict()
    coverage = data["constraints"]["buildingCoverage"]
    if damage == "computed-null":
        coverage["maxFootprintAreaM2"] = None
    elif damage == "unavailable-value":
        coverage["state"] = "UNAVAILABLE"
    elif damage == "absent-value":
        data["constraints"]["height"]["state"] = "ABSENT"
    elif damage == "promoted-null":
        coverage.update(state="UNAVAILABLE", maxFootprintAreaM2=None)
        coverage["provenance"][1]["condition"].update(value=None, status="official_verified")
    elif damage == "computed-null-input":
        coverage["provenance"][1]["condition"].update(value=None, status="unknown")
    elif damage == "unavailable-numeric-input":
        coverage.update(state="UNAVAILABLE", maxFootprintAreaM2=None)
    elif damage == "missing-trace":
        coverage["provenance"].pop(0)
    elif damage == "bad-reference":
        data["inputReferences"]["project"] = "synthetic-private-filename"
    elif damage == "null-selected-area":
        data["areaBasis"]["declaredAreaM2"] = None
    assert not schema_validator("constraints").is_valid(data)


def test_all_null_conditions_preserve_individual_unavailability(project_document, normalized_document):
    for condition in project_document["zoning"].values():
        condition.update(value=None, status="review_required")
    computed = result(project_document, normalized_document)
    assert all(item.state == "UNAVAILABLE" and item.value is None for item in
               (computed.building_coverage, computed.floor_area_ratio, computed.height))
    schema_validator("constraints").validate(computed.to_dict())


def test_small_lexemes_remain_exact_without_underflow(project_document, normalized_document):
    text = json.dumps(project_document).replace('"value": 200', '"value": 1e-1024').replace('"value": 600', '"value": 1e-1024')
    computed = compute_constraints(load_project(text), load_normalized_geometry(json.dumps(normalized_document)),
                                   area_basis="declared_project_area")
    assert computed.building_coverage.value == Decimal("8e-1025")
    assert computed.floor_area_ratio.value == Decimal("1e-2050")
    decoded = json.loads(result_bytes(computed), parse_float=Decimal)
    assert decoded["constraints"]["floorAreaRatio"]["maxTotalFloorAreaM2"] == Decimal("1e-2050")


def test_maximum_coefficient_is_exact_and_bounded(project_document, normalized_document):
    coefficient = "9" * 1024
    text = json.dumps(project_document).replace('"value": 200', '"value": ' + coefficient)
    computed = compute_constraints(load_project(text), load_normalized_geometry(json.dumps(normalized_document)),
                                   area_basis="declared_project_area")
    assert computed.floor_area_ratio.value == Decimal(int(coefficient) * 6)
    assert len(result_bytes(computed)) < 32 * 1024


def test_schema_references_are_offline(project_document, normalized_document, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("synthetic-network-forbidden")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    schema_validator.cache_clear()
    encoded = result_bytes(result(project_document, normalized_document))
    assert json.loads(encoded)["constraints"]["height"]["maxHeightM"] == 31


@pytest.mark.parametrize("kind", ["geojson", "dxf"])
def test_existing_geometry_producers_feed_constraint_consumer(project_document, kind):
    case = Path(__file__).resolve().parents[1] / "cases/example-urban-office"
    raw = (case / f"site.{kind}").read_bytes()
    original = read_geojson(raw) if kind == "geojson" else read_dxf(raw, layer="SITE")
    site = load_normalized_geometry(json_bytes(normalized_feature(original)))
    computed = compute_constraints(load_project(json.dumps(project_document)), site, area_basis="geometry_area")
    assert (computed.building_coverage.value, computed.floor_area_ratio.value, computed.height.value) == (160, 1200, 31)
    assert site.source_status == original.source_status and site.source_unit == original.source_unit


def test_export_write_failure_is_fixed_and_does_not_report_pass(project_document, normalized_document, tmp_path, monkeypatch):
    computed = result(project_document, normalized_document)
    output = tmp_path / "synthetic-failed-output.json"
    original_open = Path.open
    class FailingWriter:
        def __enter__(self):
            self.stream = original_open(output, "xb")
            return self
        def write(self, data):
            self.stream.write(data[:8])
            raise OSError("synthetic-private-write-diagnostic")
        def __exit__(self, *args):
            self.stream.close()
    def patched_open(path, *args, **kwargs):
        return FailingWriter() if path == output and args and args[0] == "xb" else original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", patched_open)
    with pytest.raises(ConstraintError, match="^IO_ERROR$"):
        write_output(computed, output)
    assert output.read_bytes() == result_bytes(computed)[:8]


def test_cli_unexpected_exception_is_non_disclosing(project_document, normalized_document, tmp_path, monkeypatch, capsys):
    import bve.constraints.__main__ as cli
    source = tmp_path / "synthetic-private-project.json"
    source.write_text(json.dumps(project_document), encoding="utf-8")
    def fail(*args):
        raise RuntimeError("synthetic-private-internal-diagnostic")
    monkeypatch.setattr(cli, "load_project", fail)
    assert cli.main(["--project", str(source), "--geometry", "synthetic-private-missing", "--area-basis", "geometry_area"]) == 2
    captured = capsys.readouterr()
    assert captured.out == "FAIL code=INTERNAL_ERROR\n" and captured.err == ""


def test_export_nonfinite_model_value_is_fixed_failure(project_document, normalized_document):
    computed = result(project_document, normalized_document)
    invalid = replace(computed, building_coverage=replace(computed.building_coverage, value=Decimal("NaN")))
    with pytest.raises(ConstraintError, match="^NUMERIC_RANGE$"):
        result_bytes(invalid)


@pytest.mark.parametrize("value", [1, 0, None, "true"])
def test_normalized_valid_flag_is_not_truthiness(normalized_document, value):
    normalized_document["properties"]["valid"] = value
    with pytest.raises(GeometryError, match="^NORMALIZED_SCHEMA_INVALID$"):
        load_normalized_geometry(json.dumps(normalized_document))
