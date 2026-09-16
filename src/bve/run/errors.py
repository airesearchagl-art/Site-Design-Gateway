"""Stage-tagged fixed codes; never retain paths, payloads or native diagnostics."""
from contextlib import contextmanager
from enum import StrEnum

from bve.constraints import ConstraintError
from bve.geometry import GeometryError
from bve.massing import MassingError
from bve.search import SearchError


class Stage(StrEnum):
    ARGUMENTS = "arguments"
    PROJECT = "project"
    GEOMETRY = "geometry"
    CONSTRAINTS = "constraints"
    SEARCH = "search"
    MANIFEST = "manifest"
    VERIFY = "verify"
    WRITE = "write"
    PUBLISH = "publish"
    CLEANUP = "cleanup"


class Code(StrEnum):
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    OUTPUT_EXISTS = "OUTPUT_EXISTS"
    IO_ERROR = "IO_ERROR"
    INPUT_TOO_LARGE = "INPUT_TOO_LARGE"
    INVALID_JSON = "INVALID_JSON"
    MANIFEST_SCHEMA_INVALID = "MANIFEST_SCHEMA_INVALID"
    ARTIFACT_SCHEMA_INVALID = "ARTIFACT_SCHEMA_INVALID"
    SCHEMA_UNAVAILABLE = "SCHEMA_UNAVAILABLE"
    FILE_SET_MISMATCH = "FILE_SET_MISMATCH"
    NOT_REGULAR_FILE = "NOT_REGULAR_FILE"
    NOT_PACKAGE_DIRECTORY = "NOT_PACKAGE_DIRECTORY"
    HASH_MISMATCH = "HASH_MISMATCH"
    REFERENCE_MISMATCH = "REFERENCE_MISMATCH"
    CONFIGURATION_MISMATCH = "CONFIGURATION_MISMATCH"
    NONCANONICAL_ARTIFACT = "NONCANONICAL_ARTIFACT"
    ARTIFACT_SEMANTIC_MISMATCH = "ARTIFACT_SEMANTIC_MISMATCH"
    ATOMIC_PUBLISH_UNAVAILABLE = "ATOMIC_PUBLISH_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class RunError(ValueError):
    def __init__(self, stage: Stage, code: StrEnum):
        self.stage = Stage(stage)
        # Core enum instances are preserved, including their original meaning.
        self.code = code
        super().__init__(f"stage={self.stage.value} code={self.code.value}")


@contextmanager
def at_stage(stage: Stage):
    try:
        yield
    except RunError:
        raise
    except (GeometryError, ConstraintError, MassingError, SearchError) as error:
        raise RunError(stage, error.code) from None
    except (OSError, ValueError):
        raise RunError(stage, Code.IO_ERROR) from None
    except Exception:
        raise RunError(stage, Code.INTERNAL_ERROR) from None
