"""P8-PY-01..18: complete public synthetic orchestration, not mock calculations."""
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from bve._schemas import schema_validator
from bve.constraints.__main__ import main as constraints_main
from bve.constraints.export import project_bytes
from bve.geometry.__main__ import main as geometry_main
from bve.run import create_package, verify_package
from bve.run.__main__ import main
from bve.run.model import ARTIFACTS, FILE_SET
from bve.search.__main__ import main as search_main


def create(inputs, output, **kwargs):
    options = dict(project=inputs / "project.json", geometry=inputs / "site.geojson",
                   format="geojson", area_basis="declared_project_area",
                   floor_heights_m=[4, 5, 6, 7, 8], output=output)
    options.update(kwargs)
    return create_package(**options)


def test_manifest_structure_hashes_and_references(run_package):
    manifest = json.loads((run_package / "manifest.json").read_bytes())
    schema_validator("run").validate(manifest)
    assert set(p.name for p in run_package.iterdir()) == FILE_SET
    assert manifest["packageVersion"] == "sdg-run-package-v0.1"
    refs = {}
    for kind, name in ARTIFACTS.items():
        refs[kind] = "sha256:" + sha256((run_package / name).read_bytes()).hexdigest()
        assert manifest["artifacts"][kind] == {"path": name, "reference": refs[kind]}
    constraints = json.loads((run_package / "constraints.json").read_bytes())
    search = json.loads((run_package / "search-result.json").read_bytes())
    assert constraints["inputReferences"] == {k: refs[k] for k in ("project", "geometry")}
    assert search["inputReferences"] == {k: refs[k] for k in ("project", "geometry", "constraints")}
    assert search["schemaVersion"] == "0.2"
    assert verify_package(run_package).console() == (
        "PASS packageVersion=sdg-run-package-v0.1 artifacts=4 reviewRequired=true evaluated=5 accepted=5 rejected=0")


