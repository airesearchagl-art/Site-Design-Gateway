"""Stable decimal JSON numbers and exclusive, explicit local output."""
from decimal import Decimal
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


def result_bytes(result: ConstraintResult) -> bytes:
    if type(result) is not ConstraintResult:
        raise ConstraintError(Code.INVALID_ARGUMENTS)
    data = result.to_dict()
    try:
        validator = schema_validator("constraints")
    except Exception:
        raise ConstraintError(Code.SCHEMA_UNAVAILABLE) from None
    if not validator.is_valid(data):
        raise ConstraintError(Code.OUTPUT_SCHEMA_INVALID)
    return (_encode(data) + "\n").encode("utf-8")


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
