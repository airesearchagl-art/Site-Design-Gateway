"""Publishable fixture provenance and whole-flow checks, no real input."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from bve.geometry import read_dxf, read_geojson
from bve.geometry.export import json_bytes, normalized_feature

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "cases/example-urban-office"


def test_fixtures_are_reproducible_from_invented_constants():
    spec = importlib.util.spec_from_file_location("synthetic_geometry", ROOT / "scripts/generate_synthetic_geometry.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    generated = module.synthetic_files()
    assert generated == module.synthetic_files()
    for name, data in generated.items():
        assert (CASE / name).read_bytes() == data


def test_fixture_equivalence_area_and_coordinate_precision():
    geo = read_geojson((CASE / "site.geojson").read_bytes())
    dxf = read_dxf((CASE / "site.dxf").read_bytes(), layer="SITE")
    assert geo.area_m2 == dxf.area_m2 == 200.0
    assert abs(geo.area_m2 - dxf.area_m2) == 0
    assert geo.bounds == dxf.bounds == (0.0, 0.0, 12.0, 20.0)
    assert geo.polygon.wkb == dxf.polygon.wkb
    assert geo.polygon.equals(dxf.polygon)
    assert dxf.source_unit == "mm" and geo.source_unit == "m"
    assert geo.source_status == "assumed" and dxf.source_status == "drawing_derived"


def test_both_fixture_clis_with_temporary_outputs(tmp_path):
    for source_format in ("geojson", "dxf"):
        output, summary = tmp_path / f"{source_format}.geojson", tmp_path / f"{source_format}.json"
        result = subprocess.run([sys.executable, "-m", "bve.geometry", str(CASE / f"site.{source_format}"),
                                 "--format", source_format, "--output", str(output), "--summary", str(summary)],
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        assert result.stdout == "PASS code=VALID warnings=0\n" and result.stderr == ""
        assert json.loads(summary.read_bytes())["areaM2"] == 200
        assert read_geojson(output.read_bytes()).area_m2 == 200


def test_legacy_project_cli_unchanged():
    result = subprocess.run([sys.executable, "-m", "bve", str(CASE / "project.json")],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0
    assert result.stdout == "PASS errors=0\n" and result.stderr == ""
