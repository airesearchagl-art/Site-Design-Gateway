"""Export and subprocess boundary tests use temporary synthetic inputs only."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
import pytest

from bve.geometry import GeometryError, read_geojson
from bve.geometry.export import geometry_summary, json_bytes, normalized_feature, write_outputs

ROOT = Path(__file__).resolve().parents[1]
INPUT = {"type": "Polygon", "unit": "m", "coordinateSystem": "local_xy",
         "coordinates": [[[0, 0], [10, 0], [10, 20], [0, 20], [0, 0]]]}


def run(*args):
    return subprocess.run([sys.executable, "-m", "bve.geometry", *map(str, args)],
                          capture_output=True, text=True, timeout=30)


@pytest.fixture
def source(tmp_path):
    file = tmp_path / "synthetic-private-marker.geojson"
    file.write_text(json.dumps(INPUT), encoding="utf-8")
    return file


@pytest.fixture
def schema_validator():
    schema = json.loads((ROOT / "schemas/sdg-site-geometry-v0.1.schema.json").read_text())
    project = json.loads((ROOT / "schemas/sdg-project-v0.1.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    registry = Registry().with_resource(project["$id"], Resource.from_contents(project))
    return Draft202012Validator(schema, registry=registry)


def test_export_schema_roundtrip_and_deterministic_bytes(tmp_path, schema_validator):
    site = read_geojson(json.dumps(INPUT))
    output = tmp_path / "site.geojson"
    summary = tmp_path / "summary.json"
    write_outputs(site, output=output, summary=summary)
    schema_validator.validate(json.loads(output.read_bytes()))
    assert output.read_bytes() == json_bytes(normalized_feature(site))
    assert read_geojson(output.read_bytes()).polygon.wkb == site.polygon.wkb
    assert json.loads(summary.read_bytes()) == geometry_summary(site)
    assert geometry_summary(site)["areaM2"] == 200
    assert "coordinates" not in json.loads(summary.read_bytes())


@pytest.mark.parametrize("key,value", [("unit", "mm"), ("coordinateSystem", "EPSG:4326"),
                                      ("areaM2", 0), ("valid", False), ("sourceStatus", "verified"),
                                      ("sourceReference", "synthetic-file-path"), ("sourceReference", "sha256:" + "a" * 64 + "\n")])
def test_output_schema_rejects_invalid_contract(schema_validator, key, value):
    data = json.loads(json_bytes(normalized_feature(read_geojson(json.dumps(INPUT)))))
    data["properties"][key] = value
    assert not schema_validator.is_valid(data)


def test_cli_summary_optional_geometry_and_no_disclosure(source, tmp_path):
    output, summary = tmp_path / "site.geojson", tmp_path / "summary.json"
    result = run(source, "--format", "geojson", "--output", output, "--summary", summary)
    assert result.returncode == 0
    assert result.stdout == "PASS code=VALID warnings=0\n" and result.stderr == ""
    assert json.loads(output.read_text())["properties"]["areaM2"] == 200
    assert json.loads(summary.read_text())["bounds"] == [0, 0, 10, 20]
    assert set(p.name for p in tmp_path.iterdir()) == {source.name, output.name, summary.name}


def test_validation_only_creates_no_output(source, tmp_path):
    before = list(tmp_path.iterdir())
    result = run(source, "--format", "geojson")
    assert result.returncode == 0 and result.stderr == ""
    assert list(tmp_path.iterdir()) == before


def test_invalid_input_does_not_create_output(source, tmp_path):
    source.write_text('{"synthetic-private-marker":NaN}')
    output = tmp_path / "out.geojson"
    result = run(source, "--format", "geojson", "--output", output)
    assert result.returncode == 1
    assert result.stdout == "FAIL code=INVALID_JSON\n" and result.stderr == ""
    assert not output.exists()


@pytest.mark.parametrize("extra", [[], ["--format", "secret-format"], ["--secret", "synthetic-private-marker"],
                                   ["--format", "geojson", "--unit", "m"],
                                   ["--format", "geojson", "--layer", "synthetic-private-marker"]])
def test_invalid_arguments_never_echo_values(source, extra):
    result = run(source, *extra)
    assert result.returncode == 2
    assert result.stdout == "FAIL code=INVALID_ARGUMENTS\n" and result.stderr == ""


def test_missing_input_is_private(tmp_path):
    result = run(tmp_path / "synthetic-private-marker", "--format", "geojson")
    assert result.returncode == 2
    assert result.stdout == "FAIL code=IO_ERROR\n" and result.stderr == ""


def test_no_overwrite_input_or_existing_output(source, tmp_path):
    before = source.read_bytes()
    summary = tmp_path / "summary.json"
    result = run(source, "--format", "geojson", "--summary", summary, "--output", source)
    assert result.returncode == 2 and result.stdout == "FAIL code=OUTPUT_EXISTS\n"
    assert source.read_bytes() == before and not summary.exists()


def test_output_alias_and_missing_parent(source, tmp_path):
    output = tmp_path / "out.json"
    result = run(source, "--format", "geojson", "--output", output, "--summary", output)
    assert result.returncode == 2 and result.stdout == "FAIL code=INVALID_ARGUMENTS\n"
    assert not output.exists()
    result = run(source, "--format", "geojson", "--output", output, "--summary", tmp_path / "absent/out.json")
    assert result.returncode == 2 and result.stdout == "FAIL code=IO_ERROR\n"
    assert not output.exists()


def test_help_is_static():
    result = run("--help")
    assert result.returncode == 0 and result.stderr == ""
    assert "python -m bve.geometry" in result.stdout


def test_io_failure_returns_fixed_error_without_native_message(tmp_path, monkeypatch):
    site = read_geojson(json.dumps(INPUT))
    def fail(*args, **kwargs):
        raise OSError("synthetic-private-marker")
    monkeypatch.setattr(Path, "open", fail)
    with pytest.raises(GeometryError, match="^IO_ERROR$"):
        write_outputs(site, output=tmp_path / "out.json")
