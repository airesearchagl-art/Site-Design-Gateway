"""One fixed conceptual baseline; geometry and decimal arithmetic stay distinct."""
from decimal import Decimal, DecimalException
from fractions import Fraction
import math
import re
import warnings

from shapely import Polygon
from shapely.affinity import scale as affine_scale
from shapely.errors import GEOSException

from bve.constraints import ValidatedConstraintResult
from bve.geometry import SiteGeometry
from bve.geometry.normalization import MAX_POSITIONS, canonical_polygon

from .errors import Code, MassingError
from .model import MassingCandidate

MAX_SHRINK_ATTEMPTS = 64
MAX_FLOORS = 10_000


def _floor_height(value) -> Decimal:
    if value is None:
        raise MassingError(Code.FLOOR_HEIGHT_REQUIRED)
    if type(value) not in (str, int, float, Decimal):
        raise MassingError(Code.INVALID_FLOOR_HEIGHT)
    try:
        text = str(value)
        if len(text) > 3074 or re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", text) is None:
            raise MassingError(Code.INVALID_FLOOR_HEIGHT)
        height = Decimal(text)
        if (not height.is_finite() or height <= 0 or len(height.as_tuple().digits) > 1024
                or abs(height.as_tuple().exponent) > 1024):
            raise MassingError(Code.INVALID_FLOOR_HEIGHT)
        return height
    except (DecimalException, ValueError):
        raise MassingError(Code.INVALID_FLOOR_HEIGHT) from None


def _validate_inputs(site_geometry, constraint_result, floor_height_m):
    height = _floor_height(floor_height_m)
    if type(site_geometry) is not SiteGeometry or type(constraint_result) is not ValidatedConstraintResult:
        raise MassingError(Code.INVALID_ARGUMENTS)
    site_geometry.__post_init__()
    result = constraint_result.result
    if result.geometry_reference != site_geometry.source_reference:
        raise MassingError(Code.INPUT_REFERENCE_MISMATCH)
    actual = result.area_provenance[1].condition
    if actual.value != Decimal(str(site_geometry.area_m2)) or actual.status != site_geometry.source_status:
        raise MassingError(Code.INPUT_GEOMETRY_MISMATCH)
    if any(item.state != "COMPUTED" for item in (result.building_coverage, result.floor_area_ratio, result.height)):
        raise MassingError(Code.REQUIRED_CONSTRAINT_UNAVAILABLE)
    return height, result


def _require_supported_site(polygon: Polygon) -> None:
    if polygon.interiors or not polygon.equals(polygon.convex_hull):
        raise MassingError(Code.UNSUPPORTED_MASSING_SITE_GEOMETRY)
    if len(polygon.exterior.coords) > MAX_POSITIONS:
        raise MassingError(Code.RESOURCE_LIMIT)


def _check_footprint(site: Polygon, footprint: Polygon, target: Decimal) -> Decimal:
    if (not isinstance(footprint, Polygon) or footprint.is_empty or footprint.interiors
            or not footprint.is_valid or not math.isfinite(footprint.area) or footprint.area <= 0
            or any(len(point) != 2 or not all(math.isfinite(v) for v in point)
                   for point in footprint.exterior.coords)
            or not footprint.equals(footprint.convex_hull)):
        raise MassingError(Code.GEOMETRY_GENERATION_FAILED)
    if not site.covers(footprint):
        raise MassingError(Code.GEOMETRY_GENERATION_FAILED)
    actual = Decimal(str(footprint.area))
    if actual > target:
        raise MassingError(Code.GEOMETRY_GENERATION_FAILED)
    return actual


