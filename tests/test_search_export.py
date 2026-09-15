"""Export corruption tests retain schema validity where testing semantic guards."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal, FloatOperation, Inexact, localcontext
import json

import pytest

from bve._schemas import schema_validator
from bve.massing import MassingError
from bve.search import SearchError, search_massing_candidates
from bve.search import export
from bve.search.model import Rejection, SearchResult
from test_search_engine import inputs


@pytest.fixture
def result(project_document, normalized_document):
    return search_massing_candidates(*inputs(project_document, normalized_document), floor_heights_m=[4, 5, 32, 40])


def test_offline_canonical_export(result, monkeypatch):
    import socket
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **k: pytest.fail('network forbidden'))
    schema_validator.cache_clear()
    data = export.search_bytes(result)
    assert data.endswith(b'\n') and not data.endswith(b'\n\n') and b'\r' not in data
    loaded = json.loads(data, parse_float=Decimal)
    schema_validator('search').validate(loaded)
    assert loaded == result.to_dict()
    assert loaded['rejections'] == [{'floorHeightM': 32, 'code': 'NO_FEASIBLE_MASSING'},
                                    {'floorHeightM': 40, 'code': 'NO_FEASIBLE_MASSING'}]


@pytest.mark.parametrize('field,value', [('evaluated', 3), ('accepted', 1), ('rejected', 1),
                                      ('hasFeasibleCandidate', False), ('reviewRequired', False)])
def test_summary_tamper(result, monkeypatch, field, value):
    data = result.to_dict()
    data['summary'][field] = value
    schema_validator('search').validate(data)
    monkeypatch.setattr(SearchResult, 'to_dict', lambda self: deepcopy(data))
    with pytest.raises(SearchError, match='^OUTPUT_SEMANTIC_INVALID$'):
        export.search_bytes(result)


@pytest.mark.parametrize('mutation', ['points_order', 'missing_point', 'duplicate_point', 'rank_gap', 'rank_order',
    'wrong_hash', 'wrong_metric', 'foreign_height', 'wrong_refs', 'candidate_review', 'rejections_order', 'duplicate_partition'])
def test_serialized_semantic_tamper(result, monkeypatch, mutation):
    data = result.to_dict()
    if mutation == 'points_order': data['search']['floorHeightsM'].reverse()
    if mutation == 'missing_point': data['search']['floorHeightsM'].pop()
    if mutation == 'duplicate_point': data['rankedCandidates'][1] = deepcopy(data['rankedCandidates'][0])
    if mutation == 'rank_gap': data['rankedCandidates'][1]['rank'] = 3
    if mutation == 'rank_order': data['rankedCandidates'].reverse()
    if mutation == 'wrong_hash': data['rankedCandidates'][0]['candidateReference'] = 'sha256:'+'0'*64
    if mutation == 'wrong_metric': data['rankedCandidates'][0]['grossFloorAreaM2'] = 1119
    if mutation == 'foreign_height': data['rankedCandidates'][0]['candidate']['generator']['floorHeightM'] = 6
    if mutation == 'wrong_refs': data['inputReferences']['project'] = 'sha256:'+'0'*64
    if mutation == 'candidate_review': data['rankedCandidates'][0]['candidate']['candidate']['reviewRequired'] = False
    if mutation == 'rejections_order': data['rejections'].reverse()
    if mutation == 'duplicate_partition': data['rejections'][1]['floorHeightM'] = 4
    schema_validator('search').validate(data)
    monkeypatch.setattr(SearchResult, 'to_dict', lambda self: deepcopy(data))
    with pytest.raises(SearchError, match='^OUTPUT_SEMANTIC_INVALID$'):
        export.search_bytes(result)


@pytest.mark.parametrize('mutation', ['order', 'missing', 'rank', 'gfa', 'hash', 'rejection', 'partition', 'binding'])
def test_internal_model_tamper(result, mutation):
    entry = result.ranked_candidates[0]
    if mutation == 'order': result = replace(result, floor_heights_m=tuple(reversed(result.floor_heights_m)))
    if mutation == 'missing': result = replace(result, ranked_candidates=(entry,))
    if mutation == 'rank': result = replace(result, ranked_candidates=(replace(entry, rank=2), result.ranked_candidates[1]))
    if mutation == 'gfa': result = replace(result, ranked_candidates=(replace(entry, gross_floor_area_m2=Decimal(1)), result.ranked_candidates[1]))
    if mutation == 'hash': result = replace(result, ranked_candidates=(replace(entry, candidate_reference='sha256:'+'0'*64), result.ranked_candidates[1]))
    if mutation == 'rejection': result = replace(result, rejections=tuple(reversed(result.rejections)))
    if mutation == 'partition': result = replace(result, rejections=(Rejection(Decimal(4), 'NO_FEASIBLE_MASSING'), result.rejections[1]))
    if mutation == 'binding': result = replace(result, site=replace(result.site))
    with pytest.raises(SearchError, match='^OUTPUT_SEMANTIC_INVALID$'):
        export.search_bytes(result)


def test_candidate_cap_rechecked(result):
    entry = result.ranked_candidates[0]
    broken = replace(entry, candidate=replace(entry.candidate, floor_count=8))
    with pytest.raises(MassingError, match='^GEOMETRY_GENERATION_FAILED$'):
        export.search_bytes(replace(result, ranked_candidates=(broken, result.ranked_candidates[1])))


def test_ambient_decimal_context(project_document, normalized_document):
    args = inputs(project_document, normalized_document)
    heights = ['4.00000000000000000000001', 5, 6, 32]
    expected = export.search_bytes(search_massing_candidates(*args, floor_heights_m=heights))
    with localcontext() as ctx:
        ctx.prec, ctx.Emin, ctx.Emax = 1, -1, 1
        ctx.traps[FloatOperation] = ctx.traps[Inexact] = True
        before = str(ctx)
        assert export.search_bytes(search_massing_candidates(*args, floor_heights_m=heights)) == expected
        assert str(ctx) == before


def test_schema_unavailable(result, monkeypatch):
    def fail(*args): raise OSError('private diagnostic')
    monkeypatch.setattr(export, 'schema_validator', fail)
    with pytest.raises(SearchError, match='^SCHEMA_UNAVAILABLE$'):
        export.search_bytes(result)


def test_explicit_new_output_and_no_mkdir(result, tmp_path):
    target = tmp_path / 'new.json'
    export.write_output(result, target)
    before = target.read_bytes()
    assert before == export.search_bytes(result)
    with pytest.raises(SearchError, match='^OUTPUT_EXISTS$'):
        export.write_output(result, target)
    assert target.read_bytes() == before
    with pytest.raises(SearchError, match='^IO_ERROR$'):
        export.write_output(result, tmp_path / 'missing' / 'new.json')
    assert not (tmp_path / 'missing').exists()


def test_symlink_guard_without_os_privilege(result, tmp_path, monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(Path, 'is_symlink', lambda self: True)
    with pytest.raises(SearchError, match='^OUTPUT_EXISTS$'):
        export.write_output(result, tmp_path / 'link.json')
    assert not (tmp_path / 'link.json').exists()
