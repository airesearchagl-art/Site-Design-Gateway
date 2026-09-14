"""Consume the Phase 1 output contract; recompute, never trust its metrics."""
from decimal import Decimal
from hashlib import sha256

from bve._json import JSONInputError, decode_json
from bve._schemas import schema_validator

from .errors import Code, GeometryError
from .geojson import MAX_INPUT_BYTES
from .model import SiteGeometry
from .normalization import normalized_polygon


def load_normalized_geometry(payload: bytes | str) -> SiteGeometry:
    try:
        raw, data = decode_json(payload, max_bytes=MAX_INPUT_BYTES)
    except JSONInputError as error:
        raise GeometryError(Code(str(error))) from None
    try:
        validator = schema_validator("geometry")
    except Exception:
        raise GeometryError(Code.SCHEMA_UNAVAILABLE) from None
    if not validator.is_valid(data):
        raise GeometryError(Code.NORMALIZED_SCHEMA_INVALID)
    properties = data["properties"]
    # Preserve encoded ring order when comparing the producer's float metrics.
    # Validation and all unit/coordinate rules remain in the Geometry package.
    polygon = normalized_polygon(data["geometry"]["coordinates"], "m", canonical=False)
    site = SiteGeometry(polygon, properties["sourceFormat"], properties["sourceUnit"],
                        properties["sourceStatus"], "sha256:" + sha256(raw).hexdigest(),
                        tuple(properties["warnings"]))
    if (properties["areaM2"] != Decimal(str(site.area_m2))
            or properties["bounds"] != [Decimal(str(value)) for value in site.bounds]):
        raise GeometryError(Code.METADATA_MISMATCH)
    return site
