"""Verify package bytes through existing Core APIs, never a second compute engine."""
from pathlib import Path
from decimal import Decimal
import json
import stat

from bve._schemas import schema_validator
from bve.constraints import compute_constraints, load_constraint_result, load_project
from bve.constraints.export import canonical_json_bytes, project_bytes, result_bytes
from bve.constraints.reader import MAX_RESULT_BYTES
from bve.geometry import load_normalized_geometry
from bve.geometry.export import json_bytes, normalized_feature
from bve.geometry.geojson import MAX_INPUT_BYTES as GEOMETRY_LIMIT
from bve.search import search_massing_candidates
from bve.search.export import search_bytes
from bve.validation import MAX_INPUT_BYTES as PROJECT_LIMIT

from .errors import Code, RunError, Stage, at_stage
from .filesystem import is_link, read_regular
from .manifest import MAX_MANIFEST_BYTES, decode, reference, validate_manifest
from .model import ARTIFACTS, FILE_SET, RunSummary

MAX_SEARCH_BYTES = 256 * 1024 * 1024
LIMITS = {"project": PROJECT_LIMIT, "geometry": GEOMETRY_LIMIT,
          "constraints": MAX_RESULT_BYTES, "search": MAX_SEARCH_BYTES}


def check_hashes(manifest: dict, artifacts: dict[str, bytes]) -> None:
    for kind, raw in artifacts.items():
        if manifest["artifacts"][kind]["reference"] != reference(raw):
            raise RunError(Stage.VERIFY, Code.HASH_MISMATCH)


def check_references(manifest: dict, constraints: dict, search: dict) -> None:
    refs = {kind: entry["reference"] for kind, entry in manifest["artifacts"].items()}
    if constraints["inputReferences"] != {kind: refs[kind] for kind in ("project", "geometry")}:
        raise RunError(Stage.VERIFY, Code.REFERENCE_MISMATCH)
    if search["inputReferences"] != {kind: refs[kind] for kind in ("project", "geometry", "constraints")}:
        raise RunError(Stage.VERIFY, Code.REFERENCE_MISMATCH)


def verify_package(package: Path) -> RunSummary:
    with at_stage(Stage.VERIFY):
        package = Path(package)
        info = package.lstat()
        if is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise RunError(Stage.VERIFY, Code.NOT_PACKAGE_DIRECTORY)
        if {p.name for p in package.iterdir()} != FILE_SET:
            raise RunError(Stage.VERIFY, Code.FILE_SET_MISMATCH)
        raw_manifest = read_regular(package / "manifest.json", MAX_MANIFEST_BYTES, Stage.VERIFY)
        manifest = decode(raw_manifest, MAX_MANIFEST_BYTES)
        validate_manifest(manifest)
        if canonical_json_bytes(manifest) != raw_manifest:
            raise RunError(Stage.VERIFY, Code.NONCANONICAL_ARTIFACT)
        # Read only constant names; untrusted manifest paths are never traversed.
        artifacts = {kind: read_regular(package / name, LIMITS[kind], Stage.VERIFY)
                     for kind, name in ARTIFACTS.items()}
        check_hashes(manifest, artifacts)
        if project_bytes(artifacts["project"]) != artifacts["project"]:
            raise RunError(Stage.VERIFY, Code.NONCANONICAL_ARTIFACT)
        project = load_project(artifacts["project"])
        site = load_normalized_geometry(artifacts["geometry"])
        geometry_data = decode(artifacts["geometry"], GEOMETRY_LIMIT)
        canonical_geometry = normalized_feature(site)
        # Loader binds site to packaged bytes; the export retains the original
        # input digest as provenance, without requiring the original input file.
        canonical_geometry["properties"]["sourceReference"] = geometry_data["properties"]["sourceReference"]
        if json_bytes(canonical_geometry) != artifacts["geometry"]:
            raise RunError(Stage.VERIFY, Code.NONCANONICAL_ARTIFACT)
        constraints = load_constraint_result(artifacts["constraints"])
        if result_bytes(constraints.result) != artifacts["constraints"]:
            raise RunError(Stage.VERIFY, Code.NONCANONICAL_ARTIFACT)
        search_data = decode(artifacts["search"], MAX_SEARCH_BYTES)
        # The bounded decoder already rejects duplicate keys, invalid Unicode,
        # depth/range excess and nonfinite values. Preserve JSON integer tokens
        # for the schema's rank/count integer types, without rounding decimals.
        del search_data
        search_data = json.loads(artifacts["search"], parse_float=Decimal)
        if not schema_validator("search").is_valid(search_data):
            raise RunError(Stage.VERIFY, Code.ARTIFACT_SCHEMA_INVALID)
        check_references(manifest, constraints.result.to_dict(), search_data)
        config = manifest["configuration"]
        if (config["areaBasis"] != constraints.result.area.selected_basis
                or config["floorHeightsM"] != search_data["search"]["floorHeightsM"]):
            raise RunError(Stage.VERIFY, Code.CONFIGURATION_MISMATCH)
        authoritative = compute_constraints(project, site, area_basis=config["areaBasis"])
        if result_bytes(authoritative) != artifacts["constraints"]:
            raise RunError(Stage.VERIFY, Code.ARTIFACT_SEMANTIC_MISMATCH)
        # No serialized Search loader exists. Replay the public engine and its
        # semantic exporter, including every rejection, then compare exact bytes.
        expected = search_massing_candidates(site, constraints, floor_heights_m=config["floorHeightsM"])
        if search_bytes(expected) != artifacts["search"]:
            raise RunError(Stage.VERIFY, Code.ARTIFACT_SEMANTIC_MISMATCH)
        return RunSummary(expected.review_required, len(expected.floor_heights_m),
                          len(expected.ranked_candidates), len(expected.rejections))
