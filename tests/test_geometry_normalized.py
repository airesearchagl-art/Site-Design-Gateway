"""Normalized contract consumption verifies metrics against synthetic polygons."""
from decimal import Decimal
from hashlib import sha256
import json

import pytest
from shapely import Polygon

from bve.geometry import GeometryError, SiteGeometry, load_normalized_geometry
from bve.geometry.export import json_bytes, normalized_feature


@pytest.mark.parametrize("as_bytes", [False, True])
@pytest.mark.parametrize("indent", [None, 2])
def test_normalized_exact_reference_and_original_provenance(normalized_document, as_bytes, indent):
    normalized_document["properties"].update(sourceFormat="dxf", sourceUnit="mm", sourceStatus="llm_researched")
    text = json.dumps(normalized_document, indent=indent) + "\r\n"
    raw = text.encode("utf-8")
    site = load_normalized_geometry(raw if as_bytes else text)
    assert site.area_m2 == 200 and site.bounds == (0, 0, 12, 20)
    assert site.source_format == "dxf" and site.source_unit == "mm"
    assert site.source_status == "llm_researched"
    assert site.source_reference == "sha256:" + sha256(raw).hexdigest()
    assert site.source_reference != normalized_document["properties"]["sourceReference"]


@pytest.mark.parametrize("field,value", [("areaM2", 199), ("bounds", [0, 0, 12, 21]),
    ("bounds", [1, 0, 12, 20]), ("bounds", [0, -1, 12, 20]), ("bounds", [0, 0, 13, 20])])
def test_normalized_metadata_tampering(normalized_document, field, value):
    normalized_document["properties"][field] = value
    with pytest.raises(GeometryError, match="^METADATA_MISMATCH$"):
        load_normalized_geometry(json.dumps(normalized_document))


def test_normalized_does_not_round_metadata_before_comparison(normalized_document):
    raw = json.dumps(normalized_document).replace('"areaM2": 200.0', '"areaM2": 200.000000000000000000000001')
    with pytest.raises(GeometryError, match="^METADATA_MISMATCH$"):
        load_normalized_geometry(raw)


@pytest.mark.parametrize("field,value", [("unit", "mm"), ("sourceStatus", "verified"), ("valid", False),
    ("sourceReference", "synthetic-name"), ("sourceReference", "sha256:" + "a" * 64 + "\n"),
    ("areaM2", True), ("bounds", [0, 0, 12]), ("sourceUnit", "inch")])
def test_normalized_schema_gate(normalized_document, field, value):
    normalized_document["properties"][field] = value
    with pytest.raises(GeometryError, match="^NORMALIZED_SCHEMA_INVALID$"):
        load_normalized_geometry(json.dumps(normalized_document))


@pytest.mark.parametrize("coordinates,code", [
    ([[[0, 0], [4, 3], [0, 4], [3, 0], [0, 0]]], "INVALID_POLYGON"),
    ([[[0, 0], [1, 0], [2, 0], [0, 0]]], "ZERO_AREA"),
    ([[[0, 0], [1, 0], [1, 1], [0, 2]]], "OPEN_BOUNDARY"),
    ([[[0, 0, 1], [1, 0], [1, 1], [0, 0]]], "NORMALIZED_SCHEMA_INVALID"),
])
def test_schema_structure_does_not_replace_polygon_checks(normalized_document, coordinates, code):
    normalized_document["geometry"]["coordinates"] = coordinates
    with pytest.raises(GeometryError, match=f"^{code}$"):
        load_normalized_geometry(json.dumps(normalized_document))


@pytest.mark.parametrize("ring", [
    [(0.1, 0.2), (9.9, 0.1), (11.1, 20.5), (0.2, 21.1), (0.1, 0.2)],
    [(0.1, 0.2), (0.2, 21.1), (11.1, 20.5), (9.9, 0.1), (0.1, 0.2)],
])
def test_roundtrip_preserves_encoded_metric_order_with_holes(ring):
    polygon = Polygon(ring, [[(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)]])
    original = SiteGeometry(polygon, "geojson", "m", "assumed", "sha256:" + "0" * 64)
    loaded = load_normalized_geometry(json_bytes(normalized_feature(original)))
    assert loaded.area_m2 == original.area_m2
    assert loaded.bounds == original.bounds
    assert loaded.polygon.wkb == original.polygon.wkb


@pytest.mark.parametrize("payload,code", [(b"\xff", "INVALID_JSON"), (b"\xef\xbb\xbf{}", "INVALID_JSON"),
    ('{"x":1,"x":2}', "INVALID_JSON"), ('{"x":"\\ud800"}', "INVALID_JSON"),
    ('{"x":NaN}', "INVALID_JSON"), ('{"x":Infinity}', "INVALID_JSON"),
    ("[" * 33 + "0" + "]" * 33, "INVALID_JSON"), ('{"x":1e1025}', "NUMERIC_RANGE"),
    (b" " * (4 * 1024 * 1024 + 1), "INPUT_TOO_LARGE")], ids=[
        "utf8", "bom", "duplicate-key", "surrogate", "nan", "infinity", "depth", "exponent", "size"])
def test_normalized_bounded_json(payload, code):
    with pytest.raises(GeometryError, match=f"^{code}$"):
        load_normalized_geometry(payload)
