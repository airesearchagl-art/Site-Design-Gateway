"""Synthetic ezdxf documents exercise selection and geometry-loss boundaries."""
import io
import hashlib
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
    rejected(doc, Code.INVALID_DXF)  # unsupported raw subclass fails before selection
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


def raw_groups(doc):
    lines = payload(doc).splitlines()
    groups = []
    for code, value in zip(lines[::2], lines[1::2]):
        if int(code) == 0:
            groups.append([])
        groups[-1].append((int(code), value))
    return groups


def render(groups):
    return "".join(f"{code}\n{value}\n" for group in groups for code, value in group)


@pytest.mark.parametrize("tag,code", [(42, Code.UNSUPPORTED_CURVE), (38, Code.UNSUPPORTED_PLANE),
                                      (39, Code.UNSUPPORTED_PLANE), (43, Code.UNSUPPORTED_WIDTH)])
def test_raw_nonzero_attributes_cannot_underflow_to_supported_zero(tag, code):
    doc, _ = document()
    groups = raw_groups(doc)
    entity = next(group for group in groups if group[0] == (0, "LWPOLYLINE"))
    at = next(i for i, pair in enumerate(entity) if pair[0] == 20) + 1
    entity.insert(at, (tag, "1e-400"))
    with pytest.raises(GeometryError) as error:
        read_dxf(render(groups))
    assert error.value.code == code


@pytest.mark.parametrize("kind,tag,value", [("LWPOLYLINE", 70, "1.9"), ("POLYLINE", 70, "1.9"),
                                          ("POLYLINE", 75, "0.5")])
def test_integer_attributes_cannot_be_truncated(kind, tag, value):
    doc, _ = document(kind)
    groups = raw_groups(doc)
    entity = next(group for group in groups if group[0] == (0, kind))
    entity[:] = [pair for pair in entity if pair[0] != tag]
    entity.append((tag, value))
    with pytest.raises(GeometryError, match="^INVALID_DXF$"):
        read_dxf(render(groups))


@pytest.mark.parametrize("tag,value", [(75, "5"), (30, "5"), (40, "1")])
def test_duplicate_polyline_attributes_cannot_hide_shape_information(tag, value):
    doc, _ = document("POLYLINE")
    groups = raw_groups(doc)
    entity = next(group for group in groups if group[0] == (0, "POLYLINE"))
    entity.extend([(tag, value), (tag, "0")])
    with pytest.raises(GeometryError):
        read_dxf(render(groups))


@pytest.mark.parametrize("value", ["9007199254740993", "1e-400", "4.00000000000000000001"])
def test_raw_coordinates_cannot_disappear(value):
    doc, _ = document(points=[(0, 0), (1, 0), (4, 0), (4, 4), (0, 4)])
    groups = raw_groups(doc)
    entity = next(group for group in groups if group[0] == (0, "LWPOLYLINE"))
    for i, (code, text) in enumerate(entity):
        if code == 10 and text == "1.0":
            entity[i] = (code, value)
    with pytest.raises(GeometryError, match="^NUMERIC_RANGE$"):
        read_dxf(render(groups))


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
    rejected(doc, Code.INVALID_DXF)  # explicitly unsupported 3D subclass
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
    circle = doc.modelspace().add_circle((0, 0), 1)
    doc.paperspace().add_lwpolyline(RING, close=True)
    rejected(doc, Code.UNSUPPORTED_CURVE)
    doc.modelspace().delete_entity(circle)
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


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_text_dxf_newlines_preserve_geometry(newline):
    doc, _ = document()
    site = read_dxf(payload(doc).replace("\n", newline))
    assert site.area_m2 == 220


@pytest.mark.parametrize("mode", ["repeated_subclass", "appdata", "before_subclass"])
def test_lwpolyline_vertices_cannot_be_hidden_from_parser(mode):
    doc, _ = document()
    groups = raw_groups(doc)
    entity = next(group for group in groups if group[0] == (0, "LWPOLYLINE"))
    if mode == "repeated_subclass":
        at = [i for i, pair in enumerate(entity) if pair[0] == 10][-1]
        entity.insert(at, (100, "AcDbPolyline"))
    elif mode == "appdata":
        at = [i for i, pair in enumerate(entity) if pair[0] == 10][-1]
        entity.insert(at, (102, "{SYNTHETIC"))
        entity.append((102, "}"))
    else:
        at = next(i for i, pair in enumerate(entity) if pair[0] == 10)
        point = entity[at:at + 2]
        del entity[at:at + 2]
        at = entity.index((100, "AcDbPolyline"))
        entity[at:at] = point
    with pytest.raises(GeometryError, match="^INVALID_DXF$"):
        read_dxf(render(groups))


