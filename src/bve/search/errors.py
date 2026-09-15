"""Fixed search failures, without raw input diagnostics."""
from enum import StrEnum


class Code(StrEnum):
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    SEARCH_SPACE_REQUIRED = "SEARCH_SPACE_REQUIRED"
    SEARCH_SPACE_TOO_LARGE = "SEARCH_SPACE_TOO_LARGE"
    DUPLICATE_SEARCH_VALUE = "DUPLICATE_SEARCH_VALUE"
    DUPLICATE_CANDIDATE = "DUPLICATE_CANDIDATE"
    OUTPUT_SEMANTIC_INVALID = "OUTPUT_SEMANTIC_INVALID"
    OUTPUT_SCHEMA_INVALID = "OUTPUT_SCHEMA_INVALID"
    SCHEMA_UNAVAILABLE = "SCHEMA_UNAVAILABLE"
    OUTPUT_EXISTS = "OUTPUT_EXISTS"
    IO_ERROR = "IO_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class SearchError(ValueError):
    def __init__(self, code: Code):
        self.code = Code(code)
        super().__init__(self.code.value)
