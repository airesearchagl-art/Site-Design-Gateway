"""The tracked Web sample is exact canonical output from the public synthetic CLI pipeline."""
from pathlib import Path

from bve.constraints.__main__ import main as constraints_main
from bve.geometry.__main__ import main as geometry_main
from bve.search.__main__ import main as search_main


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "cases/example-urban-office"


def test_search_result_fixture_matches_complete_cli_pipeline(tmp_path, capsys):
    geometry = tmp_path / "geometry.json"
    constraints = tmp_path / "constraints.json"
    search = tmp_path / "search-result.json"

    assert geometry_main([str(CASE / "site.geojson"), "--format", "geojson", "--output", str(geometry)]) == 0
    assert constraints_main([
        "--project", str(CASE / "project.json"),
        "--geometry", str(geometry),
        "--area-basis", "declared_project_area",
        "--output", str(constraints),
    ]) == 0
    assert search_main([
        "--geometry", str(geometry),
        "--constraints", str(constraints),
        "--floor-height-m", "4",
        "--floor-height-m", "5",
        "--floor-height-m", "6",
        "--floor-height-m", "7",
        "--floor-height-m", "8",
        "--output", str(search),
    ]) == 0

    assert search.read_bytes() == (CASE / "search-result.json").read_bytes()
    assert capsys.readouterr().err == ""
