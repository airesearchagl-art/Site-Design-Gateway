"""Deterministic local outputs. Only explicit output files contain coordinates."""
import json
from pathlib import Path

from shapely.geometry import mapping

from .errors import Code, GeometryError
from .model import SiteGeometry


def geometry_summary(site: SiteGeometry) -> dict:
    return {"areaM2": site.area_m2, "bounds": list(site.bounds), "unit": "m",
            "sourceFormat": site.source_format, "valid": True,
            "sourceUnit": site.source_unit, "sourceStatus": site.source_status,
            "sourceReference": site.source_reference, "warnings": list(site.warnings)}


def normalized_feature(site: SiteGeometry) -> dict:
    properties = geometry_summary(site)
    properties["coordinateSystem"] = "local_xy"
    return {"schemaVersion": "0.1", "type": "Feature",
            "geometry": mapping(site.polygon), "properties": properties}


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def write_outputs(site: SiteGeometry, *, output: Path | None = None,
                  summary: Path | None = None) -> None:
    """Create explicit files exclusively; no overwrites or implicit directory creation.

    Each file is a separate write, not a multi-file transaction. On an OS write
    failure already-created files may remain; callers receive IO_ERROR, never PASS.
    """
    jobs = []
    if output is not None:
        jobs.append((Path(output), json_bytes(normalized_feature(site))))
    if summary is not None:
        jobs.append((Path(summary), json_bytes(geometry_summary(site))))
    try:
        targets = [path.resolve() for path, _ in jobs]
        if len(set(targets)) != len(targets):
            raise GeometryError(Code.INVALID_ARGUMENTS)
        if any(path.exists() or path.is_symlink() for path, _ in jobs):
            raise GeometryError(Code.OUTPUT_EXISTS)
        if any(not path.parent.is_dir() for path, _ in jobs):
            raise GeometryError(Code.IO_ERROR)
        for path, data in jobs:
            with path.open("xb") as target:
                target.write(data)
    except FileExistsError:
        raise GeometryError(Code.OUTPUT_EXISTS) from None
    except (OSError, ValueError) as error:
        if isinstance(error, GeometryError):
            raise
        raise GeometryError(Code.IO_ERROR) from None
