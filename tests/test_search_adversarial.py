"""Search must not hide shared input faults even when no floor could fit."""
from dataclasses import replace
from decimal import Decimal
import json

import pytest
from shapely import Polygon

from bve.constraints import compute_constraints, load_constraint_result, load_project
from bve.constraints.export import _encode, result_bytes
from bve.geometry import load_normalized_geometry
from bve.massing import MassingError
from bve.massing import engine as massing_engine
from bve.search import SearchError, search_massing_candidates
from bve.search import engine, export
from test_search_engine import inputs


@pytest.mark.parametrize('heights', [[4, 5], [32, 40]])
@pytest.mark.parametrize('which', ['site', 'constraints'])
def test_raw_objects_rejected(project_document, normalized_document, heights, which):
    site, caps = inputs(project_document, normalized_document)
    with pytest.raises(MassingError, match='^INVALID_ARGUMENTS$'):
        search_massing_candidates({} if which == 'site' else site, {} if which == 'constraints' else caps,
                                  floor_heights_m=heights)


@pytest.mark.parametrize('field', ['buildingCoverageRatio', 'floorAreaRatio', 'heightLimit', 'absent'])
def test_unavailable_even_zero_feasible(project_document, normalized_document, field):
    if field == 'absent': del project_document['zoning']['heightLimit']
    else: project_document['zoning'][field].update(value=None, status='unknown')
    with pytest.raises(MassingError, match='^REQUIRED_CONSTRAINT_UNAVAILABLE$'):
        search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=[32, 40])


@pytest.mark.parametrize('which', ['reference', 'status', 'area'])
def test_binding_even_zero_feasible(project_document, normalized_document, which):
    site, caps = inputs(project_document, normalized_document)
    if which == 'reference': site = load_normalized_geometry(json.dumps(normalized_document, indent=2))
    if which == 'status': site = replace(site, source_status='official_verified')
    if which == 'area': site = replace(site, polygon=Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]))
    code = 'INPUT_REFERENCE_MISMATCH' if which == 'reference' else 'INPUT_GEOMETRY_MISMATCH'
    with pytest.raises(MassingError, match=f'^{code}$'):
        search_massing_candidates(site, caps, floor_heights_m=[32, 40])


@pytest.mark.parametrize('polygon', [Polygon([(0, 0), (10, 0), (4, 4), (10, 10), (0, 10)]),
    Polygon([(0, 0), (10, 0), (10, 10), (0, 10)], holes=[[(2, 2), (3, 2), (3, 3), (2, 3)]])], ids=['concave', 'hole'])
def test_unsupported_geometry_whole_search(project_document, normalized_document, polygon):
    site, _ = inputs(project_document, normalized_document)
    site = replace(site, polygon=polygon)
    caps = load_constraint_result(result_bytes(compute_constraints(load_project(_encode(project_document)), site,
                                                                  area_basis='declared_project_area')))
    with pytest.raises(MassingError, match='^UNSUPPORTED_MASSING_SITE_GEOMETRY$'):
        search_massing_candidates(site, caps, floor_heights_m=[32, 40])


def test_shared_resource_failure_is_not_point_rejection(project_document, normalized_document, monkeypatch):
    site, caps = inputs(project_document, normalized_document)
    monkeypatch.setattr(massing_engine, 'MAX_POSITIONS', 4)
    monkeypatch.setattr(engine, 'generate_massing_candidate', lambda *a, **k: pytest.fail('must preflight first'))
    with pytest.raises(MassingError, match='^RESOURCE_LIMIT$'):
        search_massing_candidates(site, caps, floor_heights_m=[32, 40])


def test_all_64_requested_points_accounted(project_document, normalized_document):
    result = search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=list(range(64, 0, -1)))
    assert len(result.ranked_candidates) == 31 and len(result.rejections) == 33
    assert result.to_dict()['summary']['evaluated'] == 64
    assert sorted([e.candidate.floor_height_m for e in result.ranked_candidates] +
                  [e.floor_height_m for e in result.rejections]) == list(range(1, 65))


def test_zero_capacity_fails_whole_search(project_document, normalized_document):
    project_document['zoning']['buildingCoverageRatio']['value'] = 0
    with pytest.raises(MassingError, match='^NO_MASSING_CAPACITY$'):
        search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=[4, 32])


def test_false_review_preserved(project_document, normalized_document):
    project_document['site']['area']['status'] = 'user_provided'
    normalized_document['properties']['sourceStatus'] = 'user_provided'
    for condition in project_document['zoning'].values(): condition['status'] = 'user_provided'
    result = search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=[4, 32])
    assert result.review_required is False and result.to_dict()['summary']['reviewRequired'] is False


def test_candidate_validation_resource_failure_not_swallowed(project_document, normalized_document, monkeypatch):
    args = inputs(project_document, normalized_document)
    def fail(candidate): raise MassingError('RESOURCE_LIMIT')
    monkeypatch.setattr(engine, 'candidate_bytes', fail)
    with pytest.raises(MassingError, match='^RESOURCE_LIMIT$'):
        search_massing_candidates(*args, floor_heights_m=[4, 5])


def test_semantic_failure_creates_no_output(project_document, normalized_document, tmp_path):
    result = search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=[4, 5])
    bad = replace(result, ranked_candidates=(result.ranked_candidates[0],))
    output = tmp_path / 'never-created.json'
    with pytest.raises(SearchError, match='^OUTPUT_SEMANTIC_INVALID$'):
        export.write_output(bad, output)
    assert not output.exists()
