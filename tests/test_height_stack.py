"""P11 Project / Constraint boundaries using only public synthetic conditions."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

import pytest

from bve._schemas import schema_validator
from bve.constraints import ConstraintError, compute_constraints, load_constraint_result, load_project
from bve.constraints.export import canonical_json_bytes, project_bytes, result_bytes
from bve.constraints.model import FAR_STACK_REVIEW_STATUSES, REVIEW_STATUSES
from bve.geometry import load_normalized_geometry, read_geojson
from bve.geometry.export import json_bytes, normalized_feature
from bve.validation import validate_project

CASE = Path(__file__).resolve().parents[1] / "cases/example-urban-office"


def project():
    return json.loads((CASE / "project-height-stack.json").read_bytes())


def cap(id="explicit-height-cap", value=24, status="user_provided", kind="absolute_height_explicit"):
    return {"id": id, "kind": kind, "value": value, "unit": "m", "status": status}


def evaluate(value, *, bound=True):
    site = load_normalized_geometry(json_bytes(normalized_feature(read_geojson((CASE / "site.geojson").read_bytes()))))
    source = load_project(canonical_json_bytes(value))
    result = compute_constraints(source, site, area_basis="declared_project_area")
    return source, site, load_constraint_result(result_bytes(result), project=source if bound else None)


@pytest.mark.parametrize("caps", [[], [cap()], [cap(), cap("second", 25, kind="external_rule_result")]])
def test_project_v3_explicit_stacks(caps):
    value = project(); value["zoning"]["additionalHeightCaps"] = caps
    assert validate_project(value).valid
    assert load_project(json.dumps(value)).schema_version == "0.3"


def test_duplicate_height_id_guard():
    value = project(); value["zoning"]["additionalHeightCaps"] = [cap(), cap(value=20)]
    assert schema_validator("project_v3").is_valid(value)
    assert validate_project(value).code == "duplicate_height_cap_id"
    with pytest.raises(ConstraintError, match="^DUPLICATE_HEIGHT_CAP_ID$"):
        load_project(json.dumps(value))


@pytest.mark.parametrize("change", [{"id":"base-height"}, {"id":"UPPER"}, {"id":"a"*81},
    {"id":"cap\n"}, {"value":-1}, {"unit":"mm"}, {"kind":"north_slope"}, {"description":"synthetic"},
    {"value":None,"status":"user_provided"}, {"value":None,"status":"llm_researched"}])
def test_invalid_height_entry(change):
    value=project(); value["zoning"]["additionalHeightCaps"][0].update(change)
    assert not validate_project(value).valid
    with pytest.raises(ConstraintError,match="^PROJECT_SCHEMA_INVALID$"):
        load_project(json.dumps(value))


def test_required_max16_and_separate_id_namespaces():
    value=project(); caps=[cap(f"cap-{i}") for i in range(16)]
    value["zoning"]["additionalHeightCaps"]=caps
    assert validate_project(value).valid
    caps.append(cap("cap-16")); assert not validate_project(value).valid
    del value["zoning"]["additionalHeightCaps"]; assert not validate_project(value).valid
    value=project(); value["zoning"]["additionalHeightCaps"][0]["id"]="road-width-cap"
    assert validate_project(value).valid  # Uniqueness is within each separate stack.
    value["zoning"]["heightLimit"]["value"]=0
    assert not validate_project(value).valid  # Legacy positive base contract is unchanged.


@pytest.mark.parametrize("version", ["0.4","latest",None,3])
def test_unknown_version_no_fallback(version):
    value=project(); value["schemaVersion"]=version
    assert not validate_project(value).valid
    with pytest.raises(ConstraintError,match="^PROJECT_SCHEMA_INVALID$"):
        load_project(json.dumps(value))


@pytest.mark.parametrize("base,caps,expected,ids", [
    (31,[],31,["base-height"]), (31,[cap()],24,["explicit-height-cap"]),
    (31,[cap(value=40)],31,["base-height"]), (31,[cap(value=31)],31,["base-height","explicit-height-cap"]),
    (31,[cap("z",20),cap("a",20),cap("middle",28)],20,["z","a"]),
    ("absent",[cap()],24,["explicit-height-cap"]), (31,[cap(value=0)],0,["explicit-height-cap"]),
])
def test_height_min_and_ties(base,caps,expected,ids):
    value=project(); value["zoning"]["additionalHeightCaps"]=caps
    if base == "absent": del value["zoning"]["heightLimit"]
    else: value["zoning"]["heightLimit"]["value"]=base
    _,_,result=evaluate(value)
    height=result.result.to_dict()["constraints"]["height"]
    assert height["state"]=="COMPUTED"
    assert height["maxHeightM"]==height["effectiveHeightM"]==Decimal(expected)
    assert type(height["effectiveHeightM"]) is Decimal
    assert height["effectiveCapIds"]==ids
    assert height["calculationId"]=="height_cap_stack_v0.3"
    assert [e["id"] for e in height["capStack"]]==([] if base=="absent" else ["base-height"])+[c["id"] for c in caps]


def test_base_absent_empty_stack():
    value=project(); del value["zoning"]["heightLimit"]; value["zoning"]["additionalHeightCaps"]=[]
    from bve.constraints.height_stack import compute_height_stack
    source=load_project(canonical_json_bytes(value))
    raw=compute_height_stack(source.reference,source.height,source.additional_height_caps)
    assert raw.state=="ABSENT" and raw.value is None and raw.cap_stack==()
    _,_,result=evaluate(value)
    assert result.result.to_dict()["constraints"]["height"]=={
        "state":"ABSENT","calculationId":"height_cap_stack_v0.3","maxHeightM":None,
        "effectiveHeightM":None,"effectiveCapIds":[],"capStack":[],"reviewRequired":False}


@pytest.mark.parametrize("where",["base","first","last","no-base"])
@pytest.mark.parametrize("status",["unknown","review_required"])
def test_height_unknown_fail_closed(where,status):
    value=project(); caps=[cap("a",24),cap("b",20)]; value["zoning"]["additionalHeightCaps"]=caps
    source=value["zoning"]["heightLimit"] if where=="base" else caps[-1 if where=="last" else 0]
    source.update(value=None,status=status)
    if where=="no-base": del value["zoning"]["heightLimit"]
    _,_,result=evaluate(value); h=result.result.to_dict()["constraints"]["height"]
    assert h["state"]=="UNAVAILABLE"
    assert h["effectiveHeightM"] is None and h["maxHeightM"] is None
    assert h["effectiveCapIds"]==[] and h["reviewRequired"] is True
    assert len(h["capStack"])==(2 if where=="no-base" else 3)


def test_height_decimal_and_provenance():
    outputs=[]
    for number in [Decimal("24"),Decimal("24.00"),Decimal("2.4e1")]:
        value=project(); value["zoning"]["additionalHeightCaps"][0]["value"]=number
        with localcontext() as context:
            context.prec=2
            source,_,result=evaluate(value); outputs.append(result_bytes(result.result))
    assert outputs[0]==outputs[1]==outputs[2]
    value["zoning"]["heightLimit"]["value"]=Decimal("24.0000000000000000001")
    value["zoning"]["additionalHeightCaps"]=[cap("z",Decimal("24.0000000000000000000"),"drawing_derived"),cap("a",30,kind="external_rule_result")]
    source,_,result=evaluate(value); h=result.result.to_dict()["constraints"]["height"]
    assert h["effectiveCapIds"]==["z"]
    assert [e["id"] for e in h["capStack"]]==["base-height","z","a"]
    assert [e["kind"] for e in h["capStack"]]==["base_height","absolute_height_explicit","external_rule_result"]
    assert h["capStack"][1]["condition"]["status"]=="drawing_derived"
    assert all(e["reference"]==source.reference for e in h["capStack"])
    assert source.reference=="sha256:"+sha256(project_bytes(canonical_json_bytes(value))).hexdigest()
    before=source.reference; value["zoning"]["additionalHeightCaps"].reverse()
    assert load_project(canonical_json_bytes(value)).reference!=before


@pytest.mark.parametrize("where",["base","additional"])
@pytest.mark.parametrize("status,review",[("official_verified",False),("user_provided",False),
    ("drawing_derived",False),("llm_researched",True),("assumed",True),("unknown",True),("review_required",True)])
def test_height_review_policy(where,status,review):
    value=project(); value["zoning"]["heightLimit"]["status"]="official_verified"
    target=value["zoning"]["heightLimit"] if where=="base" else value["zoning"]["additionalHeightCaps"][0]
    target["status"]=status
    _,_,result=evaluate(value); h=result.result.to_dict()["constraints"]["height"]
    assert h["reviewRequired"]==review
    assert h["capStack"][0 if where=="base" else 1]["reviewRequired"]==review
    assert h["capStack"][0 if where=="base" else 1]["condition"]["status"]==status
    assert REVIEW_STATUSES=={"assumed","unknown","review_required"}
    assert FAR_STACK_REVIEW_STATUSES=={"llm_researched","assumed","unknown","review_required"}


@pytest.mark.parametrize("field,replacement",[("effectiveHeightM",23),("maxHeightM",23),
    ("effectiveCapIds",["base-height"]),("reviewRequired",True),("reference","sha256:"+"0"*64)])
def test_internal_height_derived_tamper_rejected(field,replacement):
    _,_,result=evaluate(project()); data=result.result.to_dict()
    target=data["constraints"]["height"]
    if field=="reference": target=target["capStack"][1]
    target[field]=not target[field] if field=="reviewRequired" else replacement
    assert schema_validator("constraints_v3").is_valid(data)
    with pytest.raises(ConstraintError,match="^CONSTRAINT_SEMANTIC_MISMATCH$"):
        load_constraint_result(canonical_json_bytes(data))


@pytest.mark.parametrize("field",["id","kind","value","status","order","input"])
def test_original_project_binding_rejects_self_consistent_height_source_tamper(field):
    value=project(); value["zoning"]["additionalHeightCaps"].append(cap("non-min",28))
    if field=="input": del value["zoning"]["heightLimit"]
    source,_,result=evaluate(value); data=result.result.to_dict(); h=data["constraints"]["height"]
    entry=h["capStack"][-1]
    if field=="id": entry["id"]="different-non-min"
    elif field=="kind": entry["kind"]="other_explicit"
    elif field=="value": entry["condition"]["value"]=29
    elif field=="status": entry["condition"]["status"]="drawing_derived"
    elif field=="order": h["capStack"][1:]=reversed(h["capStack"][1:])
    else:
        entry=h["capStack"][0]
        entry.update(id="base-height",kind="base_height",input="zoning.heightLimit")
        h["effectiveCapIds"]=["base-height"]
    assert schema_validator("constraints_v3").is_valid(data)
    raw=canonical_json_bytes(data)
    assert load_constraint_result(raw).result.schema_version=="0.3"  # Internal consistency is not source authentication.
    with pytest.raises(ConstraintError,match="^CONSTRAINT_SEMANTIC_MISMATCH$"):
        load_constraint_result(raw,project=source)


def test_binding_wrong_project_and_duplicate_stack():
    source,_,result=evaluate(project()); data=result.result.to_dict()
    wrong=project(); wrong["zoning"]["additionalHeightCaps"][0]["value"]=22
    with pytest.raises(ConstraintError,match="^CONSTRAINT_SEMANTIC_MISMATCH$"):
        load_constraint_result(result_bytes(result.result),project=load_project(canonical_json_bytes(wrong)))
    data["constraints"]["height"]["capStack"].append(deepcopy(data["constraints"]["height"]["capStack"][1]))
    assert schema_validator("constraints_v3").is_valid(data)
    with pytest.raises(ConstraintError,match="^CONSTRAINT_SEMANTIC_MISMATCH$"):
        load_constraint_result(canonical_json_bytes(data),project=source)