def test_same_inputs_different_directories_all_exact_bytes(run_inputs, tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    before = {p.name: p.read_bytes() for p in run_inputs.iterdir()}
    create(run_inputs, first)
    other_inputs = tmp_path / "different-input-directory"
    other_inputs.mkdir()
    for name, raw in before.items():
        (other_inputs / name).write_bytes(raw)
    create(other_inputs, second)
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {p.name: p.read_bytes() for p in second.iterdir()}
    assert {p.name: p.read_bytes() for p in run_inputs.iterdir()} == before
    assert {p.name: p.read_bytes() for p in other_inputs.iterdir()} == before


@pytest.mark.parametrize("format", ["geojson", "dxf"])
def test_manual_cli_equivalence(run_inputs, tmp_path, capsys, format):
    package, manual = tmp_path / "package", tmp_path / "manual"
    manual.mkdir()
    args = ["create", "--project", str(run_inputs / "project.json"),
            "--geometry", str(run_inputs / ("site." + format)), "--format", format,
            "--area-basis", "declared_project_area", "--output", str(package)]
    layer = ["--layer", "SITE"] if format == "dxf" else []
    heights = [argument for height in (4, 5, 6, 7, 8) for argument in ("--floor-height-m", str(height))]
    assert main(args + layer + heights) == 0
    # Canonical Project bytes are the package's explicit input contract. Every
    # downstream CLI hashes those exact bytes, not the source's pretty formatting.
    (manual / "project.json").write_bytes(project_bytes((run_inputs / "project.json").read_bytes()))
    assert geometry_main([str(run_inputs / ("site." + format)), "--format", format,
                          "--output", str(manual / "site.geojson")] + layer) == 0
    assert constraints_main(["--project", str(manual / "project.json"),
                             "--geometry", str(manual / "site.geojson"),
                             "--area-basis", "declared_project_area", "--output", str(manual / "constraints.json")]) == 0
    assert search_main(["--geometry", str(manual / "site.geojson"),
                        "--constraints", str(manual / "constraints.json"),
                        "--output", str(manual / "search-result.json")] + heights) == 0
    for name in ARTIFACTS.values():
        assert (package / name).read_bytes() == (manual / name).read_bytes()
    assert main(["verify", "--package", str(package)]) == 0
    captured = capsys.readouterr()
    assert captured.err == "" and str(tmp_path) not in captured.out
    assert "Example Urban Office" not in captured.out and "coordinates" not in captured.out


def test_geojson_dxf_preserve_provenance_not_artificially_equal(run_inputs, tmp_path):
    geo, dxf = tmp_path / "geo", tmp_path / "dxf"
    create(run_inputs, geo)
    create(run_inputs, dxf, geometry=run_inputs / "site.dxf", format="dxf", layer="SITE")
    a, b = [json.loads((folder / "site.geojson").read_bytes()) for folder in (geo, dxf)]
    assert a["geometry"] == b["geometry"]
    assert a["properties"]["areaM2"] == b["properties"]["areaM2"]
    assert a["properties"]["sourceFormat"] != b["properties"]["sourceFormat"]
    assert a["properties"]["sourceReference"] != b["properties"]["sourceReference"]
    # Different source provenance legitimately changes normalized and downstream bytes.
    assert (geo / "constraints.json").read_bytes() != (dxf / "constraints.json").read_bytes()


@pytest.mark.parametrize("basis,cap", [("declared_project_area", 144), ("geometry_area", 160)])
def test_explicit_area_basis_and_canonical_heights(run_inputs, tmp_path, basis, cap):
    project = json.loads((run_inputs / "project.json").read_bytes())
    project["site"]["area"]["value"] = 180
    (run_inputs / "project.json").write_text(json.dumps(project), encoding="utf-8")
    target = tmp_path / "package"
    create(run_inputs, target, area_basis=basis, floor_heights_m=["8.00", "4e0", Decimal("6")])
    manifest = json.loads((target / "manifest.json").read_bytes())
    constraints = json.loads((target / "constraints.json").read_bytes())
    search = json.loads((target / "search-result.json").read_bytes())
    assert manifest["configuration"] == {"areaBasis": basis, "floorHeightsM": [4, 6, 8]}
    assert constraints["areaBasis"]["selectedBasis"] == basis
    assert constraints["constraints"]["buildingCoverage"]["maxFootprintAreaM2"] == cap
    assert search["search"]["floorHeightsM"] == manifest["configuration"]["floorHeightsM"]


def test_zero_accepted_is_completed_verified_package(run_inputs, tmp_path):
    target = tmp_path / "zero"
    summary = create(run_inputs, target, floor_heights_m=[40, 32])
    assert summary.evaluated == 2 and summary.accepted == 0 and summary.rejected == 2
    assert summary.review_required and verify_package(target) == summary
    search = json.loads((target / "search-result.json").read_bytes())
    assert search["rankedCandidates"] == [] and search["summary"]["hasFeasibleCandidate"] is False
    assert [r["code"] for r in search["rejections"]] == ["NO_FEASIBLE_MASSING"] * 2


def test_canonical_project_formatting_and_status_preserved(run_inputs, tmp_path):
    before = (run_inputs / "project.json").read_bytes()
    first = tmp_path / "first"
    create(run_inputs, first)
    data = json.loads(before)
    (run_inputs / "project.json").write_text(json.dumps(data, indent=4, sort_keys=True), encoding="utf-8")
    second = tmp_path / "second"
    create(run_inputs, second)
    for name in FILE_SET:
        assert (first / name).read_bytes() == (second / name).read_bytes()
    assert json.loads((first / "project.json").read_bytes()) == data
    assert (first / "project.json").read_bytes() == project_bytes(before)


def test_module_entrypoint_summary_only(run_inputs, tmp_path):
    args = [sys.executable, "-m", "bve.run", "create", "--project", str(run_inputs / "project.json"),
            "--geometry", str(run_inputs / "site.geojson"), "--format", "geojson",
            "--area-basis", "geometry_area", "--floor-height-m", "4", "--output", str(tmp_path / "cli")]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0 and result.stderr == ""
    assert result.stdout.strip() == "PASS packageVersion=sdg-run-package-v0.1 artifacts=4 reviewRequired=true evaluated=1 accepted=1 rejected=0"


@pytest.mark.parametrize("missing", ["--project", "--geometry", "--format", "--area-basis", "--floor-height-m", "--output"])
def test_required_arguments_no_defaults(missing, capsys):
    args = ["create", "--project", "synthetic.json", "--geometry", "synthetic.geojson", "--format", "geojson",
            "--area-basis", "geometry_area", "--floor-height-m", "4", "--output", "result"]
    index = args.index(missing)
    del args[index:index + 2]
    assert main(args) == 1
    assert capsys.readouterr().out == "FAIL stage=arguments code=INVALID_ARGUMENTS\n"


@pytest.mark.parametrize("args", [["verify", "--package", "a", "--package", "b"],
                                 ["verify", "--pack", "a"], ["verify", "--package", "a", "--unexpected", "sensitive"],
                                 ["unknown"], []])
def test_cli_invalid_arguments_never_echo_values(args, capsys):
    assert main(args) == 1
    assert capsys.readouterr().out == "FAIL stage=arguments code=INVALID_ARGUMENTS\n"
