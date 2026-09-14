"""Synthetic ezdxf documents exercise selection and geometry-loss boundaries."""
import io
import json
import logging
import os
from pathlib import Path
import subprocess
import sys

import pytest

from bve.geometry import Code, GeometryError, read_dxf, read_geojson
from bve.geometry._dxf_runtime import ezdxf_module, quiet_dxf

with quiet_dxf():
    ezdxf = ezdxf_module()

RING = [(0, 0), (10, 0), (14, 10), (6, 20), (0, 20)]


def document(kind="LWPOLYLINE", units=6, closed=True, points=RING):
    doc = ezdxf.new("R2010", units=units)
    if kind == "LWPOLYLINE":
        boundary = doc.modelspace().add_lwpolyline(points, close=closed)
    else:
        boundary = doc.modelspace().add_polyline2d(points, close=closed)
    return doc, boundary


def payload(doc):
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue()


def rejected(doc, code, **options):
    with pytest.raises(GeometryError) as error:
        read_dxf(payload(doc), **options)
    assert error.value.code == code
    assert str(error.value) == code


@pytest.mark.parametrize("kind", ["LWPOLYLINE", "POLYLINE"])
@pytest.mark.parametrize("units,scale", [(6, 1), (4, 1000)])
def test_supported_dxf_and_geojson_equivalence(kind, units, scale):
    doc, _ = document(kind, units, points=[(x * scale, y * scale) for x, y in RING])
    data = payload(doc)
    site = read_dxf(data)
    geojson = read_geojson(json.dumps({"type": "Polygon", "unit": "m", "coordinateSystem": "local_xy",
                                     "coordinates": [[*RING, RING[0]]]}))
    assert site.area_m2 == geojson.area_m2 == 220
    assert site.bounds == (0, 0, 14, 20)
    assert site.polygon.wkb == geojson.polygon.wkb
    assert site.source_unit == ("mm" if units == 4 else "m")
    assert site.source_status == "drawing_derived"
    assert site.source_reference == read_dxf(data).source_reference


@pytest.mark.parametrize("kind", ["LWPOLYLINE", "POLYLINE"])
def test_open_flag_rejected_even_when_last_point_repeats_first(kind):
    doc, _ = document(kind, closed=False, points=[*RING, RING[0]])
    rejected(doc, Code.OPEN_BOUNDARY)


def test_multiple_boundaries_require_explicit_layer_not_largest_area():
    doc, boundary = document()
    doc.layers.new("SITE")
    boundary.dxf.layer = "SITE"
    doc.modelspace().add_lwpolyline([(0, 0), (1, 0), (1, 1)], close=True)
    rejected(doc, Code.AMBIGUOUS_BOUNDARY)
    assert read_dxf(payload(doc), layer="site").area_m2 == 220
    rejected(doc, Code.NO_BOUNDARY, layer="absent")
    rejected(doc, Code.NO_BOUNDARY, layer='SITE"] *')
    doc.modelspace().add_lwpolyline(RING, close=True, dxfattribs={"layer": "SITE"})
    rejected(doc, Code.AMBIGUOUS_BOUNDARY, layer="SITE")


def test_open_and_3d_candidates_are_not_silently_ignored():
    doc, _ = document()
    extra = doc.modelspace().add_polyline3d([(0, 0, 1), (1, 1, 1), (1, 0, 1)])
    rejected(doc, Code.AMBIGUOUS_BOUNDARY)
    doc.modelspace().delete_entity(extra)
    doc.modelspace().add_lwpolyline(RING, close=False)
    rejected(doc, Code.AMBIGUOUS_BOUNDARY)


@pytest.mark.parametrize("unit", [0, 99])
def test_unknown_units_require_explicit_override(unit):
    doc, _ = document()
    doc.header["$INSUNITS"] = unit
    rejected(doc, Code.UNIT_REQUIRED)
    site = read_dxf(payload(doc), unit_override="mm")
    assert site.area_m2 == pytest.approx(0.00022)
    assert site.source_status == "user_provided"
    assert site.warnings == ("UNIT_OVERRIDDEN",)


def test_missing_units_and_unit_conflict():
    doc, _ = document()
    rejected(doc, Code.UNIT_CONFLICT, unit_override="mm")
    assert read_dxf(payload(doc), unit_override="m").source_status == "drawing_derived"
    del doc.header["$INSUNITS"]
    rejected(doc, Code.UNIT_REQUIRED)


def test_absent_header_does_not_accept_ezdxf_default_meter():
    doc, _ = document()
    data = payload(doc)
    start = data.index("  0\nSECTION\n  2\nHEADER\n")
    end = data.index("  0\nENDSEC\n", start) + len("  0\nENDSEC\n")
    with pytest.raises(GeometryError, match="^UNIT_REQUIRED$"):
        read_dxf(data[:start] + data[end:])


@pytest.mark.parametrize("extra,code", [(" 30\n0.0\n", Code.NON_2D),
                                         (" 42\nnan\n", Code.NONFINITE_COORDINATES)])
def test_raw_lwpolyline_information_is_not_silently_dropped(extra, code):
    doc, _ = document()
    data = payload(doc)
    index = data.index("AcDbPolyline\n")
    at = data.index(" 20\n0.0\n", index) + len(" 20\n0.0\n")
    with pytest.raises(GeometryError) as error:
        read_dxf(data[:at] + extra + data[at:])
    assert error.value.code == code


