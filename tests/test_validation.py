"""Synthetic contract and privacy checks; never use runtime project data."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from bve import ValidationResult, validate_json, validate_project
from bve import validation

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "cases" / "example-urban-office" / "project.json"
STATUSES = (
    "official_verified", "user_provided", "drawing_derived", "llm_researched",
    "assumed", "unknown", "review_required",
)


@pytest.fixture
def project():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_synthetic_fixture_passes(project):
    assert validate_project(project) == ValidationResult(True, 0, "valid")
    assert validate_json(SAMPLE.read_bytes()).valid


@pytest.mark.parametrize("ending", ["\n", "\r", "\r\n", "\u2028"])
def test_project_id_ends_at_document_boundary(project, ending):
    project["project"]["id"] = "example" + ending
    assert not validate_json(json.dumps(project)).valid


@pytest.mark.parametrize("name", ["\ud800", "\udfff"])
def test_escaped_lone_surrogate_in_project_name_is_rejected(project, name):
    project["project"]["name"] = name
    assert validate_json(json.dumps(project)).code == "invalid_json"


@pytest.mark.parametrize("name", ["架空の建物", "🏢", "\ufffd"])
def test_valid_unicode_project_names_are_preserved(project, name):
    project["project"]["name"] = name
    assert validate_json(json.dumps(project, ensure_ascii=False)).valid


def test_file_bytes_reject_malformed_utf8_and_bom():
    payload = SAMPLE.read_bytes()
    assert validate_json(payload.replace(b"Example", b"\xffxample")).code == "invalid_json"
    assert validate_json(b"\xef\xbb\xbf" + payload).code == "invalid_json"


def test_sole_schema_is_read_from_repository():
    assert validation.SCHEMA_PATH == ROOT / "schemas" / "sdg-project-v0.1.schema.json"


@pytest.mark.parametrize("status", STATUSES)
def test_every_declared_provenance_status_is_schema_valid(project, status):
    project["site"]["area"]["status"] = status
    before = deepcopy(project)
    assert validate_project(project).valid
    assert project == before


@pytest.mark.parametrize("status", STATUSES)
@pytest.mark.parametrize("location", ["area", "buildingCoverageRatio", "floorAreaRatio", "heightLimit"])
def test_null_requires_review_or_unknown_for_every_measurement(project, status, location):
    value = project["site"][location] if location == "area" else project["zoning"][location]
    value.update(value=None, status=status)
    assert validate_project(project).valid == (status in {"unknown", "review_required"})


@pytest.mark.parametrize(("path", "value"), [
    (("schemaVersion",), "0.2"),
    (("project", "intendedUses"), ["residential"]),
    (("project", "intendedUses"), ["office", "office"]),
    (("site", "area", "status"), "verified"),
    (("site", "area", "unit"), "mm2"),
    (("zoning", "buildingCoverageRatio", "unit"), "ratio"),
    (("zoning", "floorAreaRatio", "unit"), "%"),
    (("zoning", "heightLimit", "unit"), "mm"),
    (("site", "area", "value"), -1),
    (("site", "area", "value"), 0),
    (("site", "area", "value"), True),
    (("zoning", "buildingCoverageRatio", "value"), 100.01),
    (("zoning", "buildingCoverageRatio", "value"), -1),
    (("zoning", "floorAreaRatio", "value"), -1),
    (("zoning", "heightLimit", "value"), 0),
])
def test_invalid_contract_values_are_rejected_without_mutation(project, path, value):
    target = project
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    before = deepcopy(project)
    result = validate_project(project)
    assert not result.valid and result.error_count > 0
    assert result.code == "schema_invalid"
    assert project == before


@pytest.mark.parametrize("path", [
    ("schemaVersion",), ("project",), ("site",), ("zoning",),
    ("project", "id"), ("project", "name"), ("site", "area"),
    ("site", "area", "value"), ("site", "area", "unit"),
    ("site", "area", "status"), ("zoning", "buildingCoverageRatio"),
    ("zoning", "floorAreaRatio"),
])
def test_required_properties_are_enforced(project, path):
    target = project
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    assert not validate_project(project).valid


@pytest.mark.parametrize("path", [(), ("project",), ("site",), ("zoning",), ("site", "area")])
def test_extra_properties_are_rejected(project, path):
    target = project
    for key in path:
        target = target[key]
    target["synthetic-extra-field"] = "synthetic-only"
    assert not validate_project(project).valid


def test_valid_numeric_boundaries_and_optional_fields(project):
    project["site"]["area"]["value"] = 0.0001
    project["zoning"]["buildingCoverageRatio"]["value"] = 100
    project["zoning"]["floorAreaRatio"]["value"] = 0
    del project["zoning"]["heightLimit"]
    del project["project"]["intendedUses"]
    assert validate_project(project).valid
    project["zoning"]["buildingCoverageRatio"]["value"] = 0
    assert validate_project(project).valid


@pytest.mark.parametrize("text", ["", "{", '{"private-synthetic":}', '{"a":1,}', b"\xff", '"\\ud800"'])
def test_malformed_or_invalid_unicode_is_rejected(text):
    assert validate_json(text) == ValidationResult(False, 1, "invalid_json")


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "1e400", "-1e400", "9" * 400])
def test_nonfinite_json_numbers_are_rejected(project, token):
    text = json.dumps(project).replace('"value": 200', f'"value": {token}', 1)
    assert validate_json(text) == ValidationResult(False, 1, "invalid_json")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), 10**400, (1,), {1}, b"bytes"])
def test_non_json_python_values_are_rejected(project, value):
    project["site"]["area"]["value"] = value
    assert validate_project(project) == ValidationResult(False, 1, "invalid_json")


def test_non_string_keys_are_rejected(project):
    project[1] = "synthetic"
    assert validate_project(project).code == "invalid_json"


def test_cycles_and_excessive_nesting_are_rejected():
    cycle = {}
    cycle["cycle"] = cycle
    assert validate_project(cycle).code == "invalid_json"
    assert validate_json("[" * 1000 + "0" + "]" * 1000).code == "invalid_json"
    assert validate_json("[" * validation.MAX_DEPTH + "0" + "]" * validation.MAX_DEPTH).code == "schema_invalid"


def test_brackets_and_escaped_quotes_in_strings_do_not_increase_depth(project):
    project["project"]["name"] = '["\\' * 30
    assert validate_json(json.dumps(project)).valid


def test_size_limit_counts_utf8_bytes_and_accepts_exact_boundary(project):
    text = json.dumps(project, ensure_ascii=False)
    exact = text + " " * (validation.MAX_INPUT_BYTES - len(text.encode("utf-8")))
    assert validate_json(exact).valid
    assert validate_json(exact + " ").code == "input_too_large"
    assert validate_json("あ" * (validation.MAX_INPUT_BYTES // 3 + 1)).code == "input_too_large"
    project["project"]["name"] = "x" * validation.MAX_INPUT_BYTES
    assert validate_project(project).code == "input_too_large"


def test_missing_shared_schema_has_a_safe_failure(monkeypatch, tmp_path, project):
    validation._validator.cache_clear()
    monkeypatch.setattr(validation, "SCHEMA_PATH", tmp_path / "synthetic-missing-schema.json")
    try:
        assert validate_project(project) == ValidationResult(False, 1, "schema_unavailable")
    finally:
        validation._validator.cache_clear()


def run_cli(*arguments, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "bve", *map(str, arguments)],
        capture_output=True, text=True, check=False, cwd=cwd,
    )


def test_installed_package_imports_outside_repository(tmp_path):
    result = subprocess.run(
        [sys.executable, "-c", "from bve import validate_json, validate_project; print('IMPORT PASS')"],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    assert result.stdout == "IMPORT PASS\n"
    assert result.stderr == ""


def test_cli_sample_passes_from_arbitrary_working_directory(tmp_path):
    result = run_cli(SAMPLE, cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout == "PASS errors=0\n"
    assert result.stderr == ""


@pytest.mark.parametrize("case", ["malformed", "schema", "oversize", "nonfinite", "missing", "directory"])
def test_cli_failures_do_not_disclose_input_values_or_paths(project, tmp_path, case):
    marker = "SYNTHETIC-PRIVACY-SENTINEL"
    source = tmp_path / f"{marker}.json"
    if case == "malformed":
        source.write_text('{"' + marker + '":}', encoding="utf-8")
    elif case == "schema":
        project["site"]["area"]["status"] = marker
        source.write_text(json.dumps(project), encoding="utf-8")
    elif case == "oversize":
        source.write_bytes(b" " * (validation.MAX_INPUT_BYTES + 1))
    elif case == "nonfinite":
        source.write_text('{"' + marker + '":NaN}', encoding="utf-8")
    elif case == "directory":
        source.mkdir()
    result = run_cli(source)
    assert result.returncode != 0
    assert result.stdout == "FAIL errors=1\n"
    assert result.stderr == ""
    assert marker not in result.stdout + result.stderr
    assert str(tmp_path) not in result.stdout + result.stderr


def test_cli_argument_errors_are_safe():
    result = run_cli("SYNTHETIC-ARGUMENT-ONE", "SYNTHETIC-ARGUMENT-TWO")
    assert result.returncode == 2
    assert result.stdout == "FAIL errors=1\n"
    assert result.stderr == ""
