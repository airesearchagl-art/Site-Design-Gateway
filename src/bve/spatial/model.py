"""Immutable supplied domain, bound to the packaged site and original Project."""
from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Literal

from bve._json import decode_json
from bve.constraints import ValidatedProject
from bve.geometry import SiteGeometry
from bve.geometry.export import json_bytes, normalized_feature
from bve.geometry.geojson import MAX_INPUT_BYTES
from bve.geometry.normalization import canonical_polygon, MAX_POSITIONS

from .errors import Code, SpatialError

SPATIAL_REVIEW_STATUSES = frozenset(("llm_researched", "assumed", "unknown", "review_required"))


def require_supported_buildable(polygon) -> None:
    # Convex hull is used only as a predicate; it never replaces the input.
    if (polygon.interiors or not polygon.equals(polygon.convex_hull)
            or len(polygon.exterior.coords) > MAX_POSITIONS):
        raise SpatialError(Code.UNSUPPORTED_BUILDABLE_AREA_GEOMETRY)


@dataclass(frozen=True, init=False)
class ValidatedBuildableArea:
    geometry: SiteGeometry = field(repr=False)
    site_reference: str
    project_reference: str
    role: Literal["explicit_buildable_area"] = field(default="explicit_buildable_area", init=False)

    def __init__(self, geometry: SiteGeometry, *, site: SiteGeometry, project: ValidatedProject):
        if (type(geometry) is not SiteGeometry or type(site) is not SiteGeometry
                or type(project) is not ValidatedProject or project.schema_version != "0.4"):
            raise SpatialError(Code.INVALID_ARGUMENTS)
        geometry.__post_init__()
        site.__post_init__()
        require_supported_buildable(geometry.polygon)
        if not site.polygon.covers(geometry.polygon):
            raise SpatialError(Code.BUILDABLE_AREA_OUTSIDE_SITE)
        if project.buildable_area_status != geometry.source_status:
            raise SpatialError(Code.BUILDABLE_AREA_STATUS_MISMATCH)
        normalized = SiteGeometry(canonical_polygon(geometry.polygon), geometry.source_format,
                                  geometry.source_unit, geometry.source_status, geometry.source_reference,
                                  geometry.warnings)
        object.__setattr__(self, "geometry", normalized)
        object.__setattr__(self, "site_reference", site.source_reference)
        object.__setattr__(self, "project_reference", project.reference)

    @property
    def polygon(self):
        return self.geometry.polygon

    @property
    def area_m2(self):
        return self.geometry.area_m2

    @property
    def source_status(self):
        return self.geometry.source_status

    @property
    def source_reference(self):
        return self.geometry.source_reference

    @property
    def review_required(self) -> bool:
        return self.source_status in SPATIAL_REVIEW_STATUSES

    def to_dict(self) -> dict:
        data = normalized_feature(self.geometry)
        data["properties"].update(role=self.role, siteReference=self.site_reference)
        return data

    @property
    def reference(self) -> str:
        return "sha256:" + sha256(buildable_bytes(self)).hexdigest()

    def spatial_context(self) -> dict:
        # Decode the canonical producer bytes for exact Decimal JSON values.
        _, data = decode_json(buildable_bytes(self), max_bytes=MAX_INPUT_BYTES)
        props = data["properties"]
        return {"buildableArea": {
            **{key: props[key] for key in ("role", "siteReference", "sourceReference", "sourceStatus", "areaM2")},
            "artifactReference": self.reference, "reviewRequired": self.review_required,
            "geometry": data["geometry"]}}

    def validate_binding(self, site: SiteGeometry, project_reference: str) -> None:
        self.geometry.__post_init__()
        require_supported_buildable(self.polygon)
        if self.site_reference != site.source_reference:
            raise SpatialError(Code.BUILDABLE_AREA_SITE_REFERENCE_MISMATCH)
        if self.project_reference != project_reference:
            raise SpatialError(Code.BUILDABLE_AREA_PROJECT_REFERENCE_MISMATCH)
        if not site.polygon.covers(self.polygon):
            raise SpatialError(Code.BUILDABLE_AREA_OUTSIDE_SITE)


def buildable_bytes(buildable: ValidatedBuildableArea) -> bytes:
    if type(buildable) is not ValidatedBuildableArea:
        raise SpatialError(Code.INVALID_ARGUMENTS)
    from bve._schemas import schema_validator

    buildable.geometry.__post_init__()
    require_supported_buildable(buildable.polygon)
    raw = json_bytes(buildable.to_dict())
    data = json.loads(raw)
    if not schema_validator("buildable").is_valid(data):
        raise SpatialError(Code.BUILDABLE_AREA_SCHEMA_INVALID)
    return raw
