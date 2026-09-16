"""Tampered bytes, self-consistent false claims and path mutations fail closed."""
from decimal import Decimal
import json

import pytest

from bve.constraints import compute_constraints, load_constraint_result, load_project
from bve.constraints.export import canonical_json_bytes, result_bytes
from bve.geometry import load_normalized_geometry
from bve.search import search_massing_candidates
from bve.search.export import search_bytes
from bve.run import RunError, verify_package
from bve.run.manifest import reference, validate_manifest
from bve.run.model import ARTIFACTS
from bve.run.verification import check_references


def read(path):
    return json.loads(path.read_bytes(), parse_float=Decimal)


def write(path, value):
    path.write_bytes(canonical_json_bytes(value))


def rehash(package, kind):
    manifest = read(package / "manifest.json")
    manifest["artifacts"][kind]["reference"] = reference((package / ARTIFACTS[kind]).read_bytes())
    write(package / "manifest.json", manifest)


@pytest.mark.parametrize("kind", list(ARTIFACTS))
def test_exact_artifact_byte_tamper_detected(run_package, kind):
    path = run_package / ARTIFACTS[kind]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(RunError, match="code=HASH_MISMATCH$"):
        verify_package(run_package)


@pytest.mark.parametrize("kind", list(ARTIFACTS))
def test_manifest_hash_tamper_detected(run_package, kind):
    manifest = read(run_package / "manifest.json")
    manifest["artifacts"][kind]["reference"] = "sha256:" + "0" * 64
    write(run_package / "manifest.json", manifest)
    with pytest.raises(RunError, match="code=HASH_MISMATCH$"):
        verify_package(run_package)


@pytest.mark.parametrize("name", ["manifest.json", *ARTIFACTS.values()])
def test_missing_file_detected(run_package, name):
    (run_package / name).unlink()
    with pytest.raises(RunError, match="code=FILE_SET_MISMATCH$"):
        verify_package(run_package)


@pytest.mark.parametrize("name", ["unexpected.json", ".DS_Store", "Thumbs.db", "project-copy.json", "report"])
def test_strict_file_set_includes_hidden_metadata(run_package, name):
    (run_package / name).write_bytes(b"extra")
    with pytest.raises(RunError, match="code=FILE_SET_MISMATCH$"):
        verify_package(run_package)


@pytest.mark.parametrize("kind", list(ARTIFACTS))
def test_schema_or_canonical_check_cannot_be_bypassed_by_rehash(run_package, kind):
    path = run_package / ARTIFACTS[kind]
    data = read(path)
    data["unexpected"] = "synthetic"
    write(path, data)
    rehash(run_package, kind)
    with pytest.raises(RunError):
        verify_package(run_package)


@pytest.mark.parametrize("kind", ["project", "geometry", "constraints", "search"])
def test_noncanonical_whitespace_rehash_still_fails(run_package, kind):
    path = run_package / ARTIFACTS[kind]
    path.write_bytes(path.read_bytes() + b"\n")
    rehash(run_package, kind)
    with pytest.raises(RunError):
        verify_package(run_package)


@pytest.mark.parametrize("which,key", [("constraints", "project"), ("constraints", "geometry"),
                                       ("search", "project"), ("search", "geometry"), ("search", "constraints")])
def test_reference_guard_independently(run_package, which, key):
    manifest = read(run_package / "manifest.json")
    constraints = read(run_package / "constraints.json")
    search = read(run_package / "search-result.json")
    data = constraints if which == "constraints" else search
    data["inputReferences"][key] = "sha256:" + "0" * 64
    with pytest.raises(RunError, match="code=REFERENCE_MISMATCH$"):
        check_references(manifest, constraints, search)


def test_valid_but_different_project_is_not_bound_by_rehash_alone(run_package):
    path = run_package / "project.json"
    data = read(path)
    data["zoning"]["floorAreaRatio"]["value"] = 500
    write(path, data)
    rehash(run_package, "project")
    with pytest.raises(RunError, match="code=REFERENCE_MISMATCH$"):
        verify_package(run_package)


