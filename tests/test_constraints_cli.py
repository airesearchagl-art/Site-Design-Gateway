"""Explicit temporary output, deterministic bytes and fixed CLI diagnostics."""
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from bve._schemas import schema_validator
from bve.constraints import ConstraintError, compute_constraints, load_project
from bve.constraints.export import constraint_summary, result_bytes, write_output
from bve.geometry import load_normalized_geometry


@pytest.fixture
def constraint_files(tmp_path, project_document, normalized_document):
    project, geometry = tmp_path / "synthetic-private-project.json", tmp_path / "synthetic-private-site.json"
    project.write_text(json.dumps(project_document), encoding="utf-8")
    geometry.write_text(json.dumps(normalized_document), encoding="utf-8")
    return project, geometry


def run(project, geometry, *args, seed="1"):
    return subprocess.run([sys.executable, "-m", "bve.constraints", "--project", str(project),
                           "--geometry", str(geometry), *map(str, args)], capture_output=True, text=True,
                          env=dict(os.environ, PYTHONHASHSEED=seed), timeout=30)


def test_deterministic_decimal_export_and_schema(project_document, normalized_document, tmp_path):
    text = json.dumps(project_document).replace('"value": 80', '"value": 80.12345678901234567890123456789')
    project = load_project(text)
    geometry = load_normalized_geometry(json.dumps(normalized_document))
    result = compute_constraints(project, geometry, area_basis="declared_project_area")
    before = result_bytes(result)
    assert before == result_bytes(result)
    assert b'"maxFootprintAreaM2":160.24691357802469135780246913578' in before
    decoded = json.loads(before, parse_float=Decimal)
    schema_validator("constraints").validate(decoded)
    assert list(decoded["constraints"]) == ["buildingCoverage", "floorAreaRatio", "height"]
    path = tmp_path / "result.json"
    write_output(result, path)
    assert path.read_bytes() == before
    with pytest.raises(ConstraintError, match="^OUTPUT_EXISTS$"):
        write_output(result, path)
    assert path.read_bytes() == before


def test_cli_hashseed_determinism_exact_hashes_and_nondisclosure(constraint_files, tmp_path):
    project, geometry = constraint_files
    expected_refs = {"project": "sha256:" + sha256(project.read_bytes()).hexdigest(),
                     "geometry": "sha256:" + sha256(geometry.read_bytes()).hexdigest()}
    outputs, summaries = [], []
    for seed in ("1", "23"):
        output = tmp_path / f"result-{seed}.json"
        process = run(project, geometry, "--area-basis", "declared_project_area", "--output", output, seed=seed)
        assert process.returncode == 0 and process.stderr == ""
        assert process.stdout == "PASS reviewRequired=true computed=3 unavailable=0 absent=0\n"
        data = output.read_bytes()
        parsed = json.loads(data)
        assert parsed["inputReferences"] == expected_refs
        assert b"synthetic-private" not in data and b"Example Urban Office" not in data
        assert "coordinates" not in parsed and "bounds" not in parsed
        outputs.append(data)
        summaries.append(process.stdout)
    assert outputs[0] == outputs[1] and summaries[0] == summaries[1]


def test_cli_no_output_has_no_side_effects(constraint_files, tmp_path):
    before = set(tmp_path.iterdir())
    result = run(*constraint_files, "--area-basis", "geometry_area")
    assert result.returncode == 0 and result.stderr == ""
    assert set(tmp_path.iterdir()) == before


@pytest.mark.parametrize("args,code,exit_code", [
    ([], "AREA_BASIS_REQUIRED", 1),
    (["--area-basis", "synthetic-private-value"], "INVALID_AREA_BASIS", 1),
    (["--area", "geometry_area"], "INVALID_ARGUMENTS", 2),
    (["--unexpected", "synthetic-private-value"], "INVALID_ARGUMENTS", 2),
    (["--project", "synthetic-private-value"], "INVALID_ARGUMENTS", 2),
    (["--area-basis", "geometry_area", "--area-basis", "declared_project_area"], "INVALID_ARGUMENTS", 2),
], ids=["basis-required", "basis-invalid", "no-abbreviation", "unknown-argument", "duplicate-project", "duplicate-basis"])
def test_cli_fixed_argument_failures(constraint_files, args, code, exit_code):
    result = run(*constraint_files, *args)
    assert result.returncode == exit_code
    assert result.stdout == f"FAIL code={code}\n" and result.stderr == ""


@pytest.mark.parametrize("target,damage,code", [
    (0, "json", "INVALID_JSON"), (0, "schema", "PROJECT_SCHEMA_INVALID"),
    (1, "json", "INVALID_JSON"), (1, "schema", "NORMALIZED_SCHEMA_INVALID"),
    (1, "tamper", "METADATA_MISMATCH"),
])
def test_cli_input_failures_are_non_disclosing(constraint_files, tmp_path, target, damage, code):
    path = constraint_files[target]
    if damage == "tamper":
        data = json.loads(path.read_bytes())
        data["properties"]["areaM2"] = 199
        path.write_text(json.dumps(data), encoding="utf-8")
    else:
        path.write_text('{"synthetic-private-marker":' if damage == "json" else '{"synthetic-private-marker":1}', encoding="utf-8")
    output = tmp_path / "rejected.json"
    result = run(*constraint_files, "--area-basis", "geometry_area", "--output", output)
    assert result.returncode == 1 and result.stdout == f"FAIL code={code}\n" and result.stderr == ""
    assert not output.exists()


def test_cli_existing_output_and_io_errors_do_not_leak(constraint_files, tmp_path):
    project, geometry = constraint_files
    before = project.read_bytes()
    existing = run(project, geometry, "--area-basis", "geometry_area", "--output", project)
    assert existing.returncode == 2 and existing.stdout == "FAIL code=OUTPUT_EXISTS\n" and existing.stderr == ""
    assert project.read_bytes() == before
    for result in (run(tmp_path / "synthetic-private-missing.json", geometry, "--area-basis", "geometry_area"),
                   run(project, geometry, "--area-basis", "geometry_area", "--output", tmp_path / "missing" / "result.json")):
        assert result.returncode == 2 and result.stdout == "FAIL code=IO_ERROR\n" and result.stderr == ""


def test_counts_for_unavailable_and_absent(project_document, normalized_document):
    project_document["zoning"]["buildingCoverageRatio"].update(value=None, status="unknown")
    del project_document["zoning"]["heightLimit"]
    result = compute_constraints(load_project(json.dumps(project_document)),
        load_normalized_geometry(json.dumps(normalized_document)), area_basis="geometry_area")
    assert constraint_summary(result) == {"reviewRequired": True, "computed": 1, "unavailable": 1, "absent": 1}
