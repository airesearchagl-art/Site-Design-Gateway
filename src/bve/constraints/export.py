"""Stable decimal JSON numbers and exclusive, explicit local output."""
from decimal import Decimal, DecimalException
import json
from pathlib import Path

from bve._schemas import schema_validator

from .errors import Code, ConstraintError
from .model import ConstraintResult


def _encode(value) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is Decimal:
        if not value.is_finite():
            raise ConstraintError(Code.NUMERIC_RANGE)
        if value == 0:
            return "0"
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    if type(value) is int:
        return str(value)
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if type(value) is list:
        return "[" + ",".join(_encode(item) for item in value) + "]"
    if type(value) is dict and all(type(key) is str for key in value):
        return "{" + ",".join(_encode(key) + ":" + _encode(value[key]) for key in sorted(value)) + "}"
    raise ConstraintError(Code.INTERNAL_ERROR)


def canonical_json_bytes(value) -> bytes:
    """Public access to the existing Decimal encoder; no alternate numeric format."""
    return (_encode(value) + "\n").encode("utf-8")


def project_bytes(payload: bytes | str) -> bytes:
    """Validate and canonicalize a complete Project without stripping its fields.

    Consumers must bind references to these returned bytes, not the original
    input formatting. The same bounded Project reader validates both forms.
    """
    from bve._json import decode_json
    from bve.validation import MAX_INPUT_BYTES
    from .inputs import load_project

    load_project(payload)
    _, data = decode_json(payload, max_bytes=MAX_INPUT_BYTES)
    canonical = canonical_json_bytes(data)
    load_project(canonical)
    return canonical


def result_bytes(result: ConstraintResult) -> bytes:
    if type(result) is not ConstraintResult:
        raise ConstraintError(Code.INVALID_ARGUMENTS)
    data = result.to_dict()
    if result.schema_version not in ("0.1", "0.2", "0.3", "0.4"):
        raise ConstraintError(Code.OUTPUT_SCHEMA_INVALID)
    try:
        validator = schema_validator({"0.1":"constraints", "0.2":"constraints_v2", "0.3":"constraints_v3", "0.4":"constraints_v4"}[result.schema_version])
    except Exception:
        raise ConstraintError(Code.SCHEMA_UNAVAILABLE) from None
    try:
        if not validator.is_valid(data):
            raise ConstraintError(Code.OUTPUT_SCHEMA_INVALID)
    except DecimalException:
        raise ConstraintError(Code.NUMERIC_RANGE) from None
    return canonical_json_bytes(data)


def constraint_summary(result: ConstraintResult) -> dict:
    states = [item.state for item in (result.building_coverage, result.floor_area_ratio, result.height)]
    return {"reviewRequired": result.review_required, "computed": states.count("COMPUTED"),
            "unavailable": states.count("UNAVAILABLE"), "absent": states.count("ABSENT")}


def write_output(result: ConstraintResult, output: Path) -> None:
    data = result_bytes(result)
    try:
        path = Path(output)
        if path.exists() or path.is_symlink():
            raise ConstraintError(Code.OUTPUT_EXISTS)
        if not path.parent.is_dir():
            raise ConstraintError(Code.IO_ERROR)
        with path.open("xb") as target:
            target.write(data)
    except ConstraintError:
        raise
    except FileExistsError:
        raise ConstraintError(Code.OUTPUT_EXISTS) from None
    except (OSError, ValueError):
        raise ConstraintError(Code.IO_ERROR) from None
