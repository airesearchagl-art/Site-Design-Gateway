"""Combine explicit numeric caps only; never infer a legal rule or coefficient."""
from decimal import Decimal

from .arithmetic import floor_area_cap
from .inputs import AdditionalFarCap, Condition
from .model import FarCapEntry, FarStackConstraint, Provenance


def compute_far_stack(basis_area: Decimal, selected: Provenance, reference: str,
                      base: Condition, additional: tuple[AdditionalFarCap, ...]) -> FarStackConstraint:
    stack = (FarCapEntry("base-zoning", "base_zoning", Provenance("zoning.floorAreaRatio", reference, base)),) + tuple(
        FarCapEntry(cap.id, cap.kind, Provenance("zoning.additionalFloorAreaRatioCaps", reference, cap.condition))
        for cap in additional)
    if any(entry.provenance.condition.value is None for entry in stack):
        return FarStackConstraint("UNAVAILABLE", None, None, (), stack, (selected,))
    effective = min(entry.provenance.condition.value for entry in stack)
    ids = tuple(entry.id for entry in stack if entry.provenance.condition.value == effective)
    return FarStackConstraint("COMPUTED", floor_area_cap(basis_area, effective), effective, ids, stack, (selected,))
