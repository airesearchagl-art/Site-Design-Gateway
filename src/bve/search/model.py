"""Immutable search-owned results; derived metrics remain in Phase 3."""
from dataclasses import dataclass, field
from decimal import Decimal

from bve.constraints import ValidatedConstraintResult
from bve.geometry import SiteGeometry
from bve.massing import MassingCandidate
from bve.spatial import ValidatedBuildableArea


@dataclass(frozen=True)
class Rejection:
    floor_height_m: Decimal
    code: str

    def to_dict(self) -> dict:
        return {"floorHeightM": self.floor_height_m, "code": self.code}


@dataclass(frozen=True)
class RankedCandidate:
    rank: int
    candidate_reference: str
    gross_floor_area_m2: Decimal
    candidate: MassingCandidate = field(repr=False)

    def to_dict(self) -> dict:
        return {"rank": self.rank, "candidateReference": self.candidate_reference,
                "grossFloorAreaM2": self.gross_floor_area_m2, "candidate": self.candidate.to_dict()}


@dataclass(frozen=True)
class SearchResult:
    site: SiteGeometry = field(repr=False)
    constraints: ValidatedConstraintResult = field(repr=False)
    floor_heights_m: tuple[Decimal, ...]
    ranked_candidates: tuple[RankedCandidate, ...]
    rejections: tuple[Rejection, ...]
    buildable_area: ValidatedBuildableArea | None = field(default=None, repr=False)

    @property
    def schema_version(self) -> str:
        return {"0.1": "0.2", "0.2": "0.3", "0.3": "0.4", "0.4": "0.5"}[self.constraints.result.schema_version]

    @property
    def review_required(self) -> bool:
        return (self.constraints.result.review_required
                or (self.buildable_area is not None and self.buildable_area.review_required))

    def to_dict(self) -> dict:
        constraints = self.constraints.result
        context = {"areaBasis": constraints.to_dict()["areaBasis"],
                   "constraintCaps": {"maxFootprintAreaM2": constraints.building_coverage.value,
                                      "maxTotalFloorAreaM2": constraints.floor_area_ratio.value,
                                      "maxHeightM": constraints.height.value}}
        if self.schema_version in ("0.3", "0.4", "0.5"):
            context["floorAreaRatio"] = constraints.to_dict()["constraints"]["floorAreaRatio"]
        if self.schema_version in ("0.4", "0.5"):
            context["height"] = constraints.to_dict()["constraints"]["height"]
        data = {"schemaVersion": self.schema_version,
                "inputReferences": {"project": self.constraints.result.project_reference,
                                    "geometry": self.site.source_reference,
                                    "constraints": self.constraints.reference},
                "constraintContext": context,
                "search": {"strategy": "floor_height_sweep_v0.1",
                           "ranking": "maximize_gross_floor_area_v0.1",
                           "floorHeightsM": list(self.floor_heights_m), "floorHeightStatus": "user_provided"},
                "summary": {"evaluated": len(self.floor_heights_m),
                            "accepted": len(self.ranked_candidates), "rejected": len(self.rejections),
                            "hasFeasibleCandidate": bool(self.ranked_candidates),
                            "reviewRequired": self.review_required},
                "rankedCandidates": [entry.to_dict() for entry in self.ranked_candidates],
                "rejections": [entry.to_dict() for entry in self.rejections]}
        if self.buildable_area is not None:
            data["inputReferences"]["buildableArea"] = self.buildable_area.reference
            data["spatialContext"] = self.buildable_area.spatial_context()
        return data
