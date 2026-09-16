"""Immutable inputs/footprint; metrics are derived from the actual polygon."""
from dataclasses import dataclass, field
from decimal import Decimal

from shapely import Polygon

from bve.constraints import ValidatedConstraintResult
from bve.constraints.arithmetic import _context
from bve.geometry import SiteGeometry
from bve.spatial import ValidatedBuildableArea


@dataclass(frozen=True)
class MassingCandidate:
    site: SiteGeometry = field(repr=False)
    constraints: ValidatedConstraintResult = field(repr=False)
    footprint: Polygon = field(repr=False)
    target_footprint_area_m2: Decimal
    floor_count: int
    floor_height_m: Decimal
    buildable_area: ValidatedBuildableArea | None = field(default=None, repr=False)

    @property
    def footprint_area_m2(self) -> Decimal:
        return Decimal(str(self.footprint.area))

    @property
    def height_m(self) -> Decimal:
        return _context().multiply(Decimal(self.floor_count), self.floor_height_m)

    @property
    def gross_floor_area_m2(self) -> Decimal:
        return _context().multiply(Decimal(self.floor_count), self.footprint_area_m2)

    @property
    def review_required(self) -> bool:
        return (self.constraints.result.review_required
                or (self.buildable_area is not None and self.buildable_area.review_required))

    def to_dict(self) -> dict:
        result = self.constraints.result
        data = {"schemaVersion": "0.1",
                "inputReferences": {"project": result.project_reference,
                                    "geometry": self.site.source_reference,
                                    "constraints": self.constraints.reference},
                "generator": {"strategy": "max_footprint_stack_v0.1",
                              "footprintMethod": "convex_homothetic_footprint_v0.1",
                              "floorHeightM": self.floor_height_m, "floorHeightStatus": "user_provided"},
                "constraintCaps": {"maxFootprintAreaM2": result.building_coverage.value,
                                   "maxTotalFloorAreaM2": result.floor_area_ratio.value,
                                   "maxHeightM": result.height.value},
                "candidate": {"footprint": {"type": "Polygon", "coordinates": [
                    [[Decimal(str(value)) for value in point] for point in self.footprint.exterior.coords]]},
                    "targetFootprintAreaM2": self.target_footprint_area_m2,
                    "footprintAreaM2": self.footprint_area_m2, "floorCount": self.floor_count,
                    "heightM": self.height_m, "grossFloorAreaM2": self.gross_floor_area_m2,
                    "reviewRequired": self.review_required}}
        if self.buildable_area is not None:
            data["schemaVersion"] = "0.2"
            data["inputReferences"]["buildableArea"] = self.buildable_area.reference
            data["generator"]["strategy"] = "max_footprint_stack_v0.2"
            data["generator"]["footprintMethod"] = "convex_homothetic_buildable_area_v0.1"
        return data
