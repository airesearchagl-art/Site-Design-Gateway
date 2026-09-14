"""Validated, immutable inputs stripped of names and arbitrary metadata."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256

from bve._json import JSONInputError, decode_json
from bve._schemas import schema_validator
from bve.geometry import SiteGeometry
from bve.geometry.model import SourceStatus
from bve.validation import MAX_INPUT_BYTES

from .errors import Code, ConstraintError


@dataclass(frozen=True)
class Condition:
    value: Decimal | None
    unit: str
    status: SourceStatus

    def to_dict(self) -> dict:
        return {"value": self.value, "unit": self.unit, "status": self.status}


@dataclass(frozen=True, init=False)
class ValidatedProject:
    area: Condition
    coverage: Condition
    far: Condition
    height: Condition | None
    reference: str

    def __init__(self, payload: bytes | str):
        try:
            raw, data = decode_json(payload, max_bytes=MAX_INPUT_BYTES)
        except JSONInputError as error:
            raise ConstraintError(Code(str(error))) from None
        try:
            validator = schema_validator("project")
        except Exception:
            raise ConstraintError(Code.SCHEMA_UNAVAILABLE) from None
        if not validator.is_valid(data):
            raise ConstraintError(Code.PROJECT_SCHEMA_INVALID)
        zoning = data["zoning"]
        object.__setattr__(self, "area", Condition(**data["site"]["area"]))
        object.__setattr__(self, "coverage", Condition(**zoning["buildingCoverageRatio"]))
        object.__setattr__(self, "far", Condition(**zoning["floorAreaRatio"]))
        object.__setattr__(self, "height", Condition(**zoning["heightLimit"]) if "heightLimit" in zoning else None)
        object.__setattr__(self, "reference", "sha256:" + sha256(raw).hexdigest())


def load_project(payload: bytes | str) -> ValidatedProject:
    return ValidatedProject(payload)


@dataclass(frozen=True)
class AreaSelection:
    selected_basis: str
    declared_area_m2: Decimal | None
    geometry_area_m2: Decimal
    basis_area_m2: Decimal


def select_area(project: ValidatedProject, geometry: SiteGeometry, area_basis: str | None = None) -> AreaSelection:
    if area_basis is None:
        raise ConstraintError(Code.AREA_BASIS_REQUIRED)
    if type(area_basis) is not str or area_basis not in ("declared_project_area", "geometry_area"):
        raise ConstraintError(Code.INVALID_AREA_BASIS)
    if type(project) is not ValidatedProject or type(geometry) is not SiteGeometry:
        raise ConstraintError(Code.INVALID_ARGUMENTS)
    geometry.__post_init__()
    declared = project.area.value
    actual = Decimal(str(geometry.area_m2))
    selected = declared if area_basis == "declared_project_area" else actual
    if selected is None:
        raise ConstraintError(Code.AREA_BASIS_UNAVAILABLE)
    return AreaSelection(area_basis, declared, actual, selected)
