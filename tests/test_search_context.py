"""Phase 7 authoritative context contracts; all inputs are synthetic."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

import pytest

from bve._schemas import schema_validator
from bve.constraints import compute_constraints, load_constraint_result, load_project
from bve.constraints.export import _encode, result_bytes
from bve.geometry import load_normalized_geometry
from bve.search import SearchError, search_massing_candidates
from bve.search.export import _validate_context, search_bytes
from bve.search.model import SearchResult


def make_result(project, normalized, basis="declared_project_area", heights=(4, 5, 6, 7, 8)):
    site = load_normalized_geometry(json.dumps(normalized))
    constraints = compute_constraints(load_project(_encode(project)), site, area_basis=basis)
    canonical = result_bytes(constraints)
    return search_massing_candidates(site, load_constraint_result(canonical), floor_heights_m=heights), canonical


@pytest.mark.parametrize("basis", ["declared_project_area", "geometry_area"])
@pytest.mark.parametrize("area", [190, 210])
def test_v2_context_is_exact_authoritative_copy(project_document, normalized_document, basis, area):
    project_document["site"]["area"]["value"] = area
    result, canonical = make_result(project_document, normalized_document, basis)
    data = json.loads(search_bytes(result), parse_float=Decimal)
    authoritative = json.loads(canonical, parse_float=Decimal, parse_int=Decimal)
    assert data["schemaVersion"] == "0.2"
    schema_validator("search").validate(data)
    context = data["constraintContext"]
    assert _encode(context["areaBasis"]) == _encode(authoritative["areaBasis"])
    assert context["areaBasis"]["differenceM2"] == area - 200
    assert context["areaBasis"]["selectedBasis"] == basis
    assert data["inputReferences"]["constraints"] == "sha256:" + sha256(canonical).hexdigest()
    assert context["constraintCaps"] == {
        "maxFootprintAreaM2": authoritative["constraints"]["buildingCoverage"]["maxFootprintAreaM2"],
        "maxTotalFloorAreaM2": authoritative["constraints"]["floorAreaRatio"]["maxTotalFloorAreaM2"],
        "maxHeightM": authoritative["constraints"]["height"]["maxHeightM"],
    }
    assert all(entry["candidate"]["constraintCaps"] == context["constraintCaps"] for entry in data["rankedCandidates"])


@pytest.mark.parametrize("field,value", [("selectedBasis", "geometry_area"), ("basisAreaM2", 199),
                                        ("differenceM2", -1), ("declaredAreaM2", 199)])
def test_area_basis_semantic_tamper(project_document, normalized_document, monkeypatch, field, value):
    result, _ = make_result(project_document, normalized_document)
    data = result.to_dict()
    data["constraintContext"]["areaBasis"][field] = value
    schema_validator("search").validate(data)
    monkeypatch.setattr(SearchResult, "to_dict", lambda self: deepcopy(data))
    with pytest.raises(SearchError, match="^OUTPUT_SEMANTIC_INVALID$"):
        search_bytes(result)


@pytest.mark.parametrize("field", ["maxFootprintAreaM2", "maxTotalFloorAreaM2", "maxHeightM"])
def test_root_cap_semantic_tamper_even_without_candidates(project_document, normalized_document, monkeypatch, field):
    result, _ = make_result(project_document, normalized_document, heights=(40,))
    data = result.to_dict()
    data["constraintContext"]["constraintCaps"][field] += 1
    schema_validator("search").validate(data)
    monkeypatch.setattr(SearchResult, "to_dict", lambda self: deepcopy(data))
    with pytest.raises(SearchError, match="^OUTPUT_SEMANTIC_INVALID$"):
        search_bytes(result)


def test_candidate_root_cap_consistency_contract(project_document, normalized_document, monkeypatch):
    result, canonical = make_result(project_document, normalized_document)
    data = result.to_dict()
    data["rankedCandidates"][0]["candidate"]["constraintCaps"]["maxHeightM"] += 1
    schema_validator("search").validate(data)
    # Exercise the context boundary independently of the existing candidate-byte guard.
    authoritative = json.loads(canonical, parse_float=Decimal, parse_int=Decimal)
    with pytest.raises(SearchError, match="^OUTPUT_SEMANTIC_INVALID$"):
        _validate_context(data, authoritative)
    monkeypatch.setattr(SearchResult, "to_dict", lambda self: deepcopy(data))
    with pytest.raises(SearchError, match="^OUTPUT_SEMANTIC_INVALID$"):
        search_bytes(result)


def test_zero_accepted_keeps_context_with_nullable_declared_area(project_document, normalized_document):
    project_document["site"]["area"].update(value=None, status="unknown")
    result, canonical = make_result(project_document, normalized_document, "geometry_area", (40,))
    data = json.loads(search_bytes(result))
    assert data["summary"]["accepted"] == 0
    assert data["constraintContext"]["areaBasis"] == json.loads(canonical)["areaBasis"]
    assert data["constraintContext"]["areaBasis"]["differenceM2"] is None
    assert data["constraintContext"]["constraintCaps"]["maxHeightM"] == 31


def test_context_hash_cannot_refer_to_different_constraints(project_document, normalized_document):
    result, _ = make_result(project_document, normalized_document, heights=(40,))
    object.__setattr__(result.constraints, "reference", "sha256:" + "0" * 64)
    with pytest.raises(SearchError, match="^OUTPUT_SEMANTIC_INVALID$"):
        search_bytes(result)


def test_legacy_schema_and_original_fixture_bytes_preserved():
    fixture = Path(__file__).resolve().parents[1] / "cases/example-urban-office/search-result.json"
    legacy = json.loads(fixture.read_bytes(), parse_float=Decimal)
    legacy.pop("constraintContext")
    legacy["schemaVersion"] = "0.1"
    schema_validator("search_legacy").validate(legacy)
    assert sha256((_encode(legacy) + "\n").encode()).hexdigest() == "96b81ec252622bce9721d100b70264238b4db083599af0c6cd58c3cc6f9b017a"


def test_v2_requires_context_and_reuses_existing_schema_fragments(project_document, normalized_document):
    result, _ = make_result(project_document, normalized_document)
    data = result.to_dict()
    data.pop("constraintContext")
    assert not schema_validator("search").is_valid(data)
    properties = schema_validator("search").schema["properties"]["constraintContext"]["properties"]
    assert properties["areaBasis"] == {"$ref": "urn:sdg:constraint-result:0.1#/properties/areaBasis"}
    assert properties["constraintCaps"] == {"$ref": "urn:sdg:massing-candidate:0.1#/properties/constraintCaps"}
