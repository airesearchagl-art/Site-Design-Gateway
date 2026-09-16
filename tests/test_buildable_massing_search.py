"""Independent domain/cap/containment oracles and authoritative spatial export."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json

import pytest
from shapely.affinity import translate

from bve._schemas import schema_validator
from bve.constraints import compute_constraints, load_constraint_result, load_project
from bve.constraints.export import canonical_json_bytes, result_bytes
from bve.massing import generate_massing_candidate, MassingError
from bve.massing.export import candidate_bytes
from bve.massing import engine
from bve.search import search_massing_candidates, SearchError
from bve.search.export import search_bytes
from bve.search.model import SearchResult
from bve.spatial import SpatialError
from test_buildable_geometry import CASE, RECT, evaluate, project, raw_shape


def test_p12_candidate_v2_reference_and_domain_target(monkeypatch):
    _,site,caps,domain=evaluate();original=engine._generate_footprint
    def observed(polygon,target):
        assert polygon.equals(domain.polygon)
        assert target<=Decimal(str(domain.area_m2))
        return original(polygon,target)
    monkeypatch.setattr(engine,'_generate_footprint',observed)
    candidate=generate_massing_candidate(site,caps,floor_height_m=4,buildable_area=domain)
    data=candidate.to_dict()
    assert data['schemaVersion']=='0.2'
    assert data['inputReferences'].get('buildableArea')==domain.reference
    assert data['generator']['strategy']=='max_footprint_stack_v0.2'
    assert data['generator']['footprintMethod']=='convex_homothetic_buildable_area_v0.1'
    assert candidate.target_footprint_area_m2==candidate.footprint_area_m2==98
    assert candidate.footprint.equals(domain.polygon)
    assert (candidate.floor_count,candidate.height_m,candidate.gross_floor_area_m2)==(6,24,588)
    assert domain.polygon.covers(candidate.footprint) and site.polygon.covers(candidate.footprint)
    assert candidate_bytes(candidate)


@pytest.mark.parametrize('kind,cap,expected', [('bcr',20,40),('far',20,40),('domain',None,98)])
def test_p12_site_area_basis_and_caps_still_bound_domain(kind,cap,expected):
    value=project()
    if kind=='bcr':value['zoning']['buildingCoverageRatio']['value']=cap
    if kind=='far':value['zoning']['additionalFloorAreaRatioCaps'][0]['value']=cap
    _,site,caps,domain=evaluate(value)
    candidate=generate_massing_candidate(site,caps,floor_height_m=4,buildable_area=domain)
    assert caps.result.area.basis_area_m2==caps.result.area.geometry_area_m2==200
    assert candidate.target_footprint_area_m2==expected
    assert 0<candidate.footprint_area_m2<=expected
    assert domain.polygon.covers(candidate.footprint) and site.polygon.covers(candidate.footprint)


def test_p12_final_domain_containment_independent_of_generator(monkeypatch):
    _,site,caps,domain=evaluate()
    escaped=translate(domain.polygon,xoff=1)
    assert site.polygon.covers(escaped) and not domain.polygon.covers(escaped)
    assert escaped.area==98
    monkeypatch.setattr(engine,'_generate_footprint',lambda *_:escaped)
    with pytest.raises(MassingError,match='^GEOMETRY_GENERATION_FAILED$'):
        generate_massing_candidate(site,caps,floor_height_m=4,buildable_area=domain)


def test_p12_final_site_containment_independent_of_domain_guard(monkeypatch):
    _,site,caps,domain=evaluate()
    candidate=generate_massing_candidate(site,caps,floor_height_m=4,buildable_area=domain)
    escaped=translate(candidate.footprint,xoff=20)
    monkeypatch.setattr(engine,'_validate_domain',lambda *_:escaped)
    with pytest.raises(MassingError,match='^GEOMETRY_GENERATION_FAILED$'):
        candidate_bytes(replace(candidate,footprint=escaped))


@pytest.mark.parametrize('api',[generate_massing_candidate,search_massing_candidates])
def test_p12_explicit_api_no_missing_or_legacy_buildable(api):
    _,site,caps,domain=evaluate();kwargs={'floor_height_m':4} if api is generate_massing_candidate else {'floor_heights_m':[4]}
    with pytest.raises(SpatialError,match='^BUILDABLE_AREA_REQUIRED$'):api(site,caps,**kwargs)
    for name in ['project.json','project-far-stack.json','project-height-stack.json']:
        p=load_project((CASE/name).read_bytes());old=load_constraint_result(result_bytes(compute_constraints(p,site,area_basis='declared_project_area')))
        with pytest.raises(SpatialError,match='^INVALID_ARGUMENTS$'):api(site,old,buildable_area=domain,**kwargs)


def test_p12_site_support_not_expanded_by_convex_domain():
    value=raw_shape([[0,0],[10,0],[10,20],[9,19],[0,20],[0,0]],status='user_provided')
    _,site,caps,domain=evaluate(site_shape=value)
    with pytest.raises(MassingError,match='^UNSUPPORTED_MASSING_SITE_GEOMETRY$'):
        search_massing_candidates(site,caps,buildable_area=domain,floor_heights_m=[4])


@pytest.mark.parametrize('status,review',[('drawing_derived',False),('assumed',True),('llm_researched',True)])
def test_p12_spatial_review_aggregation(status,review):
    value=project();value['site']['area']['status']='official_verified'
    for key in ['buildingCoverageRatio','floorAreaRatio','heightLimit']:value['zoning'][key]['status']='official_verified'
    value['spatialConstraints']['buildableArea']['status']=status
    site_value=json.loads((CASE/"site.geojson").read_bytes());site_value["properties"]["sourceStatus"]="drawing_derived"
    _,site,caps,domain=evaluate(value,site_shape=site_value)
    assert caps.result.review_required is False
    candidate=generate_massing_candidate(site,caps,buildable_area=domain,floor_height_m=4)
    assert candidate.review_required is review
    result=search_massing_candidates(site,caps,buildable_area=domain,floor_heights_m=[4,5])
    assert result.review_required is review
    assert all(entry.candidate.review_required is review for entry in result.ranked_candidates)
    assert result.to_dict()['spatialContext']['buildableArea']['reviewRequired'] is review


def test_p12_search_spatial_context_and_unchanged_ranking():
    _,site,caps,domain=evaluate();result=search_massing_candidates(site,caps,buildable_area=domain,floor_heights_m=[8,6,5,7,4]);data=result.to_dict()
    assert data['schemaVersion']=='0.5' and data['spatialContext']==domain.spatial_context()
    assert data['inputReferences']['buildableArea']==domain.reference
    assert [e['grossFloorAreaM2'] for e in data['rankedCandidates']]==[588,392,392,294,294]
    assert [e['candidate']['generator']['floorHeightM'] for e in data['rankedCandidates']]==[4,5,6,7,8]
    for entry in data['rankedCandidates']:
        assert entry['candidate']['inputReferences']==data['inputReferences']
        assert entry['candidateReference']=='sha256:'+sha256(canonical_json_bytes(entry['candidate'])).hexdigest()
    for kind in ['height','floorAreaRatio']:assert data['constraintContext'][kind]==caps.result.to_dict()['constraints'][kind]
    assert search_bytes(result)


@pytest.mark.parametrize('field,replacement',[('artifactReference','sha256:'+'1'*64),('siteReference','sha256:'+'1'*64),
    ('sourceReference','sha256:'+'1'*64),('sourceStatus','assumed'),('areaM2',Decimal(99)),
    ('reviewRequired',True),('geometry',{'type':'Polygon','coordinates':[[[2,1],[8,1],[8,15],[2,15],[2,1]]]})])
def test_p12_search_spatial_exact_copy_guard(monkeypatch,field,replacement):
    _,site,caps,domain=evaluate();result=search_massing_candidates(site,caps,buildable_area=domain,floor_heights_m=[4])
    original=SearchResult.to_dict
    def changed(self):
        data=deepcopy(original(self));data['spatialContext']['buildableArea'][field]=replacement
        assert schema_validator('search_v5').is_valid(data)
        return data
    monkeypatch.setattr(SearchResult,'to_dict',changed)
    with pytest.raises(SearchError,match='^OUTPUT_SEMANTIC_INVALID$'):search_bytes(result)


@pytest.mark.parametrize('kind',['height','far'])
def test_p12_scalar_zero_keeps_spatial_context_and_zero_accepted(kind):
    value=project();key='additionalHeightCaps' if kind=='height' else 'additionalFloorAreaRatioCaps'
    value['zoning'][key][0]['value']=0
    _,site,caps,domain=evaluate(value);result=search_massing_candidates(site,caps,buildable_area=domain,floor_heights_m=[4,5])
    assert result.ranked_candidates==() and len(result.rejections)==2
    assert result.to_dict()['spatialContext']==domain.spatial_context()
    assert search_bytes(result)


def test_p12_cross_project_or_site_buildable_not_reusable():
    _,site,caps,domain=evaluate()
    from bve.geometry import SiteGeometry
    wrong_site=replace(site,source_reference='sha256:'+'0'*64)
    with pytest.raises(SpatialError,match='^BUILDABLE_AREA_SITE_REFERENCE_MISMATCH$'):
        domain.validate_binding(wrong_site,caps.result.project_reference)
    with pytest.raises(SpatialError,match='^BUILDABLE_AREA_PROJECT_REFERENCE_MISMATCH$'):
        domain.validate_binding(site,'sha256:'+'0'*64)
