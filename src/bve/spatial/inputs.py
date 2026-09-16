"""Reuse Geometry readers, limits and metric validation without repair."""
from bve._json import decode_json
from bve._schemas import schema_validator
from bve.constraints.export import canonical_json_bytes
from bve.geometry import SiteGeometry, load_normalized_geometry, read_dxf, read_geojson
from bve.geometry.geojson import MAX_INPUT_BYTES

from .errors import Code, SpatialError
from .model import ValidatedBuildableArea, buildable_bytes


def read_buildable_area(payload: bytes | str, *, format: str, site, project,
                       layer: str | None = None, unit: str | None = None) -> ValidatedBuildableArea:
    if format not in ("geojson", "dxf") or (format == "geojson" and (layer is not None or unit is not None)):
        raise SpatialError(Code.INVALID_ARGUMENTS)
    geometry = (read_geojson(payload, require_source_status=True) if format == "geojson" else
                read_dxf(payload, layer=layer, unit_override=unit))
    return ValidatedBuildableArea(geometry, site=site, project=project)


def load_buildable_area(payload: bytes | str, *, site, project) -> ValidatedBuildableArea:
    from bve.constraints import ValidatedProject
    from bve._json import JSONInputError
    from bve.geometry import Code as GeometryCode, GeometryError

    if type(site) is not SiteGeometry or type(project) is not ValidatedProject or project.schema_version != "0.4":
        raise SpatialError(Code.INVALID_ARGUMENTS)
    try:
        raw, data = decode_json(payload, max_bytes=MAX_INPUT_BYTES)
    except JSONInputError as error:
        raise GeometryError(GeometryCode(str(error))) from None
    if not schema_validator("buildable").is_valid(data):
        raise SpatialError(Code.BUILDABLE_AREA_SCHEMA_INVALID)
    props = data["properties"]
    if props["siteReference"] != site.source_reference:
        raise SpatialError(Code.BUILDABLE_AREA_SITE_REFERENCE_MISMATCH)
    # Project the shared normalized Geometry contract into its existing reader.
    site_data = {**data, "properties": {k:v for k,v in props.items() if k not in ("role", "siteReference")}}
    validated = load_normalized_geometry(canonical_json_bytes(site_data))
    geometry = SiteGeometry(validated.polygon, validated.source_format, validated.source_unit,
                            validated.source_status, props["sourceReference"], validated.warnings)
    result = ValidatedBuildableArea(geometry, site=site, project=project)
    if buildable_bytes(result) != raw:
        raise SpatialError(Code.NONCANONICAL_BUILDABLE_AREA)
    return result
