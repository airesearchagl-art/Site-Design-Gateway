from copy import deepcopy
from decimal import Decimal

import pytest

from bve._schemas import schema_validator
from bve.search import SearchError, search_massing_candidates
from bve.search.export import search_bytes
from bve.search.model import SearchResult
from bve.massing import MassingError
from test_height_stack import evaluate, project, cap


def test_search_v4_context_effective_height_and_unchanged_ranking():
    _,site,constraints=evaluate(project())
    result=search_massing_candidates(site,constraints,floor_heights_m=[8,6,4,7,5]); data=result.to_dict()
    assert data["schemaVersion"]=="0.4"
    for field in ["floorAreaRatio","height"]:
        assert data["constraintContext"][field]==constraints.result.to_dict()["constraints"][field]
    assert data["constraintContext"]["constraintCaps"]["maxHeightM"]==24
    assert [e["grossFloorAreaM2"] for e in data["rankedCandidates"]]==[800,640,640,480,480]
    assert [e["candidate"]["generator"]["floorHeightM"] for e in data["rankedCandidates"]]==[4,5,6,7,8]
    assert all(e["candidate"]["candidate"]["heightM"]<=24 for e in data["rankedCandidates"])
    assert [e["candidate"]["candidate"]["floorCount"] for e in data["rankedCandidates"]]==[5,4,4,3,3]
    assert search_bytes(result)


@pytest.mark.parametrize("field,replacement",[("effectiveHeightM",Decimal(23)),("maxHeightM",Decimal(23)),
    ("effectiveCapIds",["base-height"]),("id","changed"),("kind","other_explicit"),
    ("value",Decimal(20)),("status","drawing_derived"),("reviewRequired",True),
    ("reference","sha256:"+"0"*64)])
def test_search_height_exact_copy_guard(monkeypatch,field,replacement):
    _,site,constraints=evaluate(project()); result=search_massing_candidates(site,constraints,floor_heights_m=[4,5])
    original=SearchResult.to_dict
    def altered(self):
        data=deepcopy(original(self)); h=data["constraintContext"]["height"]
        if field in ("effectiveHeightM","maxHeightM","effectiveCapIds"): h[field]=replacement
        elif field in ("value","status"): h["capStack"][1]["condition"][field]=replacement
        else: h["capStack"][1][field]=replacement
        assert schema_validator("search_v4").is_valid(data)
        return data
    monkeypatch.setattr(SearchResult,"to_dict",altered)
    with pytest.raises(SearchError,match="^OUTPUT_SEMANTIC_INVALID$"): search_bytes(result)


def test_zero_height_completed_zero_accepted():
    value=project(); value["zoning"]["additionalHeightCaps"]=[cap(value=0)]
    _,site,constraints=evaluate(value); result=search_massing_candidates(site,constraints,floor_heights_m=[4,5,6])
    assert result.ranked_candidates==()
    assert [r.code for r in result.rejections]==["NO_FEASIBLE_MASSING"]*3
    assert result.to_dict()["constraintContext"]["height"]["effectiveHeightM"]==0
    assert result.to_dict()["constraintContext"]["constraintCaps"]["maxHeightM"]==0
    assert search_bytes(result)


@pytest.mark.parametrize("mode",["absent","unknown-base","unknown-additional","unknown-no-base"])
def test_absent_unknown_height_is_shared_failure(mode):
    value=project()
    if mode in ("absent","unknown-no-base"): del value["zoning"]["heightLimit"]
    if mode=="absent": value["zoning"]["additionalHeightCaps"]=[]
    else:
        target=value["zoning"]["heightLimit"] if mode=="unknown-base" else value["zoning"]["additionalHeightCaps"][0]
        target.update(value=None,status="unknown")
    _,site,constraints=evaluate(value)
    with pytest.raises(MassingError,match="^REQUIRED_CONSTRAINT_UNAVAILABLE$"):
        search_massing_candidates(site,constraints,floor_heights_m=[4,5])