@pytest.mark.parametrize("kind,subclass", [("POLYLINE", "AcDb3dPolyline"), ("VERTEX", "AcDb3dPolylineVertex")])
def test_inconsistent_3d_subclass_cannot_be_adopted_as_2d(kind, subclass):
    doc, _ = document("POLYLINE")
    groups = raw_groups(doc)
    entity = next(group for group in groups if group[0] == (0, kind))
    at = [i for i, pair in enumerate(entity) if pair[0] == 100][-1]
    entity[at] = (100, subclass)
    with pytest.raises(GeometryError, match="^INVALID_DXF$"):
        read_dxf(render(groups))


def test_trailing_dxf_after_eof_is_not_ignored():
    doc, _ = document()
    data = payload(doc)
    with pytest.raises(GeometryError, match="^INVALID_DXF$"):
        read_dxf(data + "0\nSECTION\n2\nOBJECTS\n0\nGEODATA\n0\nENDSEC\n0\nEOF\n")
    assert read_dxf(data + "\n  \n").area_m2 == 220


def test_modern_missing_subclasses_rejected_but_r12_supported():
    doc, _ = document("POLYLINE")
    groups = raw_groups(doc)
    for group in groups:
        if group[0] in ((0, "POLYLINE"), (0, "VERTEX")):
            group[:] = [pair for pair in group if pair[0] != 100]
    with pytest.raises(GeometryError, match="^INVALID_DXF$"):
        read_dxf(render(groups))
    with quiet_dxf():
        old = ezdxf.new("R12")
        old.modelspace().add_polyline2d(RING, close=True)
        text = payload(old)
    assert read_dxf(text, unit_override="m").area_m2 == 220


def add_curve(layout, kind, layer="SITE"):
    attributes = {"layer": layer}
    if kind == "ARC":
        layout.add_arc((0, 0), 2, 0, 90, dxfattribs=attributes)
    elif kind == "CIRCLE":
        layout.add_circle((0, 0), 2, dxfattribs=attributes)
    elif kind == "SPLINE":
        layout.add_spline([(0, 0), (1, 2), (3, 1), (4, 0)], dxfattribs=attributes)
    elif kind == "ELLIPSE":
        layout.add_ellipse((0, 0), (2, 0), ratio=0.5, dxfattribs=attributes)
    else:
        raise AssertionError("unsupported synthetic test kind")


@pytest.mark.parametrize("kind", ["ARC", "CIRCLE", "SPLINE", "ELLIPSE"])
@pytest.mark.parametrize("with_polyline", [False, True])
@pytest.mark.parametrize("layer", [None, "SITE"])
def test_unsupported_curve_in_selected_scope(kind, with_polyline, layer):
    doc = ezdxf.new("R2010", units=6)
    doc.layers.new("SITE")
    if with_polyline:
        doc.modelspace().add_lwpolyline(RING, close=True, dxfattribs={"layer": "SITE"})
    add_curve(doc.modelspace(), kind)
    rejected(doc, Code.UNSUPPORTED_CURVE, layer=layer)


@pytest.mark.parametrize("kind", ["ARC", "CIRCLE", "SPLINE", "ELLIPSE"])
def test_other_layer_curve_requires_explicit_site_selection(kind):
    doc, boundary = document()
    doc.layers.new("SITE")
    doc.layers.new("OTHER")
    boundary.dxf.layer = "SITE"
    add_curve(doc.modelspace(), kind, layer="OTHER")
    site = read_dxf(payload(doc), layer="site")
    assert site.area_m2 == 220
    rejected(doc, Code.UNSUPPORTED_CURVE)


@pytest.mark.parametrize("kind", ["ARC", "CIRCLE", "SPLINE", "ELLIPSE"])
def test_curve_outside_modelspace_is_not_in_boundary_scope(kind):
    doc, boundary = document()
    doc.layers.new("SITE")
    boundary.dxf.layer = "SITE"
    add_curve(doc.paperspace(), kind)
    add_curve(doc.blocks.new("EXAMPLE_CURVE"), kind)
    assert read_dxf(payload(doc), layer="SITE").area_m2 == 220
    assert read_dxf(payload(doc)).area_m2 == 220


@pytest.mark.parametrize("damage", ["missing_seqend", "orphan_vertex", "orphan_seqend",
    "duplicate_seqend", "interrupted", "nested_polyline", "seqend_before_polyline", "vertex_after_seqend"])
