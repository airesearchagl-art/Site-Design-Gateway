"""Recompute exported constraints from provenance before trusting derived data."""
from dataclasses import dataclass
from decimal import DecimalException
from hashlib import sha256

from bve._json import JSONInputError, decode_json
from bve._schemas import schema_validator

from .engine import _compute_result
from .errors import Code, ConstraintError
from .export import result_bytes
from .inputs import AreaSelection, Condition
from .model import ConstraintResult

MAX_RESULT_BYTES = 4 * 1024 * 1024
# Derived products/differences and fixed-point serialization may exceed the
# original Project lexical limits. Keep a separate bounded output-reader budget.
MAX_RESULT_DIGITS = 8192
MAX_RESULT_EXPONENT = 8192


def _recompute(data: dict) -> ConstraintResult:
    refs, area, constraints = data["inputReferences"], data["areaBasis"], data["constraints"]
    declared, actual = [Condition(**item["condition"]) for item in area["provenance"]]
    selected = declared if area["selectedBasis"] == "declared_project_area" else actual
    if selected.value is None:
        raise ConstraintError(Code.CONSTRAINT_SEMANTIC_MISMATCH)
    selection = AreaSelection(area["selectedBasis"], declared.value, actual.value, selected.value)
    coverage = Condition(**constraints["buildingCoverage"]["provenance"][1]["condition"])
    far = Condition(**constraints["floorAreaRatio"]["provenance"][1]["condition"])
    height_source = constraints["height"]["provenance"]
    height = Condition(**height_source[0]["condition"]) if height_source else None
    return _compute_result(refs["project"], refs["geometry"], selection,
                           declared, actual, coverage, far, height)


@dataclass(frozen=True, init=False)
class ValidatedConstraintResult:
    result: ConstraintResult
    reference: str

    def __init__(self, payload: bytes | str):
        try:
            _, data = decode_json(payload, max_bytes=MAX_RESULT_BYTES,
                                  max_digits=MAX_RESULT_DIGITS, max_exponent=MAX_RESULT_EXPONENT)
        except JSONInputError as error:
            raise ConstraintError(Code(str(error))) from None
        try:
            validator = schema_validator("constraints")
        except Exception:
            raise ConstraintError(Code.SCHEMA_UNAVAILABLE) from None
        try:
            if not validator.is_valid(data):
                raise ConstraintError(Code.CONSTRAINT_SCHEMA_INVALID)
            expected = _recompute(data)
            # Includes refs, selected/unselected areas, signed difference, all
            # conditions/units/statuses, fixed IDs, states, values and review.
            if expected.to_dict() != data:
                raise ConstraintError(Code.CONSTRAINT_SEMANTIC_MISMATCH)
            canonical = result_bytes(expected)
        except DecimalException:
            raise ConstraintError(Code.NUMERIC_RANGE) from None
        object.__setattr__(self, "result", expected)
        object.__setattr__(self, "reference", "sha256:" + sha256(canonical).hexdigest())


def load_constraint_result(payload: bytes | str) -> ValidatedConstraintResult:
    return ValidatedConstraintResult(payload)
