"""Strict selection of straight, closed modelspace XY polylines using ezdxf."""
from hashlib import sha256
import io
import math

from ._dxf_runtime import ezdxf_module, quiet_dxf
from .errors import Code, GeometryError
from .geojson import MAX_INPUT_BYTES
from .model import SiteGeometry
from .normalization import normalized_polygon, require_unit


def _unit(header_unit: int, override: str | None):
    if override is not None:
        require_unit(override)
    known = {4: "mm", 6: "m"}.get(header_unit)
    if known:
        if override is not None and override != known:
            raise GeometryError(Code.UNIT_CONFLICT)
        return known, "drawing_derived", ()
    if 1 <= header_unit <= 24:
        raise GeometryError(Code.UNSUPPORTED_UNIT)
    if override is None:
        raise GeometryError(Code.UNIT_REQUIRED)
    return override, "user_provided", ("UNIT_OVERRIDDEN",)


def _preflight(text: str) -> int:
    """Reject source tags that ezdxf would discard or coerce during entity loading."""
    from ezdxf.lldxf.tagger import ascii_tags_loader
    from ezdxf.lldxf.tags import group_tags

    tags = list(ascii_tags_loader(io.StringIO(text)))
    if not tags or (tags[0].code, tags[0].value) != (0, "SECTION") or (tags[-1].code, tags[-1].value) != (0, "EOF"):
        raise GeometryError(Code.INVALID_DXF)
    header_unit = 0
    sections = set()
    for group in group_tags(tags):
        kind = group[0].value
        if kind == "SECTION":
            if len(group) < 2 or group[1].code != 2 or group[1].value in sections:
                raise GeometryError(Code.INVALID_DXF)
            sections.add(group[1].value)
            if group[1].value == "HEADER":
                units = [index for index, tag in enumerate(group) if tag.code == 9 and tag.value == "$INSUNITS"]
                if len(units) > 1:
                    raise GeometryError(Code.INVALID_DXF)
                if units:
                    next_tag = group[units[0] + 1]
                    if next_tag.code != 70:
                        raise GeometryError(Code.INVALID_DXF)
                    header_unit = int(next_tag.value)
        if kind not in ("LWPOLYLINE", "POLYLINE", "VERTEX"):
            continue
        # Point compiler accepts 3D vertices for LWPOLYLINE then drops Z.
        if kind == "LWPOLYLINE" and any(tag.code == 30 for tag in group):
            raise GeometryError(Code.NON_2D)
        # Repeated scalar fields can hide a curve/unit/plane declaration. Repeated
        # per-vertex LWPOLYLINE fields are legal, but at most once for each vertex.
        scalar_codes = {38, 39, 43, 70, 90, 210, 220, 230}
        seen = set()
        vertex_seen = set()
        started = False
        for tag in group:
            code = tag.code
            if code in scalar_codes:
                if code in seen:
                    raise GeometryError(Code.INVALID_DXF)
                seen.add(code)
            if code == 10:
                vertex_seen = set()
                started = True
            if kind == "LWPOLYLINE" and code in (20, 40, 41, 42) and not started:
                raise GeometryError(Code.INVALID_DXF)
            if code in (10, 20, 30, 40, 41, 42):
                if code in vertex_seen:
                    raise GeometryError(Code.INVALID_DXF)
                vertex_seen.add(code)
            if code in {10, 20, 30, 38, 39, 40, 41, 42, 43, 210, 220, 230}:
                if not math.isfinite(float(tag.value)):
                    raise GeometryError(Code.NONFINITE_COORDINATES)
        if kind in ("LWPOLYLINE", "POLYLINE"):
            extrusion = {210: 0.0, 220: 0.0, 230: 1.0}
            extrusion.update({tag.code: float(tag.value) for tag in group if tag.code in extrusion})
            if tuple(extrusion.values()) != (0, 0, 1):
                raise GeometryError(Code.UNSUPPORTED_PLANE)
        if kind == "LWPOLYLINE":
            xs = sum(tag.code == 10 for tag in group)
            ys = sum(tag.code == 20 for tag in group)
            counts = [int(tag.value) for tag in group if tag.code == 90]
            if counts != [xs] or xs != ys:
                raise GeometryError(Code.INVALID_DXF)
        elif kind == "VERTEX":
            if sum(tag.code == 10 for tag in group) != 1 or sum(tag.code == 20 for tag in group) != 1:
                raise GeometryError(Code.INVALID_DXF)
    if "ENTITIES" not in sections:
        raise GeometryError(Code.INVALID_DXF)
    return header_unit


