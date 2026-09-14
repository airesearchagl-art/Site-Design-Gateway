"""Fixed, non-disclosing constraint boundary failures."""
from enum import StrEnum


class Code(StrEnum):
    INVALID_JSON = "INVALID_JSON"
    INPUT_TOO_LARGE = "INPUT_TOO_LARGE"
    NUMERIC_RANGE = "NUMERIC_RANGE"
    PROJECT_SCHEMA_INVALID = "PROJECT_SCHEMA_INVALID"
    SCHEMA_UNAVAILABLE = "SCHEMA_UNAVAILABLE"
    AREA_BASIS_REQUIRED = "AREA_BASIS_REQUIRED"
    INVALID_AREA_BASIS = "INVALID_AREA_BASIS"
    AREA_BASIS_UNAVAILABLE = "AREA_BASIS_UNAVAILABLE"
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    OUTPUT_EXISTS = "OUTPUT_EXISTS"
    IO_ERROR = "IO_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ConstraintError(ValueError):
    def __init__(self, code: Code):
        self.code = Code(code)
        super().__init__(self.code.value)