def test_raw_polyline_sequence_rejected_before_parser_repair(damage, monkeypatch):
    doc, _ = document("POLYLINE")
    groups = raw_groups(doc)
    start = next(i for i, group in enumerate(groups) if group[0] == (0, "POLYLINE"))
    end = next(i for i, group in enumerate(groups) if group[0] == (0, "SEQEND"))
    if damage == "missing_seqend":
        del groups[end]
    elif damage == "orphan_vertex":
        del groups[start]
    elif damage == "orphan_seqend":
        del groups[start:end]
    elif damage == "duplicate_seqend":
        groups.insert(end + 1, list(groups[end]))
    elif damage == "interrupted":
        groups.insert(end, [(0, "LINE"), (8, "0"), (10, "0"), (20, "0"), (11, "1"), (21, "1")])
    elif damage == "nested_polyline":
        groups.insert(start + 2, list(groups[start]))
    elif damage == "seqend_before_polyline":
        groups.insert(start, groups.pop(end))  # balanced counts, invalid order
    elif damage == "vertex_after_seqend":
        groups.insert(end - 1, groups.pop(end))  # closes before the final VERTEX
    calls = []
    original = ezdxf.read
    def tracked_read(*args, **kwargs):
        calls.append(True)
        return original(*args, **kwargs)
    monkeypatch.setattr(ezdxf, "read", tracked_read)
    with pytest.raises(GeometryError, match="^INVALID_DXF$"):
        read_dxf(render(groups))
    assert calls == []


@pytest.mark.parametrize("version", ["R12", "R2010"])
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_valid_polyline_sequence_versions_and_newlines(version, newline):
    with quiet_dxf():
        doc = ezdxf.new(version, units=6)
        doc.modelspace().add_polyline2d(RING, close=True)
        data = payload(doc).replace("\n", newline)
    site = read_dxf(data, unit_override="m" if version == "R12" else None)
    assert site.area_m2 == 220


def test_empty_polyline_sequence_is_structural_but_not_valid_geometry():
    from bve.geometry.dxf import _preflight
    doc, _ = document("POLYLINE", points=[])
    data = payload(doc)
    with quiet_dxf():
        unit, counts = _preflight(data)
    assert unit == 6 and counts["POLYLINE"] == 1 and counts["VERTEX"] == 0
    with pytest.raises(GeometryError):
        read_dxf(data)


def test_insert_attribute_seqend_is_not_an_orphan_polyline_terminator():
    doc, _ = document()
    doc.blocks.new("EXAMPLE_ATTRIBUTE").add_attdef("LABEL", (0, 0), text="synthetic")
    reference = doc.modelspace().add_blockref("EXAMPLE_ATTRIBUTE", (0, 0))
    reference.add_attrib("LABEL", "synthetic", (0, 0))
    assert read_dxf(payload(doc)).area_m2 == 220


@pytest.mark.parametrize("as_bytes", [False, True])
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_dxf_source_reference_matches_exact_input_bytes(as_bytes, newline):
    doc, boundary = document()
    doc.layers.new("合成境界")
    boundary.dxf.layer = "合成境界"
    text = payload(doc).replace("\n", newline)
    raw = text.encode("utf-8")
    site = read_dxf(raw if as_bytes else text)
    assert site.source_reference == "sha256:" + hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("initial_disable", [0, logging.WARNING])
@pytest.mark.parametrize("raise_inside", [False, True])
def test_quiet_dxf_restores_fresh_process_state(initial_disable, raise_inside):
    script = '''
import logging
import sys
logging.disable(int(sys.argv[1]))
before = (logging.root.manager.disable, sys.stdout, sys.stderr)
assert "bve.geometry._dxf_runtime" not in sys.modules
from bve.geometry._dxf_runtime import quiet_dxf
assert logging.root.manager.disable == before[0]
assert sys.stdout is before[1] and sys.stderr is before[2]
try:
    with quiet_dxf():
        assert logging.root.manager.disable == logging.CRITICAL
        assert sys.stdout is not before[1] and sys.stderr is not before[2]
        print("synthetic-hidden-output")
        print("synthetic-hidden-error", file=sys.stderr)
        if sys.argv[2] == "True":
            raise RuntimeError("synthetic-context-exception")
except RuntimeError:
    pass
assert logging.root.manager.disable == before[0]
assert sys.stdout is before[1] and sys.stderr is before[2]
print("PASS")
'''
    result = subprocess.run([sys.executable, "-c", script, str(initial_disable), str(raise_inside)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0
    assert result.stdout == "PASS\n" and result.stderr == ""
