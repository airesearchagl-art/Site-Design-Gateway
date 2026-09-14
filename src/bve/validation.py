"""Validation only; source/editable installs read the repository's sole schema.

Results never contain input values, property names, file paths, or raw exceptions.
No input is modified and declared provenance is never promoted.
"""

from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
from typing import Literal

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

MAX_INPUT_BYTES = 256 * 1024
MAX_DEPTH = 32
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "sdg-project-v0.1.schema.json"

ResultCode = Literal[
    "valid", "invalid_json", "input_too_large", "schema_invalid", "schema_unavailable"
]


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    error_count: int
    code: ResultCode


def _failure(code: ResultCode) -> ValidationResult:
    return ValidationResult(False, 1, code)


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _check_json_tree(project: object) -> None:
    """Bound depth, reject non-JSON Python values, cycles and numeric overflow."""
    pending = [(project, 0)]
    visited = 0
    while pending:
        value, depth = pending.pop()
        visited += 1
        if visited > MAX_INPUT_BYTES:
            raise ValueError
        kind = type(value)
        if kind in (dict, list):
            if depth >= MAX_DEPTH:
                raise ValueError
            if kind is dict:
                if any(type(key) is not str for key in value):
                    raise ValueError
                children = value.values()
            else:
                children = value
            pending.extend((child, depth + 1) for child in children)
        elif kind in (int, float):
            if not math.isfinite(value):
                raise ValueError
        elif kind not in (str, bool, type(None)):
            raise ValueError


def validate_project(project: object) -> ValidationResult:
    """Validate a JSON-compatible Python value without changing it.

    PASS means schema conformity only, not regulatory approval or provenance truth.
    Phase 0 supports a source checkout with editable installation, not wheel use.
    """
    try:
        _check_json_tree(project)
        serialized = json.dumps(project, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > MAX_INPUT_BYTES:
            return _failure("input_too_large")
    except (ValueError, TypeError, OverflowError, RecursionError):
        return _failure("invalid_json")

    try:
        validator = _validator()
    except (OSError, ValueError, SchemaError):
        return _failure("schema_unavailable")
    count = sum(1 for _ in validator.iter_errors(project))
    return ValidationResult(count == 0, count, "schema_invalid" if count else "valid")


def _reject_constant(_: str) -> None:
    raise ValueError


def _check_text_depth(text: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise ValueError
        elif character in "]}":
            depth -= 1


def validate_json(text: str | bytes) -> ValidationResult:
    """Parse a bounded UTF-8 JSON document and validate the shared schema."""
    if type(text) not in (str, bytes):
        return _failure("invalid_json")
    try:
        payload = text.encode("utf-8") if type(text) is str else text
        if len(payload) > MAX_INPUT_BYTES:
            return _failure("input_too_large")
        decoded = payload.decode("utf-8")
        _check_text_depth(decoded)
        project = json.loads(decoded, parse_constant=_reject_constant)
    except (ValueError, RecursionError):
        return _failure("invalid_json")
    return validate_project(project)
