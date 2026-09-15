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
