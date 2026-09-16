"""P11 package version matrix, source binding and atomic failure behavior."""
from decimal import Decimal
from hashlib import sha256
import json

import pytest

from bve.constraints.export import canonical_json_bytes
from bve.run import verify_package
from bve.run.__main__ import main
from bve.run.errors import RunError
from bve.run.model import ARTIFACTS, VERSION_MATRIX
from bve.run.verification import check_versions
from test_far_run import create, rehash
from test_height_stack import CASE, project


@pytest.mark.parametrize("version,name",[("0.1","project.json"),("0.2","project-far-stack.json"),("0.3","project-height-stack.json")])
def test_cli_three_versions(version,name,tmp_path,capsys):
    output=tmp_path/"package"
    args=["create","--project",str(CASE/name),"--geometry",str(CASE/"site.geojson"),"--format","geojson",
          "--area-basis","declared_project_area","--floor-height-m","4","--output",str(output)]
    assert main(args)==0
    assert main(["verify","--package",str(output)])==0
    assert capsys.readouterr().out.count("packageVersion=sdg-run-package-v"+version)==2
    manifest=json.loads((output/"manifest.json").read_bytes())
    assert manifest["schemaVersion"]==version
    for kind,name in ARTIFACTS.items():
        assert json.loads((output/name).read_bytes())["schemaVersion"]==VERSION_MATRIX[manifest["packageVersion"]][kind]


def test_v3_deterministic_bytes(tmp_path):
    first,summary=create(project(),tmp_path,"first");second,_=create(project(),tmp_path,"second")
    assert summary.package_version=="sdg-run-package-v0.3"
    assert verify_package(first)==summary
    assert {p.name:p.read_bytes() for p in first.iterdir()}=={p.name:p.read_bytes() for p in second.iterdir()}


@pytest.mark.parametrize("kind",list(ARTIFACTS))
def test_v3_matrix_guard(kind,tmp_path):
    output,_=create(project(),tmp_path)
    artifacts={k:(output/n).read_bytes() for k,n in ARTIFACTS.items()}
    body=json.loads(artifacts[kind],parse_float=Decimal);body["schemaVersion"]="0.2"
    artifacts[kind]=canonical_json_bytes(body)
    with pytest.raises(RunError,match="code=ARTIFACT_VERSION_MISMATCH$"):
        check_versions("sdg-run-package-v0.3",artifacts)
    (output/ARTIFACTS[kind]).write_bytes(artifacts[kind]);rehash(output,kind)
    with pytest.raises(RunError,match="code=ARTIFACT_VERSION_MISMATCH$"):
        verify_package(output)


@pytest.mark.parametrize("target",["height","floorAreaRatio"])
def test_v3_context_tamper_even_after_rehash(target,tmp_path):
    output,_=create(project(),tmp_path)
    data=json.loads((output/"search-result.json").read_bytes(),parse_float=Decimal)
    data["constraintContext"][target]["capStack"][1]["kind"]="other_explicit"
    (output/"search-result.json").write_bytes(canonical_json_bytes(data));rehash(output,"search")
    with pytest.raises(RunError,match="code=ARTIFACT_SEMANTIC_MISMATCH$"):
        verify_package(output)


def test_package_v3_requires_original_project_binding(monkeypatch,tmp_path):
    import bve.run.verification as verification
    output,_=create(project(),tmp_path)
    original=verification.load_constraint_result; supplied=[]
    def observe(raw,*,project=None):
        supplied.append(project)
        return original(raw,project=project)
    monkeypatch.setattr(verification,"load_constraint_result",observe)
    verify_package(output)
    assert len(supplied)==1 and supplied[0].schema_version=="0.3"
    data=json.loads((output/"constraints.json").read_bytes(),parse_float=Decimal)
    data["constraints"]["height"]["capStack"][1]["kind"]="other_explicit"
    (output/"constraints.json").write_bytes(canonical_json_bytes(data));rehash(output,"constraints")
    with pytest.raises(RunError,match="code=CONSTRAINT_SEMANTIC_MISMATCH$"):
        verify_package(output)


@pytest.mark.parametrize("mode",["absent","unknown-base","unknown-additional"])
def test_no_partial_package_for_unavailable_height(mode,tmp_path):
    value=project()
    if mode=="absent":
        del value["zoning"]["heightLimit"];value["zoning"]["additionalHeightCaps"]=[]
    else:
        target=value["zoning"]["heightLimit"] if mode=="unknown-base" else value["zoning"]["additionalHeightCaps"][0]
        target.update(value=None,status="unknown")
    before=canonical_json_bytes(value)
    with pytest.raises(RunError,match="stage=search code=REQUIRED_CONSTRAINT_UNAVAILABLE$"):
        create(value,tmp_path)
    assert {p.name for p in tmp_path.iterdir()}=={"package-input.json"}
    assert (tmp_path/"package-input.json").read_bytes()==before


def test_zero_height_valid_package(tmp_path):
    value=project();value["zoning"]["additionalHeightCaps"][0]["value"]=0
    output,summary=create(value,tmp_path)
    assert (summary.evaluated,summary.accepted,summary.rejected)==(5,0,5)
    assert verify_package(output)==summary


@pytest.mark.parametrize("version",["0.1","0.2"])
def test_pre_phase11_legacy_package_exact_bytes(version,tmp_path):
    # Five hashes captured from exact main base before any Phase 11 implementation.
    expected=LEGACY_HASHES[version]
    name="project.json" if version=="0.1" else "project-far-stack.json"
    output,summary=create(json.loads((CASE/name).read_bytes()),tmp_path)
    assert summary.package_version=="sdg-run-package-v"+version
    assert {p.name:sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}==expected
    assert verify_package(output)==summary


LEGACY_HASHES = {'0.1': {'constraints.json': '64ea97e8ace732231deb420b6614ae67efab8d2b4f2e275b916173c7a6dc066f', 'manifest.json': 'ec9a7945aa62f195943ae6cbf05b9fb9c8bc1d25a7d40910d1c9743ad8b228d9', 'project.json': '0ff11ad1392fdb07d9bcf793167313e14ccec5bc8771decbd2c0464cd25e7125', 'search-result.json': 'd80e60867e7fe5aa5a53ca2e362ccc75fef000dfa67c4dfb37f864a10af96262', 'site.geojson': '2b2555cbda288250663a375ee8f358ea21230a42ab112cb6989e29cbe20b7ccb'}, '0.2': {'constraints.json': '25751f04fdfec3e6442b02323510b27681afd4ee7a09b882b9c2994ed2c40cdc', 'manifest.json': '816840f7102911893bdc4cde2e52919c6088d408a807c3096a18c1877898ad4f', 'project.json': '1d26380d1c5b7de387ac7c74605642de83fdd29dff4c228315aff175a3fe6bef', 'search-result.json': '022b9ad95e139c357ced54c79c70f2a0fa78bb415660c3cd0634958055aac860', 'site.geojson': '2b2555cbda288250663a375ee8f358ea21230a42ab112cb6989e29cbe20b7ccb'}}
