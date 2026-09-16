"""Explicit scalar caps only; no spatial plane or legal rule interpretation."""
from .inputs import AdditionalHeightCap, Condition
from .model import HeightCapEntry, HeightStackConstraint, Provenance


def compute_height_stack(reference: str, base: Condition | None,
                         additional: tuple[AdditionalHeightCap, ...]) -> HeightStackConstraint:
    stack = (() if base is None else
             (HeightCapEntry("base-height", "base_height", Provenance("zoning.heightLimit", reference, base)),)) + tuple(
        HeightCapEntry(cap.id, cap.kind, Provenance("zoning.additionalHeightCaps", reference, cap.condition))
        for cap in additional)
    if not stack:
        return HeightStackConstraint("ABSENT", None, (), ())
    if any(entry.provenance.condition.value is None for entry in stack):
        return HeightStackConstraint("UNAVAILABLE", None, (), stack)
    effective = min(entry.provenance.condition.value for entry in stack)
    ids = tuple(entry.id for entry in stack if entry.provenance.condition.value == effective)
    return HeightStackConstraint("COMPUTED", effective, ids, stack)