def test_forged_coherent_constraints_still_bound_to_packaged_project(run_package):
    # Hashes, provenance, candidate generation and reference links all agree;
    # only replay from the actual packaged Project exposes the false condition.
    project = read(run_package / "project.json")
    project["zoning"]["floorAreaRatio"]["value"] = 500
    other = load_project(canonical_json_bytes(project))
    original_reference = reference((run_package / "project.json").read_bytes())
    object.__setattr__(other, "reference", original_reference)
    site = load_normalized_geometry((run_package / "site.geojson").read_bytes())
    caps = result_bytes(compute_constraints(other, site, area_basis="declared_project_area"))
    (run_package / "constraints.json").write_bytes(caps)
    search = search_massing_candidates(site, load_constraint_result(caps), floor_heights_m=[4, 5, 6, 7, 8])
    (run_package / "search-result.json").write_bytes(search_bytes(search))
    rehash(run_package, "constraints")
    rehash(run_package, "search")
    with pytest.raises(RunError, match="code=ARTIFACT_SEMANTIC_MISMATCH$"):
        verify_package(run_package)


@pytest.mark.parametrize("mutation", ["candidate", "ranking", "summary", "context", "rejection"])
def test_search_semantic_mutation_rehashed_still_fails(run_package, mutation):
    path = run_package / "search-result.json"
    data = read(path)
    if mutation == "candidate":
        data["rankedCandidates"][0]["candidate"]["candidate"]["heightM"] -= 1
    elif mutation == "ranking":
        data["rankedCandidates"][0]["rank"] = 2
    elif mutation == "summary":
        data["summary"]["reviewRequired"] = False
    elif mutation == "context":
        data["constraintContext"]["constraintCaps"]["maxHeightM"] -= 1
    else:
        data["rejections"] = [{"floorHeightM": 9, "code": "NO_FEASIBLE_MASSING"}]
    write(path, data)
    rehash(run_package, "search")
    with pytest.raises(RunError, match="code=ARTIFACT_SEMANTIC_MISMATCH$"):
        verify_package(run_package)


@pytest.mark.parametrize("mutation", ["basis", "height-set", "height-order"])
def test_configuration_mismatch_detected(run_package, mutation):
    manifest = read(run_package / "manifest.json")
    config = manifest["configuration"]
    if mutation == "basis":
        config["areaBasis"] = "geometry_area"
    elif mutation == "height-set":
        config["floorHeightsM"] = [4, 5]
    else:
        config["floorHeightsM"].reverse()
    write(run_package / "manifest.json", manifest)
    with pytest.raises(RunError, match="code=CONFIGURATION_MISMATCH$"):
        verify_package(run_package)


@pytest.mark.parametrize("path", ["../project.json", "/synthetic/input.json", "X:" + "/" + "synthetic/input.json",
                                "folder/project.json", "project.json\n", "project.json:extra"])
def test_manifest_path_leak_mutation_rejected(run_package, path):
    manifest = read(run_package / "manifest.json")
    manifest["artifacts"]["project"]["path"] = path
    write(run_package / "manifest.json", manifest)
    with pytest.raises(RunError, match="code=MANIFEST_SCHEMA_INVALID$"):
        verify_package(run_package)


@pytest.mark.parametrize("field", ["createdAt", "timestamp", "hostname", "machine", "sourcePath", "clientName"])
def test_manifest_metadata_leak_rejected(run_package, field):
    manifest = read(run_package / "manifest.json")
    manifest[field] = "synthetic-forbidden-metadata"
    with pytest.raises(RunError, match="code=MANIFEST_SCHEMA_INVALID$"):
        validate_manifest(manifest)


def test_manifest_contains_no_input_names_paths_or_clock(run_package, run_inputs):
    raw = (run_package / "manifest.json").read_text(encoding="utf-8")
    assert str(run_package) not in raw and str(run_inputs) not in raw
    assert "Example Urban Office" not in raw and "example-urban-office" not in raw
    assert all(field not in raw for field in ("createdAt", "timestamp", "hostname", "sourcePath", "sourceReference"))


@pytest.mark.parametrize("payload", [b'{"schemaVersion":"0.1","schemaVersion":"0.1"}', b'{', b'\xff', b'NaN'])
def test_malformed_or_duplicate_manifest_rejected(run_package, payload):
    (run_package / "manifest.json").write_bytes(payload)
    with pytest.raises(RunError, match="code=INVALID_JSON$"):
        verify_package(run_package)
