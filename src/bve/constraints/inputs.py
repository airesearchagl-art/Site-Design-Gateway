"""Validated, immutable inputs stripped of names and arbitrary metadata."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256

from bve._json import JSONInputError, decode_json
from bve._schemas import schema_validator
from bve.geometry import SiteGeometry
from bve.geometry.model import SourceStatus
from bve.project_semantics import unique_far_cap_ids, unique_height_cap_ids
from bve.validation import MAX_INPUT_BYTES

from .errors import Code, ConstraintError


@dataclass(frozen=True)
class Condition:
    value: Decimal | None
    unit: str
    status: SourceStatus

    def to_dict(self) -> dict:
        return {"value": self.value, "unit": self.unit, "status": self.status}


@dataclass(frozen=True)
class AdditionalFarCap:
    id: str
    kind: str
    condition: Condition


@dataclass(frozen=True)
class AdditionalHeightCap:
    id: str
    kind: str
    condition: Condition


@dataclass(frozen=True, init=False)
class ValidatedProject:
    area: Condition
    coverage: Condition
    far: Condition
    height: Condition | None
    reference: str
    schema_version: str
    additional_far_caps: tuple[AdditionalFarCap, ...]
    additional_height_caps: tuple[AdditionalHeightCap, ...]
    buildable_area_status: SourceStatus | None

    def __init__(self, payload: bytes | str):
        try:
            raw, data = decode_json(payload, max_bytes=MAX_INPUT_BYTES)
        except JSONInputError as error:
            raise ConstraintError(Code(str(error))) from None
        version = data.get("schemaVersion") if type(data) is dict else None
        if version not in ("0.1", "0.2", "0.3", "0.4"):
            raise ConstraintError(Code.PROJECT_SCHEMA_INVALID)
        try:
            validator = schema_validator({"0.1":"project", "0.2":"project_v2", "0.3":"project_v3", "0.4":"project_v4"}[version])
        except Exception:
            raise ConstraintError(Code.SCHEMA_UNAVAILABLE) from None
        if not validator.is_valid(data):
            raise ConstraintError(Code.PROJECT_SCHEMA_INVALID)
        if not unique_far_cap_ids(data):
            raise ConstraintError(Code.DUPLICATE_CAP_ID)
        if not unique_height_cap_ids(data):
            raise ConstraintError(Code.DUPLICATE_HEIGHT_CAP_ID)
        zoning = data["zoning"]
        object.__setattr__(self, "area", Condition(**data["site"]["area"]))
        object.__setattr__(self, "coverage", Condition(**zoning["buildingCoverageRatio"]))
        object.__setattr__(self, "far", Condition(**zoning["floorAreaRatio"]))
        object.__setattr__(self, "height", Condition(**zoning["heightLimit"]) if "heightLimit" in zoning else None)
        additional = ()
        if version in ("0.2", "0.3", "0.4"):
            from .export import canonical_json_bytes
            raw = canonical_json_bytes(data)
            additional = tuple(AdditionalFarCap(entry["id"], entry["kind"],
                               Condition(entry["value"], entry["unit"], entry["status"]))
                               for entry in zoning["additionalFloorAreaRatioCaps"])
        additional_height = tuple(AdditionalHeightCap(entry["id"], entry["kind"],
                                  Condition(entry["value"], entry["unit"], entry["status"]))
                                  for entry in zoning["additionalHeightCaps"]) if version in ("0.3", "0.4") else ()
        object.__setattr__(self, "additional_height_caps", additional_height)
        object.__setattr__(self, "buildable_area_status", data["spatialConstraints"]["buildableArea"]["status"] if version == "0.4" else None)
        object.__setattr__(self, "schema_version", version)
        object.__setattr__(self, "additional_far_caps", additional)
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
