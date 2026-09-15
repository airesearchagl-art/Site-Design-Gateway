"""Synthetic sweep tests with independent ranking and per-point expectations."""
from decimal import Decimal
from hashlib import sha256
import json

import pytest

from bve.constraints import compute_constraints, load_constraint_result, load_project
from bve.constraints.export import _encode, result_bytes
from bve.geometry import load_normalized_geometry
from bve.massing import MassingError
from bve.massing.export import candidate_bytes
from bve.search import engine
from bve.search import search_massing_candidates
from bve.search.export import search_bytes
from bve.search.errors import SearchError
from bve.search.inputs import canonical_heights


def inputs(project, normalized):
    site = load_normalized_geometry(json.dumps(normalized))
    caps = compute_constraints(load_project(_encode(project)), site, area_basis="declared_project_area")
    return site, load_constraint_result(result_bytes(caps))


def test_sweep_once_per_height(project_document, normalized_document, monkeypatch):
    site, caps = inputs(project_document, normalized_document)
    original, calls = engine.generate_massing_candidate, []
    def spy(*args, floor_height_m):
        calls.append(floor_height_m)
        return original(*args, floor_height_m=floor_height_m)
    monkeypatch.setattr(engine, 'generate_massing_candidate', spy)
    accepted, rejected = engine._sweep(site, caps, canonical_heights([8, 6, 4, 7, 5]))
    assert calls == [4, 5, 6, 7, 8]
    assert len(accepted) == 5 and rejected == ()
    for entry, floors, height, gfa in zip(accepted, [7, 6, 5, 4, 3], [28, 30, 30, 28, 24], [1120, 960, 800, 640, 480]):
        c = entry.candidate
        assert c.footprint_area_m2 == Decimal(str(c.footprint.area)) == 160
        assert (c.floor_count, c.height_m, c.gross_floor_area_m2) == (floors, height, gfa)
        assert entry.candidate_reference == 'sha256:' + sha256(candidate_bytes(c)).hexdigest()


@pytest.mark.parametrize('heights,accepted,rejected', [([4, 32], 1, [32]), ([32, 40], 0, [32, 40])])
def test_sweep_feasibility(project_document, normalized_document, heights, accepted, rejected):
    a, r = engine._sweep(*inputs(project_document, normalized_document), canonical_heights(heights))
    assert len(a) == accepted
    assert [(item.floor_height_m, item.code) for item in r] == [(h, 'NO_FEASIBLE_MASSING') for h in rejected]


@pytest.mark.parametrize('code', ['GEOMETRY_GENERATION_FAILED', 'INPUT_REFERENCE_MISMATCH',
    'REQUIRED_CONSTRAINT_UNAVAILABLE', 'SCHEMA_UNAVAILABLE', 'IO_ERROR', 'INVALID_FLOOR_HEIGHT',
    'NO_MASSING_CAPACITY', 'NUMERIC_RANGE'])
def test_shared_errors_not_swallowed(project_document, normalized_document, monkeypatch, code):
    site, caps = inputs(project_document, normalized_document)
    def fail(*args, **kwargs):
        raise MassingError(code)
    monkeypatch.setattr(engine, 'generate_massing_candidate', fail)
    with pytest.raises(MassingError, match=f'^{code}$'):
        engine._sweep(site, caps, canonical_heights([4, 32]))


def test_duplicate_candidate_stops(project_document, normalized_document, monkeypatch):
    site, caps = inputs(project_document, normalized_document)
    candidate = engine.generate_massing_candidate(site, caps, floor_height_m=4)
    monkeypatch.setattr(engine, 'generate_massing_candidate', lambda *args, **kwargs: candidate)
    with pytest.raises(SearchError, match='^DUPLICATE_CANDIDATE$'):
        engine._sweep(site, caps, canonical_heights([4, 5]))


def test_point_resource_limit(project_document, normalized_document):
    project_document['zoning']['floorAreaRatio']['value'] = 1000100
    project_document['zoning']['heightLimit']['value'] = 10001
    a, r = engine._sweep(*inputs(project_document, normalized_document), canonical_heights([1, 2]))
    assert [e.candidate.floor_height_m for e in a] == [2]
    assert [(e.floor_height_m, e.code) for e in r] == [(1, 'RESOURCE_LIMIT')]


def test_ranking_and_summary(project_document, normalized_document):
    result = search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=[4, 5, 6, 7, 8])
    assert [e.rank for e in result.ranked_candidates] == [1, 2, 3, 4, 5]
    assert [e.gross_floor_area_m2 for e in result.ranked_candidates] == [1120, 960, 800, 640, 480]
    assert [e.candidate.floor_height_m for e in result.ranked_candidates] == [4, 5, 6, 7, 8]
    assert result.to_dict()['summary'] == {'evaluated': 5, 'accepted': 5, 'rejected': 0,
                                          'hasFeasibleCandidate': True, 'reviewRequired': True}
    assert result.review_required is True


@pytest.mark.parametrize('heights,accepted,rejected', [([4, 32], 1, 1), ([32, 40], 0, 2)])
def test_completed_feasibility_summary(project_document, normalized_document, heights, accepted, rejected):
    result = search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=heights)
    assert result.to_dict()['summary'] == {'evaluated': 2, 'accepted': accepted, 'rejected': rejected,
                                          'hasFeasibleCandidate': accepted > 0, 'reviewRequired': True}
    assert len(result.ranked_candidates) == accepted
    assert all('rank' not in r for r in result.to_dict()['rejections'])


def test_gfa_tie_uses_lower_height(project_document, normalized_document):
    project_document['zoning']['floorAreaRatio']['value'] = 80
    result = search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=[8, 4, 6])
    assert [e.gross_floor_area_m2 for e in result.ranked_candidates] == [160, 160, 160]
    assert [e.candidate.floor_height_m for e in result.ranked_candidates] == [4, 6, 8]


def test_reference_final_tie_key(project_document, normalized_document):
    from dataclasses import replace
    result = search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=[4])
    entry = result.ranked_candidates[0]
    first, last = replace(entry, candidate_reference='sha256:'+'0'*64), replace(entry, candidate_reference='sha256:'+'f'*64)
    assert sorted([last, first], key=engine._ranking_key) == [first, last]


def test_semantic_set_bytes_independent_of_input_order(project_document, normalized_document):
    args = inputs(project_document, normalized_document)
    first = search_bytes(search_massing_candidates(*args, floor_heights_m=[4, 5, 6, 7, 8]))
    for values in ([8, 6, 4, 7, 5], ['4.000', Decimal('5e0'), 6.0, '7', 8], [4, 5, 6, 7, 8]):
        assert search_bytes(search_massing_candidates(*args, floor_heights_m=values)) == first


def test_references_change_with_candidate(project_document, normalized_document):
    result = search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=[4, 5])
    refs = [e.candidate_reference for e in result.ranked_candidates]
    assert refs[0] != refs[1]
    assert refs == ['sha256:' + sha256(candidate_bytes(e.candidate)).hexdigest() for e in result.ranked_candidates]
