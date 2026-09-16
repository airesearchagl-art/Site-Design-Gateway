"""Canonical decimal JSON and explicit exclusive local file output."""
from decimal import DecimalException
from pathlib import Path
import warnings

from shapely.errors import GEOSException

from bve._schemas import schema_validator
from bve.constraints.export import _encode

from .engine import _validate_candidate
from .errors import Code, MassingError
from .model import MassingCandidate


def candidate_bytes(candidate: MassingCandidate) -> bytes:
    if type(candidate) is not MassingCandidate:
        raise MassingError(Code.INVALID_ARGUMENTS)
    try:
        validator = schema_validator("massing_v2" if candidate.constraints.result.schema_version == "0.4" else "massing")
    except Exception:
        raise MassingError(Code.SCHEMA_UNAVAILABLE) from None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            _validate_candidate(candidate)
            data = candidate.to_dict()
            if not validator.is_valid(data):
                raise MassingError(Code.OUTPUT_SCHEMA_INVALID)
            return (_encode(data) + "\n").encode("utf-8")
    except DecimalException:
        raise MassingError(Code.NUMERIC_RANGE) from None
    except (GEOSException, RuntimeWarning, OverflowError):
        raise MassingError(Code.GEOMETRY_GENERATION_FAILED) from None


def write_output(candidate: MassingCandidate, output: Path) -> None:
    data = candidate_bytes(candidate)
    try:
        path = Path(output)
        if path.exists() or path.is_symlink():
            raise MassingError(Code.OUTPUT_EXISTS)
        if not path.parent.is_dir():
            raise MassingError(Code.IO_ERROR)
        with path.open("xb") as target:
            target.write(data)
    except MassingError:
        raise
    except FileExistsError:
        raise MassingError(Code.OUTPUT_EXISTS) from None
    except (OSError, ValueError):
        raise MassingError(Code.IO_ERROR) from None
