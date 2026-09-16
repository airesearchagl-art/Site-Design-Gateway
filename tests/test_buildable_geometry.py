"""Phase 12 raw/normalized geometry, source binding and unchanged scalar rules."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from hashlib import sha256
import io
import json
from pathlib import Path

import pytest
from shapely import Polygon

from bve._schemas import schema_validator
from bve.constraints import compute_constraints, load_constraint_result, load_project, ConstraintError
from bve.constraints.export import canonical_json_bytes, result_bytes
from bve.geometry import GeometryError, load_normalized_geometry, read_geojson
from bve.geometry.export import json_bytes, normalized_feature
from bve.spatial import SpatialError, read_buildable_area, load_buildable_area, buildable_bytes
from bve.spatial.model import require_supported_buildable
from bve.validation import validate_project

CASE = Path(__file__).resolve().parents[1] / 'cases/example-urban-office'
RECT = [[1,1],[8,1],[8,15],[1,15],[1,1]]


def project():
    return json.loads((CASE/'project-buildable-area.json').read_bytes())


def raw_shape(ring=None, status='drawing_derived'):
    return {'type':'Feature', 'properties':{'unit':'m','coordinateSystem':'local_xy','sourceStatus':status},
            'geometry':{'type':'Polygon','coordinates':[deepcopy(RECT if ring is None else ring)]}}


def evaluate(value=None, shape=None, site_shape=None):
    value = project() if value is None else value
    source = (CASE/'site.geojson').read_bytes() if site_shape is None else json_bytes(site_shape)
    site = load_normalized_geometry(json_bytes(normalized_feature(read_geojson(source))))
    p = load_project(canonical_json_bytes(value))
    shape = raw_shape(status=p.buildable_area_status) if shape is None else shape
    domain = read_buildable_area(json_bytes(shape), format='geojson', site=site, project=p)
    caps = load_constraint_result(result_bytes(compute_constraints(p,site,area_basis='declared_project_area')), project=p)
    return p, site, caps, domain


def test_p12_project_valid_required_spatial_contract():
    assert validate_project(project()).valid
    for target in ('spatialConstraints','buildableArea','kind','status'):
        value=project()
        container=value if target=='spatialConstraints' else value['spatialConstraints'] if target=='buildableArea' else value['spatialConstraints']['buildableArea']
        del container[target]
        assert not validate_project(value).valid


@pytest.mark.parametrize('field', ['filename','path','url','address','client','legalRule','description'])
def test_p12_project_rejects_uncontracted_spatial_metadata(field):
    value=project(); value['spatialConstraints']['buildableArea'][field]='untrusted'
    assert not validate_project(value).valid


@pytest.mark.parametrize('version,name', [('0.1','project.json'),('0.2','project-far-stack.json'),('0.3','project-height-stack.json')])
def test_p12_project_legacy_and_no_implicit_upgrade(version,name):
    value=json.loads((CASE/name).read_bytes())
    assert validate_project(value).valid and load_project(canonical_json_bytes(value)).schema_version==version
    value['spatialConstraints']=project()['spatialConstraints']
    assert not validate_project(value).valid


def test_p12_unknown_project_rejected_and_height_ids_still_unique():
    value=project(); value['schemaVersion']='0.5'; assert not validate_project(value).valid
    value=project(); value['zoning']['additionalHeightCaps']*=2; assert not validate_project(value).valid


@pytest.mark.parametrize('ring,area', [(RECT,98),([[0,0],[10,0],[12,10],[6,20],[0,20],[0,0]],200),
                                      ([[0,1],[8,1],[8,15],[0,15],[0,1]],112)])
def test_p12_contained_equal_and_boundary_touch_allowed(ring,area):
    p,site,_,domain=evaluate(shape=raw_shape(ring))
    assert domain.area_m2==area and site.polygon.covers(domain.polygon)
    raw=buildable_bytes(domain); data=json.loads(raw)
    assert data['properties']['role']=='explicit_buildable_area'
    assert domain.site_reference==site.source_reference
    assert domain.source_reference=='sha256:'+sha256(json_bytes(raw_shape(ring))).hexdigest()
    assert domain.reference=='sha256:'+sha256(raw).hexdigest()
    assert domain.source_reference!=domain.reference!=domain.site_reference
    assert buildable_bytes(load_buildable_area(raw,site=site,project=p))==raw
    with pytest.raises(FrozenInstanceError): domain.site_reference='changed'


@pytest.mark.parametrize('ring', [ [[1,1],[11,1],[8,15],[1,15],[1,1]],
    [[-1,1],[11,1],[11,15],[-1,15],[-1,1]], [[20,1],[22,1],[22,3],[20,3],[20,1]],
    [[0,0],[10.000000000000002,0],[10,1],[0,1],[0,0]] ])
def test_p12_outside_crossing_disconnected_no_tolerance(ring):
    with pytest.raises(SpatialError,match='^BUILDABLE_AREA_OUTSIDE_SITE$'): evaluate(shape=raw_shape(ring))


@pytest.mark.parametrize('polygon', [Polygon([(1,1),(8,1),(4,4),(8,15),(1,15)]),
    Polygon(RECT,holes=[[(2,2),(3,2),(3,3),(2,3)]])],ids=['concave','hole'])
def test_p12_support_guard_rejects_without_repair(polygon):
    before=polygon.wkb
    with pytest.raises(SpatialError,match='^UNSUPPORTED_BUILDABLE_AREA_GEOMETRY$'):
        require_supported_buildable(polygon)
    assert polygon.wkb==before
    from shapely.geometry import mapping
    shape=raw_shape();shape['geometry']=mapping(polygon)
    with pytest.raises(SpatialError,match='^UNSUPPORTED_BUILDABLE_AREA_GEOMETRY$'): evaluate(shape=shape)


@pytest.mark.parametrize('mode', ['self-intersection','multipolygon','empty','nonfinite','3d','geographic','open','unit','status-missing'])
def test_p12_invalid_raw_geometry_reuses_existing_rejection(mode):
    value=raw_shape()
    if mode=='self-intersection':value['geometry']['coordinates']=[[[1,1],[8,15],[1,15],[8,1],[1,1]]]
    elif mode=='multipolygon':value['geometry']['type']='MultiPolygon'
    elif mode=='empty':value['geometry']['coordinates']=[]
    elif mode=='nonfinite':value['geometry']['coordinates'][0][1][0]=float('inf')
    elif mode=='3d':value['geometry']['coordinates'][0][1].append(0)
    elif mode=='geographic':value['properties']['coordinateSystem']='wgs84'
    elif mode=='open':value['geometry']['coordinates'][0].pop()
    elif mode=='unit':del value['properties']['unit']
    elif mode=='status-missing':del value['properties']['sourceStatus']
    p,site,_,_=evaluate()
    with pytest.raises(GeometryError):read_buildable_area(json.dumps(value),format='geojson',site=site,project=p)


def test_p12_geojson_duplicate_keys_and_numeric_ambiguity():
    p,site,_,_=evaluate()
    for raw in [json_bytes(raw_shape()).replace(b'"unit":"m"',b'"unit":"mm","unit":"m"'),
                json_bytes(raw_shape()).replace(b'[8,1]',b'[1.000000000000000000001,1]')]:
        with pytest.raises(GeometryError):read_buildable_area(raw,format='geojson',site=site,project=p)


@pytest.mark.parametrize('status,review', [('official_verified',False),('user_provided',False),('drawing_derived',False),
    ('llm_researched',True),('assumed',True),('unknown',True),('review_required',True)])
def test_p12_exact_status_binding_and_spatial_review(status,review):
    value=project();value['spatialConstraints']['buildableArea']['status']=status
    p,site,_,domain=evaluate(value)
    assert domain.source_status==status and domain.review_required is review
    wrong='assumed' if status!='assumed' else 'drawing_derived'
    with pytest.raises(SpatialError,match='^BUILDABLE_AREA_STATUS_MISMATCH$'):
        read_buildable_area(json_bytes(raw_shape(status=wrong)),format='geojson',site=site,project=p)


def test_p12_normalized_site_reference_guard():
    p,site,_,domain=evaluate();data=json.loads(buildable_bytes(domain));data['properties']['siteReference']='sha256:'+'0'*64
    with pytest.raises(SpatialError,match='^BUILDABLE_AREA_SITE_REFERENCE_MISMATCH$'):
        load_buildable_area(json_bytes(data),site=site,project=p)


@pytest.mark.parametrize('mode',['area','bounds','canonical','status'])
def test_p12_normalized_metadata_and_bytes_fail_closed(mode):
    p,site,_,domain=evaluate();data=json.loads(buildable_bytes(domain))
    if mode=='area':data['properties']['areaM2']=99
    elif mode=='bounds':data['properties']['bounds'][0]=0
    elif mode=='status':data['properties']['sourceStatus']='user_provided'
    raw=json.dumps(data).encode() if mode=='canonical' else json_bytes(data)
    with pytest.raises((SpatialError,GeometryError)):load_buildable_area(raw,site=site,project=p)


def test_p12_dxf_units_and_ambiguity_reuse():
    import ezdxf
    p,site,_,_=evaluate()
    def payload(count=1,curved=False,unit=6):
        doc=ezdxf.new('R2010');doc.units=unit
        for _ in range(count):
            entity=doc.modelspace().add_lwpolyline(RECT[:-1],close=True,dxfattribs={'layer':'DOMAIN'})
            if curved:entity.set_points([(x,y,0,0,1) for x,y in RECT[:-1]])
        stream=io.StringIO();doc.write(stream);return stream.getvalue()
    domain=read_buildable_area(payload(),format='dxf',layer='DOMAIN',site=site,project=p)
    assert domain.area_m2==98 and domain.source_status=='drawing_derived'
    for raw in [payload(count=2),payload(curved=True),payload(unit=1)]:
        with pytest.raises(GeometryError):read_buildable_area(raw,format='dxf',site=site,project=p)
    value=project();value['spatialConstraints']['buildableArea']['status']='user_provided';p=load_project(canonical_json_bytes(value))
    override=read_buildable_area(payload(unit=0),format='dxf',unit='m',site=site,project=p)
    assert override.geometry.warnings==('UNIT_OVERRIDDEN',)
    assert override.source_status=='user_provided'


def test_p12_scalar_semantics_and_ids_exact_v3():
    p,site,caps,_=evaluate();old=project();old['schemaVersion']='0.3';del old['spatialConstraints']
    previous=load_project(canonical_json_bytes(old)); expected=compute_constraints(previous,site,area_basis='declared_project_area')
    # Only the Project reference/version transitions; all scalar values, statuses and IDs remain.
    actual=result_bytes(caps.result).replace(p.reference.encode(),previous.reference.encode())
    expected_data=expected.to_dict();expected_data['schemaVersion']='0.4'
    assert actual==canonical_json_bytes(expected_data)
    assert caps.result.building_coverage.value==160 and caps.result.floor_area_ratio.value==800
    assert caps.result.height.value==24 and caps.result.area.basis_area_m2==200
    assert schema_validator('constraints_v4').is_valid(caps.result.to_dict())


def test_p12_project_bound_reader_separate_from_internal_consistency():
    p,_,caps,_=evaluate();data=caps.result.to_dict();data['constraints']['height']['capStack'][1]['kind']='other_explicit'
    raw=canonical_json_bytes(data)
    assert load_constraint_result(raw).result.schema_version=='0.4'
    with pytest.raises(ConstraintError,match='^CONSTRAINT_SEMANTIC_MISMATCH$'):load_constraint_result(raw,project=p)
