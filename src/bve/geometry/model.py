"""Immutable normalized contract. Derived values cannot drift from the polygon."""
from dataclasses import dataclass, field
import math
import re
from typing import Literal, get_args

from shapely import Polygon

from .errors import Code, GeometryError

Unit = Literal["m", "mm"]
SourceFormat = Literal["geojson", "dxf"]
SourceStatus = Literal[
    "official_verified", "user_provided", "drawing_derived", "llm_researched",
    "assumed", "unknown", "review_required",
]


@dataclass(frozen=True)
class SiteGeometry:
    polygon: Polygon = field(repr=False)
    source_format: SourceFormat
    source_unit: Unit
    source_status: SourceStatus
    source_reference: str
    warnings: tuple[str, ...] = ()
    normalized_unit: Literal["m"] = field(default="m", init=False)

    def __post_init__(self) -> None:
        if (self.source_format not in get_args(SourceFormat)
                or self.source_unit not in get_args(Unit)
                or self.source_status not in get_args(SourceStatus)
                or type(self.source_reference) is not str
                or re.fullmatch(r"sha256:[0-9a-f]{64}", self.source_reference) is None
                or type(self.warnings) is not tuple
                or any(w != "UNIT_OVERRIDDEN" for w in self.warnings)):
            raise GeometryError(Code.INVALID_METADATA)
        polygon = self.polygon
        if not isinstance(polygon, Polygon) or polygon.is_empty:
            raise GeometryError(Code.INVALID_POLYGON)
        for ring in [polygon.exterior, *polygon.interiors]:
            for position in ring.coords:
                if len(position) != 2:
                    raise GeometryError(Code.NON_2D)
                if not all(math.isfinite(value) for value in position):
                    raise GeometryError(Code.NONFINITE_COORDINATES)
        if not math.isfinite(polygon.area):
            raise GeometryError(Code.NUMERIC_RANGE)
        if polygon.area <= 0:
            raise GeometryError(Code.ZERO_AREA)
        if not polygon.is_valid:
            raise GeometryError(Code.INVALID_POLYGON)

    @property
    def area_m2(self) -> float:
        return self.polygon.area

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return self.polygon.bounds
