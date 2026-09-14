"""Strict ring validation and unit scaling. No projection or geometry repair."""
import math
import warnings

from shapely import Polygon, normalize, orient_polygons
from shapely.errors import GEOSException

from .errors import Code, GeometryError
from .model import Unit

MAX_POSITIONS = 100_000


def require_unit(value: object) -> Unit:
    if value is None:
        raise GeometryError(Code.UNIT_REQUIRED)
    if value not in ("m", "mm"):
        raise GeometryError(Code.UNSUPPORTED_UNIT)
    return value


def normalized_polygon(coordinates: object, unit: Unit) -> Polygon:
    """Accept closed rings of plain numbers; return a canonical valid m Polygon."""
    require_unit(unit)
    if type(coordinates) is not list or not coordinates:
        raise GeometryError(Code.INVALID_COORDINATES)
    rings = []
    count = 0
    original_by_normalized = {}
    for ring in coordinates:
        if type(ring) is not list or not ring:
            raise GeometryError(Code.INVALID_COORDINATES)
        count += len(ring)
        if count > MAX_POSITIONS:
            raise GeometryError(Code.INPUT_TOO_LARGE)
        points = []
        for position in ring:
            if type(position) not in (list, tuple):
                raise GeometryError(Code.INVALID_COORDINATES)
            if len(position) != 2:
                raise GeometryError(Code.NON_2D)
            result = []
            for value in position:
                if type(value) not in (int, float):
                    raise GeometryError(Code.INVALID_COORDINATES)
                try:
                    number = float(value)
                except OverflowError:
                    raise GeometryError(Code.NUMERIC_RANGE) from None
                if not math.isfinite(number):
                    raise GeometryError(Code.NONFINITE_COORDINATES)
                if type(value) is int and number != value:
                    raise GeometryError(Code.NUMERIC_RANGE)
                scaled = number / 1000 if unit == "mm" else number
                if number != 0 and scaled == 0:
                    raise GeometryError(Code.NUMERIC_RANGE)
                result.append(0.0 if scaled == 0 else scaled)
            point = tuple(result)
            original = tuple(position)
            if point in original_by_normalized and original_by_normalized[point] != original:
                raise GeometryError(Code.NUMERIC_RANGE)
            original_by_normalized[point] = original
            points.append(point)
        if points[0] != points[-1]:
            raise GeometryError(Code.OPEN_BOUNDARY)
        while len(points) > 1 and points[-2] == points[0]:
            points.pop()
        if len(set(points)) < 3:
            raise GeometryError(Code.TOO_FEW_VERTICES)
        rings.append(points)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            polygon = Polygon(rings[0], rings[1:])
            if not math.isfinite(polygon.area):
                raise GeometryError(Code.NUMERIC_RANGE)
            if polygon.area <= 0:
                raise GeometryError(Code.ZERO_AREA)
            if not polygon.is_valid:
                raise GeometryError(Code.INVALID_POLYGON)
            return orient_polygons(normalize(polygon))
    except (GEOSException, RuntimeWarning, OverflowError):
        raise GeometryError(Code.NUMERIC_RANGE) from None
