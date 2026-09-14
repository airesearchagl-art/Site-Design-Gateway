"""Bounded decimal JSON input shared by the two Phase 2 input boundaries."""
from decimal import Decimal, DecimalException
import json

from .validation import _check_text_depth

MAX_DIGITS = 1024
MAX_EXPONENT = 1024


class JSONInputError(ValueError):
    """Only fixed codes; no input snippets or parser diagnostics."""


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise JSONInputError("INVALID_JSON")
        result[key] = value
    return result


def _constant(_):
    raise JSONInputError("INVALID_JSON")


def decode_json(payload: bytes | str, *, max_bytes: int) -> tuple[bytes, object]:
    if type(payload) not in (bytes, str):
        raise JSONInputError("INVALID_JSON")
    try:
        raw = payload.encode("utf-8") if type(payload) is str else payload
        if len(raw) > max_bytes:
            raise JSONInputError("INPUT_TOO_LARGE")
        text = raw.decode("utf-8")
        _check_text_depth(text)
        data = json.loads(text, parse_int=Decimal, parse_float=Decimal,
                          parse_constant=_constant, object_pairs_hook=_pairs)
        pending = [data]
        while pending:
            value = pending.pop()
            if type(value) is dict:
                pending.extend(value.values())
                for key in value:
                    key.encode("utf-8")
            elif type(value) is list:
                pending.extend(value)
            elif type(value) is str:
                value.encode("utf-8")
            elif type(value) is Decimal:
                if (not value.is_finite() or len(value.as_tuple().digits) > MAX_DIGITS
                        or abs(value.as_tuple().exponent) > MAX_EXPONENT):
                    raise JSONInputError("NUMERIC_RANGE")
        return raw, data
    except JSONInputError:
        raise
    except DecimalException:
        raise JSONInputError("NUMERIC_RANGE") from None
    except (ValueError, RecursionError, OverflowError):
        raise JSONInputError("INVALID_JSON") from None