def read_dxf(payload: bytes | str, *, layer: str | None = None,
             unit_override: str | None = None) -> SiteGeometry:
    """Read UTF-8 text DXF (including ASCII), never binary/recovered DXF.

    Only exact layer-name matching; no query expression evaluation, largest-area
    guessing, block explosion, paperspace adoption or coordinate-system projection.
    """
    if type(payload) not in (bytes, str):
        raise GeometryError(Code.INVALID_DXF)
    if layer is not None and (type(layer) is not str or not layer):
        raise GeometryError(Code.INVALID_ARGUMENTS)
    try:
        raw = payload.encode("utf-8") if type(payload) is str else payload
        if len(raw) > MAX_INPUT_BYTES:
            raise GeometryError(Code.INPUT_TOO_LARGE)
        text = raw.decode("utf-8")
        with quiet_dxf():
            ezdxf = ezdxf_module()
            header_unit = _preflight(text)
            unit, status, notes = _unit(header_unit, unit_override)
            doc = ezdxf.read(io.StringIO(text))
            if any(entity.dxftype() == "GEODATA" for entity in doc.objects):
                raise GeometryError(Code.UNSUPPORTED_CRS)
            candidates = [entity for entity in doc.modelspace()
                          if entity.dxftype() in ("LWPOLYLINE", "POLYLINE")
                          and (layer is None or entity.dxf.layer.casefold() == layer.casefold())]
            if not candidates:
                raise GeometryError(Code.NO_BOUNDARY)
            if len(candidates) != 1:
                raise GeometryError(Code.AMBIGUOUS_BOUNDARY)
            boundary = candidates[0]
            lightweight = boundary.dxftype() == "LWPOLYLINE"
            if not lightweight and not boundary.is_2d_polyline:
                raise GeometryError(Code.NON_2D)
            if not boundary.is_closed:
                raise GeometryError(Code.OPEN_BOUNDARY)
            if not lightweight and (boundary.dxf.flags & 6 or boundary.dxf.get("smooth_type", 0)):
                raise GeometryError(Code.UNSUPPORTED_CURVE)
            if tuple(boundary.dxf.extrusion) != (0, 0, 1):
                raise GeometryError(Code.UNSUPPORTED_PLANE)
            elevation = boundary.dxf.elevation
            if (elevation != 0 if lightweight else tuple(elevation) != (0, 0, 0)):
                raise GeometryError(Code.UNSUPPORTED_PLANE)
            if boundary.dxf.get("thickness", 0) != 0:
                raise GeometryError(Code.UNSUPPORTED_PLANE)
            if lightweight:
                points = [tuple(float(value) for value in point) for point in boundary.get_points("xyseb")]
                if boundary.dxf.get("const_width", 0) != 0:
                    raise GeometryError(Code.UNSUPPORTED_WIDTH)
            else:
                if boundary.dxf.get("default_start_width", 0) != 0 or boundary.dxf.get("default_end_width", 0) != 0:
                    raise GeometryError(Code.UNSUPPORTED_WIDTH)
                points = []
                for vertex in boundary.vertices:
                    if vertex.dxf.flags & (1 | 2 | 8 | 16):
                        raise GeometryError(Code.UNSUPPORTED_CURVE)
                    if vertex.dxf.flags & (32 | 64 | 128) or vertex.dxf.location.z != 0:
                        raise GeometryError(Code.NON_2D)
                    points.append((vertex.dxf.location.x, vertex.dxf.location.y,
                                   vertex.dxf.start_width, vertex.dxf.end_width, vertex.dxf.bulge))
            if any(point[4] != 0 for point in points):
                raise GeometryError(Code.UNSUPPORTED_CURVE)
            if any(point[2] != 0 or point[3] != 0 for point in points):
                raise GeometryError(Code.UNSUPPORTED_WIDTH)
            ring = [[point[0], point[1]] for point in points]
            if ring and ring[-1] != ring[0]:
                ring.append(ring[0])
            polygon = normalized_polygon([ring], unit)
            return SiteGeometry(polygon, "dxf", unit, status, "sha256:" + sha256(raw).hexdigest(), notes)
    except GeometryError:
        raise
    except (Exception, SystemExit):
        # ezdxf exception messages can contain source tags or machine paths.
        raise GeometryError(Code.INVALID_DXF) from None
