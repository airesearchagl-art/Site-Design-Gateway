"""Immutable search-owned results; derived metrics remain in Phase 3."""
from dataclasses import dataclass, field
from decimal import Decimal

from bve.constraints import ValidatedConstraintResult
from bve.geometry import SiteGeometry
from bve.massing import MassingCandidate


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

    @property
    def review_required(self) -> bool:
        return self.constraints.result.review_required

    def to_dict(self) -> dict:
        constraints = self.constraints.result
        return {"schemaVersion": "0.2",
                "inputReferences": {"project": self.constraints.result.project_reference,
                                    "geometry": self.site.source_reference,
                                    "constraints": self.constraints.reference},
                "constraintContext": {
                    "areaBasis": constraints.to_dict()["areaBasis"],
                    "constraintCaps": {"maxFootprintAreaM2": constraints.building_coverage.value,
                                       "maxTotalFloorAreaM2": constraints.floor_area_ratio.value,
                                       "maxHeightM": constraints.height.value}},
                "search": {"strategy": "floor_height_sweep_v0.1",
                           "ranking": "maximize_gross_floor_area_v0.1",
                           "floorHeightsM": list(self.floor_heights_m), "floorHeightStatus": "user_provided"},
                "summary": {"evaluated": len(self.floor_heights_m),
                            "accepted": len(self.ranked_candidates), "rejected": len(self.rejections),
                            "hasFeasibleCandidate": bool(self.ranked_candidates),
                            "reviewRequired": self.review_required},
                "rankedCandidates": [entry.to_dict() for entry in self.ranked_candidates],
                "rejections": [entry.to_dict() for entry in self.rejections]}
