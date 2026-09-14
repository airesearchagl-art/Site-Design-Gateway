"""BVE Phase 0: validate inputs against the shared SDG contract."""

from .validation import ValidationResult, validate_json, validate_project

__all__ = ["ValidationResult", "validate_json", "validate_project"]
