"""Phase 2 fixtures use only the existing public synthetic case."""
import json
from pathlib import Path

import pytest

CASE = Path(__file__).resolve().parents[1] / "cases/example-urban-office"


@pytest.fixture
def project_document():
    return json.loads((CASE / "project.json").read_bytes())


@pytest.fixture
def normalized_document():
    from bve.geometry import read_geojson
    from bve.geometry.export import json_bytes, normalized_feature
    site = read_geojson((CASE / "site.geojson").read_bytes())
    return json.loads(json_bytes(normalized_feature(site)))


@pytest.fixture
def run_inputs(tmp_path):
    """Writable copies of the sole public case; no private runtime sources."""
    folder = tmp_path / "inputs"
    folder.mkdir()
    for name in ("project.json", "site.geojson", "site.dxf"):
        (folder / name).write_bytes((CASE / name).read_bytes())
    return folder


@pytest.fixture
def run_package(tmp_path, run_inputs):
    from bve.run import create_package
    target = tmp_path / "package"
    create_package(project=run_inputs / "project.json", geometry=run_inputs / "site.geojson",
                   format="geojson", area_basis="declared_project_area",
                   floor_heights_m=[4, 5, 6, 7, 8], output=target)
    return target
