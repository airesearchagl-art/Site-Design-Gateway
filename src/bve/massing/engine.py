"""One fixed conceptual baseline; geometry and decimal arithmetic stay distinct."""
from decimal import Decimal, DecimalException
import re

from bve.constraints import ValidatedConstraintResult
from bve.geometry import SiteGeometry

from .errors import Code, MassingError


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
