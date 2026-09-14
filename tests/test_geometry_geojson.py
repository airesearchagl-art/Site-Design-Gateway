"""Only invented coordinates. Contract, numeric and non-disclosure boundaries."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
from typing import get_args

import pytest
from shapely import Polygon

from bve.geometry import Code, GeometryError, SiteGeometry, read_geojson
from bve.geometry.geojson import MAX_INPUT_BYTES
from bve.geometry.model import SourceStatus
from bve.geometry.normalization import normalized_polygon

RING = [[0, 0], [10, 0], [14, 10], [6, 20], [0, 20], [0, 0]]


def feature(ring=None, unit="m"):
    return {"type": "Feature", "properties": {"unit": unit, "coordinateSystem": "local_xy"},
            "geometry": {"type": "Polygon", "coordinates": [deepcopy(RING if ring is None else ring)]}}


def read(value):
    return read_geojson(json.dumps(value))


def rejected(value, *codes):
    with pytest.raises(GeometryError) as error:
        read(value)
    assert error.value.code in codes
    assert str(error.value) == error.value.code.value


@pytest.mark.parametrize("bare", [False, True])
@pytest.mark.parametrize("unit,scale", [("m", 1), ("mm", 1000)])
def test_meter_millimeter_irregular_polygon(bare, unit, scale):
    value = feature([[x * scale, y * scale] for x, y in RING], unit)
    if bare:
        value = {**value["geometry"], **value["properties"]}
    site = read(value)
    assert site.area_m2 == 220
    assert site.bounds == (0, 0, 14, 20)
    assert site.normalized_unit == "m" and site.source_unit == unit
    assert site.source_status == "user_provided"
    assert site.polygon.equals(Polygon(RING))
    assert site.polygon.exterior.is_ccw


@pytest.mark.parametrize("unit", [None, "ft", "unknown", "M", 1, {}, []])
def test_unit_required_or_supported(unit):
    rejected(feature(unit=unit), Code.UNIT_REQUIRED, Code.UNSUPPORTED_UNIT)


@pytest.mark.parametrize("crs", [None, "EPSG:4326", "EPSG:3857", "latlon", {}])
def test_unknown_or_geographic_crs(crs):
    value = feature()
    value["properties"]["coordinateSystem"] = crs
    rejected(value, Code.CRS_REQUIRED, Code.UNSUPPORTED_CRS)


@pytest.mark.parametrize("location", ["root", "geometry", "properties"])
@pytest.mark.parametrize("value", [None, {"type": "name", "properties": {"name": "EPSG:4326"}}])
def test_any_legacy_crs_is_rejected(location, value):
    data = feature()
    target = data if location == "root" else data[location]
    target["crs"] = value
    rejected(data, Code.UNSUPPORTED_CRS)


@pytest.mark.parametrize("ring,codes", [
    ([[0, 0], [1, 1], [0, 1], [1, 0], [0, 0]], (Code.ZERO_AREA, Code.INVALID_POLYGON)),
    ([[0, 0], [4, 3], [0, 4], [3, 0], [0, 0]], (Code.INVALID_POLYGON,)),
    ([[0, 0], [1, 0], [2, 0], [0, 0]], (Code.ZERO_AREA,)),
    ([[0, 0], [1, 0], [0, 0]], (Code.TOO_FEW_VERTICES,)),
    ([], (Code.INVALID_COORDINATES,)),
    ([[0, 0], [1, 0], [1, 1]], (Code.OPEN_BOUNDARY,)),
    ([[0, 0, 0], [1, 0], [1, 1], [0, 0, 0]], (Code.NON_2D,)),
    ([[False, 0], [1, 0], [1, 1], [False, 0]], (Code.INVALID_COORDINATES,)),
    ([["0", 0], [1, 0], [1, 1], ["0", 0]], (Code.INVALID_COORDINATES,)),
    ([[0], [1, 0], [1, 1], [0]], (Code.NON_2D,)),
])
def test_invalid_rings(ring, codes):
    rejected(feature(ring), *codes)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_nonfinite_json(token):
    text = json.dumps(feature()).replace("[0, 0]", f"[{token}, 0]")
    with pytest.raises(GeometryError) as error:
        read_geojson(text)
    assert error.value.code in (Code.INVALID_JSON, Code.NONFINITE_COORDINATES)


@pytest.mark.parametrize("value", [None, [], {}, {"type": "MultiPolygon"},
                                   {"type": "FeatureCollection", "features": []}])
def test_unsupported_document(value):
    rejected(value, Code.UNSUPPORTED_TYPE)


@pytest.mark.parametrize("kind", ["Point", "LineString", "MultiPolygon", "GeometryCollection"])
def test_unsupported_geometry(kind):
    value = feature()
    value["geometry"]["type"] = kind
    rejected(value, Code.UNSUPPORTED_TYPE)


@pytest.mark.parametrize("payload", [b"{", b"\xff", b"\xef\xbb\xbf{}", b'{}{}',
    '{"type":"Polygon","type":"Point"}', '{"name":"\\ud800"}', '[' * 1100 + ']' * 1100])
def test_malformed_input(payload):
    with pytest.raises(GeometryError, match="^INVALID_JSON$"):
        read_geojson(payload)


def test_input_limits():
    with pytest.raises(GeometryError, match="^INPUT_TOO_LARGE$"):
        read_geojson(b" " * (MAX_INPUT_BYTES + 1))
    value = feature()
    value["properties"]["nested"] = [[[[[]]]]]
    for _ in range(32):
        value["properties"]["nested"] = [value["properties"]["nested"]]
    rejected(value, Code.INVALID_JSON)


@pytest.mark.parametrize("status", get_args(SourceStatus))
def test_status_preserved_and_metadata_not_copied(status):
    value = feature()
    value["properties"].update(sourceStatus=status, name="synthetic-private-marker", sourceReference="unused")
    site = read(value)
    assert site.source_status == status
    assert site.source_reference.startswith("sha256:")
    assert "synthetic-private-marker" not in repr(site)
    assert "POLYGON" not in repr(site)


def test_statuses_match_sole_project_schema():
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/sdg-project-v0.1.schema.json").read_text())
    assert list(get_args(SourceStatus)) == schema["$defs"]["status"]["enum"]


def test_holes_valid_and_invalid():
    value = feature([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]])
    value["geometry"]["coordinates"].append([[2, 2], [4, 2], [4, 4], [2, 4], [2, 2]])
    site = read(value)
    assert site.area_m2 == 96
    assert not site.polygon.interiors[0].is_ccw
    value["geometry"]["coordinates"][1] = [[20, 20], [22, 20], [22, 22], [20, 20]]
    rejected(value, Code.INVALID_POLYGON)


def test_small_valid_polygon_has_no_arbitrary_area_epsilon():
    site = read(feature([[0, 0], [1e-9, 0], [1e-9, 1e-9], [0, 0]]))
    assert site.area_m2 == pytest.approx(5e-19, rel=1e-14, abs=0)


def test_orientation_start_vertex_closure_and_determinism():
    forward = read(feature())
    reverse = read(feature(list(reversed(RING))))
    rotated = RING[2:-1] + RING[:3]
    repeated = read(feature(RING + [RING[0], RING[0]]))
    assert len(repeated.polygon.exterior.coords) == len(RING)
    for other in (reverse, read(feature(rotated)), repeated, read(feature())):
        assert forward.polygon.wkb == other.polygon.wkb


def test_numeric_precision_millimeters_and_no_input_mutation():
    ring = [[0.1, 0.2], [1234.5, 0.2], [1234.5, 2345.6], [0.1, 0.2]]
    value = feature(ring, "mm")
    original = deepcopy(value)
    site = read(value)
    assert site.area_m2 == pytest.approx(1.2344 * 2.3454 / 2, rel=1e-14)
    assert value == original


def test_unrepresentable_int_and_scale_underflow_rejected():
    rejected(feature([[2**53 + 1, 0], [2**53 + 4, 0], [2**53 + 4, 4], [2**53 + 1, 0]]), Code.NUMERIC_RANGE)
    rejected(feature([[0, 0], [5e-324, 0], [1, 1], [0, 0]], "mm"), Code.NUMERIC_RANGE)


@pytest.mark.parametrize("literal", ["1e-400", "9007199254740993.0", "1.00000000000000000001"])
def test_lexical_float_loss_is_rejected_before_json_conversion(literal):
    value = feature([[0, 0], [1, 0], [2, 0], [4, 4], [0, 4], [0, 0]])
    raw = json.dumps(value).replace("[2, 0]", f"[{literal}, 0]")
    with pytest.raises(GeometryError, match="^NUMERIC_RANGE$"):
        read_geojson(raw)


def test_model_immutable_and_cannot_adopt_invalid_polygon():
    site = read(feature())
    with pytest.raises(FrozenInstanceError):
        site.source_unit = "mm"
    with pytest.raises(GeometryError):
        SiteGeometry(Polygon(), "geojson", "m", "user_provided", site.source_reference)
    with pytest.raises(GeometryError, match="^INVALID_METADATA$"):
        SiteGeometry(site.polygon, "geojson", "m", "user_provided", "arbitrary-path")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_python_normalizer_rejects_nonfinite(value):
    with pytest.raises(GeometryError, match="^NONFINITE_COORDINATES$"):
        normalized_polygon([[[0, 0], [value, 0], [1, 1], [0, 0]]], "m")