def _generate_footprint(site: Polygon, target: Decimal) -> Polygon:
    """Shrink from the original each time; cap checks use actual canonical area."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            _require_supported_site(site)
            site_area = Decimal(str(site.area))
            if target <= 0:
                raise MassingError(Code.NO_MASSING_CAPACITY)
            if target >= site_area:
                footprint = canonical_polygon(site)
            else:
                factor = math.sqrt(float(Fraction(target) / Fraction(site_area)))
                origin = site.centroid
                for attempt in range(MAX_SHRINK_ATTEMPTS + 1):
                    if not 0 < factor <= 1:
                        raise MassingError(Code.GEOMETRY_GENERATION_FAILED)
                    footprint = canonical_polygon(affine_scale(site, xfact=factor, yfact=factor, origin=origin))
                    if not math.isfinite(footprint.area):
                        raise MassingError(Code.GEOMETRY_GENERATION_FAILED)
                    if Decimal(str(footprint.area)) <= target:
                        break
                    if attempt == MAX_SHRINK_ATTEMPTS:
                        raise MassingError(Code.GEOMETRY_GENERATION_FAILED)
                    factor = math.nextafter(factor, 0.0)
            _check_footprint(site, footprint, target)
            return footprint
    except (GEOSException, RuntimeWarning, OverflowError, ZeroDivisionError, DecimalException):
        raise MassingError(Code.GEOMETRY_GENERATION_FAILED) from None


def _floor_quotient(cap: Decimal, divisor: Decimal) -> int:
    """Integer ratio division, with no Decimal rounding or float conversion."""
    numerator, denominator = (Fraction(cap) / Fraction(divisor)).as_integer_ratio()
    return numerator // denominator


def _floor_count(result, actual: Decimal, floor_height: Decimal) -> int:
    floors = min(_floor_quotient(result.floor_area_ratio.value, actual),
                 _floor_quotient(result.height.value, floor_height))
    if floors < 1:
        raise MassingError(Code.NO_FEASIBLE_MASSING)
    if floors > MAX_FLOORS:
        raise MassingError(Code.RESOURCE_LIMIT)
    return floors


def _validate_candidate(candidate: MassingCandidate) -> None:
    height, result = _validate_inputs(candidate.site, candidate.constraints, candidate.floor_height_m)
    _require_supported_site(candidate.site.polygon)
    actual = _check_footprint(candidate.site.polygon, candidate.footprint, candidate.target_footprint_area_m2)
    # Check each final cap explicitly, even though target selection also bounds
    # the generated area. These checks protect export and future internal changes.
    if actual > result.building_coverage.value:
        raise MassingError(Code.GEOMETRY_GENERATION_FAILED)
    if candidate.gross_floor_area_m2 > result.floor_area_ratio.value or candidate.height_m > result.height.value:
        raise MassingError(Code.GEOMETRY_GENERATION_FAILED)
    expected_target = min(Decimal(str(candidate.site.area_m2)), result.building_coverage.value,
                          result.floor_area_ratio.value)
    if (candidate.target_footprint_area_m2 != expected_target or type(candidate.floor_count) is not int
            or candidate.floor_count != _floor_count(result, actual, height)):
        raise MassingError(Code.GEOMETRY_GENERATION_FAILED)


def generate_massing_candidate(site_geometry, constraint_result, *, floor_height_m=None) -> MassingCandidate:
    """Return one convex baseline stack; floor height is always explicit."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            floor_height, result = _validate_inputs(site_geometry, constraint_result, floor_height_m)
            _require_supported_site(site_geometry.polygon)
            target = min(Decimal(str(site_geometry.area_m2)), result.building_coverage.value,
                         result.floor_area_ratio.value)
            if target <= 0 or result.floor_area_ratio.value <= 0 or result.height.value <= 0:
                raise MassingError(Code.NO_MASSING_CAPACITY)
            footprint = _generate_footprint(site_geometry.polygon, target)
            actual = Decimal(str(footprint.area))
            floors = _floor_count(result, actual, floor_height)
            candidate = MassingCandidate(site_geometry, constraint_result, footprint, target, floors, floor_height)
            _validate_candidate(candidate)
            return candidate
    except DecimalException:
        raise MassingError(Code.NUMERIC_RANGE) from None
    except (GEOSException, RuntimeWarning, OverflowError, ZeroDivisionError):
        raise MassingError(Code.GEOMETRY_GENERATION_FAILED) from None