def test_raw_zero_extrusion_is_not_repaired_by_ezdxf():
    doc, _ = document()
    data = payload(doc)
    at = data.index("AcDbPolyline\n") + len("AcDbPolyline\n")
    with pytest.raises(GeometryError, match="^UNSUPPORTED_PLANE$"):
        read_dxf(data[:at] + "210\n0\n220\n0\n230\n0\n" + data[at:])


@pytest.mark.parametrize("unit", [1, 2, 5, 21, 24])
def test_other_known_units_not_reinterpreted(unit):
    doc, _ = document(units=unit)
    rejected(doc, Code.UNSUPPORTED_UNIT)
    rejected(doc, Code.UNSUPPORTED_UNIT, unit_override="m")


@pytest.mark.parametrize("kind", ["LWPOLYLINE", "POLYLINE"])
@pytest.mark.parametrize("index", [0, -1])
def test_bulge_including_closing_edge_rejected(kind, index):
    doc, entity = document(kind)
    if kind == "LWPOLYLINE":
        entity[index] = (*RING[index], 0, 0, 0.25)
    else:
        entity.vertices[index].dxf.bulge = 0.25
    rejected(doc, Code.UNSUPPORTED_CURVE)


@pytest.mark.parametrize("flag", [2, 4])
def test_polyline_curve_or_spline_fit_flags(flag):
    doc, entity = document("POLYLINE")
    entity.dxf.flags |= flag
    rejected(doc, Code.UNSUPPORTED_CURVE)


@pytest.mark.parametrize("flag", [1, 2, 8, 16])
def test_vertex_fit_flags(flag):
    doc, entity = document("POLYLINE")
    entity.vertices[0].dxf.flags = flag
    rejected(doc, Code.UNSUPPORTED_CURVE)


@pytest.mark.parametrize("kind", ["LWPOLYLINE", "POLYLINE"])
@pytest.mark.parametrize("attribute,value", [("extrusion", (0, 1, 0)), ("extrusion", (0, 0, -1)),
                                             ("thickness", 1), ("elevation", 2)])
def test_unsupported_planes(kind, attribute, value):
    doc, entity = document(kind)
    if kind == "POLYLINE" and attribute == "elevation":
        value = (0, 0, value)
    setattr(entity.dxf, attribute, value)
    rejected(doc, Code.UNSUPPORTED_PLANE)


def test_3d_polyline_and_vertex_z_rejected():
    doc = ezdxf.new("R2010", units=6)
    doc.modelspace().add_polyline3d([(0, 0, 0), (1, 0, 0), (1, 1, 0)], close=True)
    rejected(doc, Code.NON_2D)
    doc, entity = document("POLYLINE")
    entity.vertices[0].dxf.location = (0, 0, 1)
    rejected(doc, Code.NON_2D)


@pytest.mark.parametrize("kind", ["LWPOLYLINE", "POLYLINE"])
def test_width_rejected(kind):
    doc, entity = document(kind)
    if kind == "LWPOLYLINE":
        entity.dxf.const_width = 1
    else:
        entity.vertices[-1].dxf.end_width = 1
    rejected(doc, Code.UNSUPPORTED_WIDTH)


def test_georeferenced_dxf_rejected():
    doc, _ = document()
    doc.modelspace().new_geodata()
    rejected(doc, Code.UNSUPPORTED_CRS)


def test_blocks_paperspace_and_other_entities_not_adopted():
    doc = ezdxf.new("R2010", units=6)
    doc.blocks.new("EXAMPLE").add_lwpolyline(RING, close=True)
    doc.modelspace().add_blockref("EXAMPLE", (0, 0))
    doc.modelspace().add_circle((0, 0), 1)
    doc.paperspace().add_lwpolyline(RING, close=True)
    rejected(doc, Code.NO_BOUNDARY)


@pytest.mark.parametrize("points,code", [
    ([(0, 0), (1, 0)], Code.TOO_FEW_VERTICES),
    ([(0, 0), (1, 0), (2, 0)], Code.ZERO_AREA),
    ([(0, 0), (4, 3), (0, 4), (3, 0)], Code.INVALID_POLYGON),
])
def test_invalid_geometry(points, code):
    doc, _ = document(points=points)
    rejected(doc, code)


@pytest.mark.parametrize("text", ["", "synthetic-private-marker", "0\nSECTION\n", "0\nEOF\n"])
def test_malformed_dxf_has_only_fixed_error(text):
    with pytest.raises(GeometryError, match="^INVALID_DXF$"):
        read_dxf(text)


def test_native_diagnostics_and_exceptions_are_discarded(monkeypatch, capsys, caplog):
    def noisy_reader(*args):
        print("synthetic-private-marker")
        logging.error("synthetic-private-marker")
        raise ValueError("synthetic-private-marker")
    doc, _ = document()
    data = payload(doc)
    monkeypatch.setattr(ezdxf, "read", noisy_reader)
    old_level = logging.root.manager.disable
    with pytest.raises(GeometryError, match="^INVALID_DXF$"):
        read_dxf(data)
    assert capsys.readouterr() == ("", "")
    assert caplog.text == ""
    assert logging.root.manager.disable == old_level


def test_cold_import_does_not_print_machine_paths_or_build_font_cache(tmp_path):
    script = "from bve.geometry._dxf_runtime import ezdxf_module; ezdxf_module(); print('PASS')"
    env = dict(os.environ, XDG_CACHE_HOME=str(tmp_path))
    completed = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env)
    assert completed.returncode == 0
    assert completed.stdout == "PASS\n" and completed.stderr == ""
    assert list(tmp_path.iterdir()) == []
