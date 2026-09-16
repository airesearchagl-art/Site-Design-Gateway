"""Canonical manifest generation with a closed schema and no source metadata."""
from hashlib import sha256

from bve._json import JSONInputError, decode_json
from bve._schemas import schema_validator
from bve.constraints.export import canonical_json_bytes
from bve.constraints.reader import MAX_RESULT_DIGITS, MAX_RESULT_EXPONENT
from bve.search.inputs import canonical_heights

from .errors import Code, RunError, Stage
from .model import ARTIFACTS, PACKAGE_VERSION

MAX_MANIFEST_BYTES = 256 * 1024


def reference(raw: bytes) -> str:
    return "sha256:" + sha256(raw).hexdigest()


def decode(payload: bytes, limit: int):
    try:
        return decode_json(payload, max_bytes=limit, max_digits=MAX_RESULT_DIGITS,
                           max_exponent=MAX_RESULT_EXPONENT)[1]
    except JSONInputError as error:
        code = Code.INPUT_TOO_LARGE if str(error) == "INPUT_TOO_LARGE" else Code.INVALID_JSON
        raise RunError(Stage.VERIFY, code) from None


def validate_manifest(data: dict) -> None:
    try:
        validator = schema_validator("run")
    except Exception:
        raise RunError(Stage.MANIFEST, Code.SCHEMA_UNAVAILABLE) from None
    if not validator.is_valid(data):
        raise RunError(Stage.MANIFEST, Code.MANIFEST_SCHEMA_INVALID)
    heights = data["configuration"]["floorHeightsM"]
    if tuple(heights) != canonical_heights(heights):
        raise RunError(Stage.MANIFEST, Code.CONFIGURATION_MISMATCH)


def manifest_bytes(area_basis: str, floor_heights: tuple, artifacts: dict[str, bytes]) -> bytes:
    if set(artifacts) != set(ARTIFACTS):
        raise RunError(Stage.MANIFEST, Code.FILE_SET_MISMATCH)
    data = {"schemaVersion": "0.1", "packageVersion": PACKAGE_VERSION,
            "configuration": {"areaBasis": area_basis, "floorHeightsM": list(floor_heights)},
            "artifacts": {kind: {"path": filename, "reference": reference(artifacts[kind])}
                          for kind, filename in ARTIFACTS.items()}}
    validate_manifest(data)
    raw = canonical_json_bytes(data)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise RunError(Stage.MANIFEST, Code.INPUT_TOO_LARGE)
    return raw
