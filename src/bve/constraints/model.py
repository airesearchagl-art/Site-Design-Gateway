"""Immutable traced results; derived state never collapses input provenance."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from .inputs import AreaSelection, Condition

REVIEW_STATUSES = frozenset(("assumed", "unknown", "review_required"))
FAR_STACK_REVIEW_STATUSES = frozenset(("llm_researched", "assumed", "unknown", "review_required"))
HEIGHT_STACK_REVIEW_STATUSES = frozenset(("llm_researched", "assumed", "unknown", "review_required"))
State = Literal["COMPUTED", "UNAVAILABLE", "ABSENT"]


@dataclass(frozen=True)
class Provenance:
    input: str
    reference: str
    condition: Condition

    @property
    def review_required(self) -> bool:
        return self.condition.status in REVIEW_STATUSES

    def to_dict(self) -> dict:
        return {"input": self.input, "reference": self.reference, "condition": self.condition.to_dict()}


@dataclass(frozen=True)
class Constraint:
    state: State
    calculation_id: str
    value: Decimal | None
    provenance: tuple[Provenance, ...]

    @property
    def review_required(self) -> bool:
        return any(item.review_required for item in self.provenance)

    def to_dict(self, value_key: str) -> dict:
        return {"state": self.state, "calculationId": self.calculation_id, value_key: self.value,
                "provenance": [item.to_dict() for item in self.provenance],
                "reviewRequired": self.review_required}


@dataclass(frozen=True)
class FarCapEntry:
    id: str
    kind: str
    provenance: Provenance

    @property
    def review_required(self) -> bool:
        return self.provenance.condition.status in FAR_STACK_REVIEW_STATUSES

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, **self.provenance.to_dict(),
                "reviewRequired": self.review_required}


@dataclass(frozen=True)
class FarStackConstraint:
    state: State
    value: Decimal | None
    effective_cap_percent: Decimal | None
    effective_cap_ids: tuple[str, ...]
    cap_stack: tuple[FarCapEntry, ...]
    provenance: tuple[Provenance, ...]

    @property
    def review_required(self) -> bool:
        return (any(item.review_required for item in self.provenance)
                or any(item.review_required for item in self.cap_stack))

    def to_dict(self, value_key: str) -> dict:
        return {"state": self.state, "calculationId": "floor_area_cap_stack_v0.2", value_key: self.value,
                "effectiveCapPercent": self.effective_cap_percent, "effectiveCapIds": list(self.effective_cap_ids),
                "capStack": [entry.to_dict() for entry in self.cap_stack],
                "provenance": [entry.to_dict() for entry in self.provenance], "reviewRequired": self.review_required}


@dataclass(frozen=True)
class HeightCapEntry:
    id: str
    kind: str
    provenance: Provenance

    @property
    def review_required(self) -> bool:
        return self.provenance.condition.status in HEIGHT_STACK_REVIEW_STATUSES

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, **self.provenance.to_dict(), "reviewRequired": self.review_required}


@dataclass(frozen=True)
class HeightStackConstraint:
    state: State
    value: Decimal | None
    effective_cap_ids: tuple[str, ...]
    cap_stack: tuple[HeightCapEntry, ...]

    @property
    def review_required(self) -> bool:
        return any(entry.review_required for entry in self.cap_stack)

    def to_dict(self, value_key: str) -> dict:
        return {"state": self.state, "calculationId": "height_cap_stack_v0.3", value_key: self.value,
                "effectiveHeightM": self.value, "effectiveCapIds": list(self.effective_cap_ids),
                "capStack": [entry.to_dict() for entry in self.cap_stack], "reviewRequired": self.review_required}


@dataclass(frozen=True)
class ConstraintResult:
    project_reference: str
    geometry_reference: str
    area: AreaSelection
    difference_m2: Decimal | None
    area_provenance: tuple[Provenance, Provenance]
    building_coverage: Constraint
    floor_area_ratio: Constraint | FarStackConstraint
    height: Constraint | HeightStackConstraint
    schema_version: str = "0.1"

    @property
    def review_required(self) -> bool:
        return (any(item.review_required for item in self.area_provenance)
                or any(item.review_required for item in
                       (self.building_coverage, self.floor_area_ratio, self.height)))

    def to_dict(self) -> dict:
        return {"schemaVersion": self.schema_version,
                "inputReferences": {"project": self.project_reference, "geometry": self.geometry_reference},
                "areaBasis": {"selectedBasis": self.area.selected_basis,
                              "declaredAreaM2": self.area.declared_area_m2,
                              "geometryAreaM2": self.area.geometry_area_m2,
                              "differenceM2": self.difference_m2, "basisAreaM2": self.area.basis_area_m2,
                              "provenance": [item.to_dict() for item in self.area_provenance]},
                "constraints": {"buildingCoverage": self.building_coverage.to_dict("maxFootprintAreaM2"),
                                "floorAreaRatio": self.floor_area_ratio.to_dict("maxTotalFloorAreaM2"),
                                "height": self.height.to_dict("maxHeightM")},
                "reviewRequired": self.review_required}
