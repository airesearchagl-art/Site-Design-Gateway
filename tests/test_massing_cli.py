"""Synthetic CLI pipeline, non-disclosure, exclusive outputs and determinism."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from bve.constraints import compute_constraints, load_project
from bve.constraints.export import result_bytes
from bve.geometry import load_normalized_geometry
from bve.massing import __main__ as cli
from bve.massing.export import write_output
from test_massing_engine import make

CASE = Path(__file__).resolve().parents[1] / "cases/example-urban-office"


@pytest.fixture
def cli_args(tmp_path, project_document, normalized_document):
    geometry = tmp_path / "synthetic-sensitive-geometry.geojson"
    geometry.write_text(json.dumps(normalized_document), encoding="utf-8")
    site = load_normalized_geometry(geometry.read_bytes())
    result = compute_constraints(load_project(json.dumps(project_document)), site, area_basis="declared_project_area")
    constraints = tmp_path / "synthetic-sensitive-constraints.json"
    constraints.write_bytes(result_bytes(result))
    return ["--geometry", str(geometry), "--constraints", str(constraints), "--floor-height-m", "4"]


def test_summary_only_writes_nothing(cli_args, tmp_path, capsys):
    before = sorted(path.name for path in tmp_path.iterdir())
    assert cli.main(cli_args) == 0
    captured = capsys.readouterr()
    assert captured.out == "PASS floors=7 reviewRequired=true\n" and captured.err == ""
    assert sorted(path.name for path in tmp_path.iterdir()) == before


@pytest.mark.parametrize("change,code", [("missing-height", "FLOOR_HEIGHT_REQUIRED"),
    ("bad-height", "INVALID_FLOOR_HEIGHT"), ("unknown-arg", "INVALID_ARGUMENTS"),
    ("duplicate", "INVALID_ARGUMENTS"), ("missing-file", "IO_ERROR"),
    ("bad-geometry", "INVALID_JSON"), ("bad-constraints", "INVALID_JSON"),
    ("tampered", "CONSTRAINT_SEMANTIC_MISMATCH")])
def test_fixed_failure_no_input_disclosure(cli_args, change, code, tmp_path, capsys):
    args = cli_args.copy()
    if change == "missing-height":
        args = args[:-2]
    elif change == "bad-height":
        args[-1] = "synthetic-sensitive-design-input"
    elif change == "unknown-arg":
        args += ["--synthetic-sensitive-extra"]
    elif change == "duplicate":
        args += ["--floor-height-m", "5"]
    elif change == "missing-file":
        args[1] = str(tmp_path / "synthetic-sensitive-missing")
    elif change in ("bad-geometry", "bad-constraints"):
        Path(args[1 if change == "bad-geometry" else 3]).write_bytes(b'{"synthetic-sensitive":')
    else:
        path = Path(args[3])
        document = json.loads(path.read_bytes())
        document["constraints"]["buildingCoverage"]["maxFootprintAreaM2"] = 161
        path.write_text(json.dumps(document), encoding="utf-8")
    output = tmp_path / "not-created.json"
    assert cli.main(args + ["--output", str(output)]) in (1, 2)
    captured = capsys.readouterr()
    assert captured.out == f"FAIL code={code}\n" and captured.err == ""
    assert not output.exists()


@pytest.mark.parametrize("which", ["geometry", "constraints", "existing", "parent"])
def test_outputs_are_exclusive_and_no_implicit_directory(cli_args, which, tmp_path, capsys):
    if which in ("geometry", "constraints"):
        path = Path(cli_args[1 if which == "geometry" else 3])
    else:
        path = tmp_path / "existing.json" if which == "existing" else tmp_path / "missing-dir" / "output.json"
        if which == "existing":
            path.write_bytes(b"preserved")
    previous = path.read_bytes() if path.exists() else None
    assert cli.main(cli_args + ["--output", str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ("FAIL code=IO_ERROR\n" if which == "parent" else "FAIL code=OUTPUT_EXISTS\n")
    assert captured.err == ""
    if previous is not None:
        assert path.read_bytes() == previous
    else:
        assert not path.parent.exists()


def test_export_rejects_symlink_before_open(project_document, normalized_document, tmp_path, monkeypatch):
    candidate = make(project_document, normalized_document)
    path = tmp_path / "synthetic-link"
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda current: current == path or original(current))
    with pytest.raises(ValueError, match="^OUTPUT_EXISTS$"):
        write_output(candidate, path)
    assert not path.exists()


def test_raw_internal_exception_is_not_disclosed(cli_args, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic-sensitive-diagnostic")
    monkeypatch.setattr(cli, "generate_massing_candidate", fail)
    assert cli.main(cli_args) == 2
    captured = capsys.readouterr()
    assert captured.out == "FAIL code=INTERNAL_ERROR\n" and captured.err == ""


def test_complete_synthetic_cli_pipeline_and_hash_seeds(tmp_path):
    geometry, constraints = tmp_path / "normalized.json", tmp_path / "constraints.json"
    commands = [
        ["bve.geometry", str(CASE / "site.geojson"), "--format", "geojson", "--output", str(geometry)],
        ["bve.constraints", "--project", str(CASE / "project.json"), "--geometry", str(geometry),
         "--area-basis", "declared_project_area", "--output", str(constraints)]]
    for args in commands:
        completed = subprocess.run([sys.executable, "-m", *args], capture_output=True, text=True, timeout=30)
        assert completed.returncode == 0 and completed.stderr == ""
        assert completed.stdout.startswith("PASS ")
    outputs = []
    for index, seed in enumerate([1, 23, 997, 23, 23]):
        output = tmp_path / f"candidate-{index}.json"
        completed = subprocess.run([sys.executable, "-m", "bve.massing", "--geometry", str(geometry),
            "--constraints", str(constraints), "--floor-height-m", "4", "--output", str(output)],
            env={**os.environ, "PYTHONHASHSEED": str(seed)}, capture_output=True, text=True, timeout=30)
        assert completed.returncode == 0
        assert completed.stdout == "PASS floors=7 reviewRequired=true\n" and completed.stderr == ""
        outputs.append(output.read_bytes())
    assert len(set(outputs)) == 1
    assert outputs[0].endswith(b"\n") and b"\r" not in outputs[0]
    data = json.loads(outputs[0])
    assert data["candidate"]["floorCount"] == 7 and data["candidate"]["heightM"] == 28
