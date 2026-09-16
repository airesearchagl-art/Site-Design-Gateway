"""Recompute exported constraints from provenance before trusting derived data."""
from dataclasses import dataclass
from decimal import DecimalException
from hashlib import sha256

from bve._json import JSONInputError, decode_json
from bve._schemas import schema_validator

from .engine import _compute_result
from .errors import Code, ConstraintError
from .export import result_bytes
from .inputs import AdditionalFarCap, AdditionalHeightCap, AreaSelection, Condition, ValidatedProject
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
    additional = ()
    if data["schemaVersion"] == "0.1":
        far = Condition(**constraints["floorAreaRatio"]["provenance"][1]["condition"])
    else:
        stack = constraints["floorAreaRatio"]["capStack"]
        ids = [entry["id"] for entry in stack]
        if len(ids) != len(set(ids)):
            raise ConstraintError(Code.CONSTRAINT_SEMANTIC_MISMATCH)
        far = Condition(**stack[0]["condition"])
        additional = tuple(AdditionalFarCap(entry["id"], entry["kind"], Condition(**entry["condition"]))
                           for entry in stack[1:])
    additional_height = ()
    if data["schemaVersion"] == "0.3":
        stack = constraints["height"]["capStack"]
        ids = [entry["id"] for entry in stack]
        if len(ids) != len(set(ids)):
            raise ConstraintError(Code.CONSTRAINT_SEMANTIC_MISMATCH)
        has_base = bool(stack) and stack[0]["id"] == "base-height"
        height = Condition(**stack[0]["condition"]) if has_base else None
        additional_height = tuple(AdditionalHeightCap(entry["id"], entry["kind"], Condition(**entry["condition"]))
                                  for entry in stack[1 if has_base else 0:])
    else:
        height_source = constraints["height"]["provenance"]
        height = Condition(**height_source[0]["condition"]) if height_source else None
    return _compute_result(refs["project"], refs["geometry"], selection,
                           declared, actual, coverage, far, height,
                           schema_version=data["schemaVersion"], additional_caps=additional, additional_height_caps=additional_height)


@dataclass(frozen=True, init=False)
class ValidatedConstraintResult:
    result: ConstraintResult
    reference: str

    def __init__(self, payload: bytes | str, *, project: ValidatedProject | None = None):
        try:
            _, data = decode_json(payload, max_bytes=MAX_RESULT_BYTES,
                                  max_digits=MAX_RESULT_DIGITS, max_exponent=MAX_RESULT_EXPONENT)
        except JSONInputError as error:
            raise ConstraintError(Code(str(error))) from None
        version = data.get("schemaVersion") if type(data) is dict else None
        if version not in ("0.1", "0.2", "0.3"):
            raise ConstraintError(Code.CONSTRAINT_SCHEMA_INVALID)
        try:
            validator = schema_validator({"0.1":"constraints", "0.2":"constraints_v2", "0.3":"constraints_v3"}[version])
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
            if project is not None:
                _check_project_binding(data, expected, project)
            canonical = result_bytes(expected)
        except DecimalException:
            raise ConstraintError(Code.NUMERIC_RANGE) from None
        object.__setattr__(self, "result", expected)
        object.__setattr__(self, "reference", "sha256:" + sha256(canonical).hexdigest())


def _check_project_binding(data: dict, expected: ConstraintResult, project: ValidatedProject) -> None:
    """Bind provenance to a caller-supplied original Project, not self-declared metadata."""
    if (type(project) is not ValidatedProject or project.schema_version != expected.schema_version
            or project.reference != expected.project_reference):
        raise ConstraintError(Code.CONSTRAINT_SEMANTIC_MISMATCH)
    actual = expected.area_provenance[1].condition
    selected = project.area if expected.area.selected_basis == "declared_project_area" else actual
    if selected.value is None:
        raise ConstraintError(Code.CONSTRAINT_SEMANTIC_MISMATCH)
    selection = AreaSelection(expected.area.selected_basis, project.area.value, actual.value, selected.value)
    bound = _compute_result(project.reference, expected.geometry_reference, selection, project.area, actual,
                            project.coverage, project.far, project.height, schema_version=project.schema_version,
                            additional_caps=project.additional_far_caps, additional_height_caps=project.additional_height_caps)
    if bound.to_dict() != data:
        raise ConstraintError(Code.CONSTRAINT_SEMANTIC_MISMATCH)


def load_constraint_result(payload: bytes | str, *, project: ValidatedProject | None = None) -> ValidatedConstraintResult:
    """Check internal consistency; optionally also bind every source to the original Project.

    Without Project, self-consistent changes to source metadata cannot be authenticated.
    Run Package v0.3 always supplies its validated Project.
    """
    return ValidatedConstraintResult(payload, project=project)
