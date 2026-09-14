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
