"""Bounded local-XY GeoJSON-shaped input; geographic GeoJSON is unsupported."""
from hashlib import sha256
import json
import math
from typing import get_args

from .errors import Code, GeometryError
from .model import SiteGeometry, SourceStatus
from .normalization import normalized_polygon, require_unit

MAX_INPUT_BYTES = 4 * 1024 * 1024
MAX_DEPTH = 32


def _object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _constant(_: str) -> None:
    raise ValueError


def read_geojson(payload: bytes | str) -> SiteGeometry:
    """Read bytes or UTF-8 text; never retain arbitrary metadata or file paths."""
    if type(payload) not in (bytes, str):
        raise GeometryError(Code.INVALID_JSON)
    try:
        raw = payload.encode("utf-8") if type(payload) is str else payload
        if len(raw) > MAX_INPUT_BYTES:
            raise GeometryError(Code.INPUT_TOO_LARGE)
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        pending = [(data, 0)]
        while pending:
            value, depth = pending.pop()
            if depth > MAX_DEPTH:
                raise ValueError
            if type(value) is dict:
                pending.extend((item, depth + 1) for item in value.values())
                for key in value:
                    key.encode("utf-8")
            elif type(value) is list:
                pending.extend((item, depth + 1) for item in value)
            elif type(value) is str:
                value.encode("utf-8")
            elif type(value) is float and not math.isfinite(value):
                raise GeometryError(Code.NONFINITE_COORDINATES)
    except GeometryError:
        raise
    except (ValueError, RecursionError, OverflowError):
        raise GeometryError(Code.INVALID_JSON) from None
    if type(data) is not dict:
        raise GeometryError(Code.UNSUPPORTED_TYPE)
    if data.get("type") == "Feature":
        geometry = data.get("geometry")
        metadata = data.get("properties")
        if type(metadata) is not dict:
            raise GeometryError(Code.INVALID_METADATA)
        if any(key in data for key in ("unit", "coordinateSystem", "sourceStatus")):
            raise GeometryError(Code.INVALID_METADATA)
        if type(geometry) is dict and any(key in geometry for key in ("unit", "coordinateSystem", "sourceStatus")):
            raise GeometryError(Code.INVALID_METADATA)
    elif data.get("type") == "Polygon":
        geometry = metadata = data
    else:
        raise GeometryError(Code.UNSUPPORTED_TYPE)
    if type(geometry) is not dict or geometry.get("type") != "Polygon":
        raise GeometryError(Code.UNSUPPORTED_TYPE)
    if any("crs" in container for container in (data, geometry, metadata)):
        raise GeometryError(Code.UNSUPPORTED_CRS)
    coordinate_system = metadata.get("coordinateSystem")
    if coordinate_system is None:
        raise GeometryError(Code.CRS_REQUIRED)
    if coordinate_system != "local_xy":
        raise GeometryError(Code.UNSUPPORTED_CRS)
    unit = require_unit(metadata.get("unit"))
    status = metadata.get("sourceStatus", "user_provided")
    if status not in get_args(SourceStatus):
        raise GeometryError(Code.INVALID_METADATA)
    polygon = normalized_polygon(geometry.get("coordinates"), unit)
    return SiteGeometry(polygon, "geojson", unit, status, "sha256:" + sha256(raw).hexdigest())
