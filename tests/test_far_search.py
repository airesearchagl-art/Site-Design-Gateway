"""Versioned context guards with the unchanged generator and GFA ranking."""
from copy import deepcopy
from decimal import Decimal

import pytest

from bve._schemas import schema_validator
from bve.massing import MassingError
from bve.search import SearchError, search_massing_candidates
from bve.search.export import search_bytes
from bve.search.model import SearchResult
from test_far_stack import cap, evaluate, project


def test_search_v3_authoritative_context_and_gfa_bound():
    site, constraints = evaluate(project())
    result = search_massing_candidates(site, constraints, floor_heights_m=[4, 5, 6, 7, 8])
    data = result.to_dict()
    assert data["schemaVersion"] == "0.3"
    assert data["constraintContext"]["floorAreaRatio"] == constraints.result.to_dict()["constraints"]["floorAreaRatio"]
    assert data["constraintContext"]["areaBasis"] == constraints.result.to_dict()["areaBasis"]
    assert data["constraintContext"]["constraintCaps"]["maxTotalFloorAreaM2"] == 800
    assert all(entry.gross_floor_area_m2 <= Decimal(800) for entry in result.ranked_candidates)
    assert [e.gross_floor_area_m2 for e in result.ranked_candidates] == [Decimal(n) for n in (800,800,800,640,480)]
    assert [e.candidate.floor_height_m for e in result.ranked_candidates[:3]] == [Decimal(4),Decimal(5),Decimal(6)]
    schema_validator("search_v3").validate(data)
    assert search_bytes(result)


@pytest.mark.parametrize("field,replacement", [
    ("effectiveCapPercent", Decimal(399)), ("effectiveCapIds", ["base-zoning"]),
    ("id", "changed-cap"), ("kind", "other_explicit"), ("value", Decimal(300)),
    ("status", "assumed"), ("reviewRequired", True),
])
def test_search_far_context_exact_copy_guard(monkeypatch, field, replacement):
    site, constraints = evaluate(project())
    result = search_massing_candidates(site, constraints, floor_heights_m=[4, 5])
    original = SearchResult.to_dict
    def tampered(self):
        data = deepcopy(original(self))
        far = data["constraintContext"]["floorAreaRatio"]
        if field in ("effectiveCapPercent", "effectiveCapIds"):
            far[field] = replacement
        elif field in ("value", "status"):
            far["capStack"][1]["condition"][field] = replacement
        else:
            far["capStack"][1][field] = replacement
        assert schema_validator("search_v3").is_valid(data)
        return data
    monkeypatch.setattr(SearchResult, "to_dict", tampered)
    with pytest.raises(SearchError, match="^OUTPUT_SEMANTIC_INVALID$"):
        search_bytes(result)


@pytest.mark.parametrize("mode", ["height", "zero-far"])
def test_zero_accepted_valid_context(mode):
    value = project()
    if mode == "zero-far":
        value["zoning"]["additionalFloorAreaRatioCaps"][0]["value"] = 0
    site, constraints = evaluate(value)
    result = search_massing_candidates(site, constraints, floor_heights_m=[4,5] if mode == "zero-far" else [32,40])
    assert not result.ranked_candidates and len(result.rejections) == 2
    assert [entry.code for entry in result.rejections] == ["NO_FEASIBLE_MASSING"] * 2
    data = result.to_dict()
    assert data["constraintContext"]["constraintCaps"]["maxTotalFloorAreaM2"] == (0 if mode == "zero-far" else 800)
    assert search_bytes(result)


def test_unknown_cap_keeps_shared_input_failure_boundary():
    value = project()
    value["zoning"]["additionalFloorAreaRatioCaps"] = [cap(value=None,status="unknown")]
    site, constraints = evaluate(value)
    with pytest.raises(MassingError, match="^REQUIRED_CONSTRAINT_UNAVAILABLE$"):
        search_massing_candidates(site, constraints, floor_heights_m=[4])
