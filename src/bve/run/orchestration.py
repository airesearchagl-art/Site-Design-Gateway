"""One explicit local pipeline, verified staging, then exclusive publication."""
from pathlib import Path
import tempfile

from bve.constraints import compute_constraints, load_constraint_result, load_project
from bve.constraints.export import project_bytes, result_bytes
from bve.geometry import load_normalized_geometry, read_dxf, read_geojson
from bve.geometry.export import json_bytes, normalized_feature
from bve.geometry.geojson import MAX_INPUT_BYTES as GEOMETRY_LIMIT
from bve.search import search_massing_candidates
from bve.search.export import search_bytes
from bve.validation import MAX_INPUT_BYTES as PROJECT_LIMIT

from .errors import Code, RunError, Stage, at_stage
from .filesystem import publish_new, read_regular, require_absent, write_new
from .manifest import manifest_bytes
from .model import ARTIFACTS, RunSummary, package_version_for_project
from .verification import verify_package


def create_package(*, project: Path, geometry: Path, format: str, area_basis: str,
                   floor_heights_m, output: Path, layer: str | None = None,
                   unit: str | None = None) -> RunSummary:
    with at_stage(Stage.ARGUMENTS):
        if format not in ("geojson", "dxf") or (format == "geojson" and (layer is not None or unit is not None)):
            raise RunError(Stage.ARGUMENTS, Code.INVALID_ARGUMENTS)
        output = Path(output).absolute()
        require_absent(output)
        # The existing parent is required; never create a caller's directory tree.
        parent = output.parent.resolve(strict=True)
        if not parent.is_dir():
            raise RunError(Stage.WRITE, Code.IO_ERROR)
        output = parent / output.name
    with at_stage(Stage.PROJECT):
        raw_project = project_bytes(read_regular(Path(project), PROJECT_LIMIT, Stage.PROJECT))
        validated_project = load_project(raw_project)
        package_version = package_version_for_project(validated_project.schema_version)
    with at_stage(Stage.GEOMETRY):
        raw_geometry = read_regular(Path(geometry), GEOMETRY_LIMIT, Stage.GEOMETRY)
        site = (read_geojson(raw_geometry) if format == "geojson" else
                read_dxf(raw_geometry, layer=layer, unit_override=unit))
        normalized = json_bytes(normalized_feature(site))
        # All downstream references bind the packaged normalized bytes.
        site = load_normalized_geometry(normalized)
    with at_stage(Stage.CONSTRAINTS):
        caps = result_bytes(compute_constraints(validated_project, site, area_basis=area_basis))
        validated_caps = load_constraint_result(caps, project=validated_project if validated_project.schema_version == "0.3" else None)
    with at_stage(Stage.SEARCH):
        result = search_massing_candidates(site, validated_caps, floor_heights_m=floor_heights_m)
        search = search_bytes(result)
    artifacts = {"project": raw_project, "geometry": normalized, "constraints": caps, "search": search}
    with at_stage(Stage.MANIFEST):
        manifest = manifest_bytes(area_basis, result.floor_heights_m, artifacts, package_version=package_version)
    with at_stage(Stage.WRITE):
        staging = tempfile.TemporaryDirectory(prefix=".sdg-run-", dir=parent)
    try:
        temporary = Path(staging.name)
        with at_stage(Stage.WRITE):
            for kind, name in ARTIFACTS.items():
                write_new(temporary / name, artifacts[kind])
            write_new(temporary / "manifest.json", manifest)
        summary = verify_package(temporary)
        with at_stage(Stage.PUBLISH):
            publish_new(temporary, output)
        return summary
    finally:
        with at_stage(Stage.CLEANUP):
            staging.cleanup()
