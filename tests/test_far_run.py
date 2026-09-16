"""Both package matrices, deterministic bytes and authoritative replay."""
from hashlib import sha256
from decimal import Decimal
import json

import pytest

from bve.constraints.export import canonical_json_bytes
from bve.run import create_package, verify_package
from bve.run.__main__ import main
from bve.run.errors import RunError
from bve.run.model import ARTIFACTS, VERSION_MATRIX, package_version_for_project
from bve.run.verification import check_versions
from test_far_stack import CASE, project


def create(document, parent, name="package"):
    input_path = parent / (name + "-input.json")
    input_path.write_bytes(canonical_json_bytes(document))
    output = parent / name
    summary = create_package(project=input_path, geometry=CASE / "site.geojson", format="geojson",
        area_basis="declared_project_area", floor_heights_m=[8,4,5,6,7], output=output)
    return output, summary


@pytest.mark.parametrize("version", ["0.1", "0.2"])
def test_package_version_routes_and_create_verify(version, tmp_path):
    value = json.loads((CASE / "project.json").read_bytes()) if version == "0.1" else project()
    output, summary = create(value, tmp_path)
    expected = "sdg-run-package-v" + version
    assert package_version_for_project(version) == expected
    assert summary.package_version == expected
    assert verify_package(output) == summary
    assert f"packageVersion={expected}" in summary.console()
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert manifest["schemaVersion"] == version and manifest["packageVersion"] == expected
    for kind, filename in ARTIFACTS.items():
        assert json.loads((output / filename).read_bytes())["schemaVersion"] == VERSION_MATRIX[expected][kind]


def test_package_v2_deterministic_exact_bytes(tmp_path):
    first, _ = create(project(), tmp_path, "first")
    second, _ = create(project(), tmp_path, "second")
    assert {p.name:p.read_bytes() for p in first.iterdir()} == {p.name:p.read_bytes() for p in second.iterdir()}


def test_legacy_package_exact_baseline_bytes(run_package):
    # Recorded from the exact pre-Phase-10 base with public synthetic [4,5,6,7,8].
    expected = {
        "constraints.json":"64ea97e8ace732231deb420b6614ae67efab8d2b4f2e275b916173c7a6dc066f",
        "manifest.json":"ec9a7945aa62f195943ae6cbf05b9fb9c8bc1d25a7d40910d1c9743ad8b228d9",
        "project.json":"0ff11ad1392fdb07d9bcf793167313e14ccec5bc8771decbd2c0464cd25e7125",
        "search-result.json":"d80e60867e7fe5aa5a53ca2e362ccc75fef000dfa67c4dfb37f864a10af96262",
        "site.geojson":"2b2555cbda288250663a375ee8f358ea21230a42ab112cb6989e29cbe20b7ccb",
    }
    assert {p.name:sha256(p.read_bytes()).hexdigest() for p in run_package.iterdir()} == expected


@pytest.mark.parametrize("kind", ["project", "geometry", "constraints", "search"])
def test_package_v2_matrix_guard(kind, tmp_path):
    output, _ = create(project(), tmp_path)
    artifacts = {key:(output/name).read_bytes() for key,name in ARTIFACTS.items()}
    body = json.loads(artifacts[kind], parse_float=Decimal)
    body["schemaVersion"] = "0.1" if kind != "geometry" else "0.2"
    artifacts[kind] = canonical_json_bytes(body)
    with pytest.raises(RunError, match="code=ARTIFACT_VERSION_MISMATCH$"):
        check_versions("sdg-run-package-v0.2", artifacts)
    (output / ARTIFACTS[kind]).write_bytes(artifacts[kind])
    rehash(output, kind)
    with pytest.raises(RunError, match="code=ARTIFACT_VERSION_MISMATCH$"):
        verify_package(output)


def rehash(output, kind):
    manifest = json.loads((output/"manifest.json").read_bytes())
    manifest["artifacts"][kind]["reference"] = "sha256:"+sha256((output/ARTIFACTS[kind]).read_bytes()).hexdigest()
    (output/"manifest.json").write_bytes(canonical_json_bytes(manifest))


def test_package_v2_far_context_tamper_even_after_rehash(tmp_path):
    output, _ = create(project(), tmp_path)
    data = json.loads((output/"search-result.json").read_bytes(), parse_float=Decimal)
    data["constraintContext"]["floorAreaRatio"]["capStack"][1]["condition"]["status"] = "assumed"
    (output/"search-result.json").write_bytes(canonical_json_bytes(data))
    rehash(output,"search")
    with pytest.raises(RunError, match="code=ARTIFACT_SEMANTIC_MISMATCH$"):
        verify_package(output)


@pytest.mark.parametrize("mode", ["hash", "reference"])
def test_v2_hash_and_reference_guards(mode, tmp_path):
    output, _ = create(project(), tmp_path)
    if mode == "hash":
        (output/"project.json").write_bytes((output/"project.json").read_bytes()+b" ")
    else:
        body = json.loads((output/"search-result.json").read_bytes(), parse_float=Decimal)
        body["inputReferences"]["constraints"] = "sha256:"+"0"*64
        (output/"search-result.json").write_bytes(canonical_json_bytes(body))
        rehash(output,"search")
    with pytest.raises(RunError, match="code="+("HASH_MISMATCH" if mode == "hash" else "REFERENCE_MISMATCH")+"$"):
        verify_package(output)


def test_unknown_cap_failure_never_publishes_partial_package(tmp_path):
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"][0].update(value=None,status="unknown")
    with pytest.raises(RunError, match="stage=search code=REQUIRED_CONSTRAINT_UNAVAILABLE$"):
        create(value, tmp_path)
    assert not (tmp_path/"package").exists() and not list(tmp_path.glob(".sdg-run-*"))


def test_zero_cap_package_is_valid_zero_accepted(tmp_path):
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"][0]["value"] = 0
    output, summary = create(value, tmp_path)
    assert summary.accepted == 0 and summary.rejected == 5
    assert verify_package(output) == summary


def test_v2_cli_and_unsupported_manifest_version(tmp_path, capsys):
    output = tmp_path/"cli"
    assert main(["create","--project",str(CASE/"project-far-stack.json"),"--geometry",str(CASE/"site.geojson"),
                 "--format","geojson","--area-basis","declared_project_area","--floor-height-m","4","--output",str(output)]) == 0
    assert main(["verify","--package",str(output)]) == 0
    assert capsys.readouterr().out.count("packageVersion=sdg-run-package-v0.2") == 2
    manifest = json.loads((output/"manifest.json").read_bytes())
    manifest["packageVersion"] = "sdg-run-package-v99"
    (output/"manifest.json").write_bytes(canonical_json_bytes(manifest))
    with pytest.raises(RunError, match="code=MANIFEST_SCHEMA_INVALID$"):
        verify_package(output)
