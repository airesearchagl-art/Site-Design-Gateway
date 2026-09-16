"""Version-specific file sets, semantic replay, atomic failures and frozen bytes."""
from decimal import Decimal
from hashlib import sha256
import json

import pytest

from bve.constraints.export import canonical_json_bytes
from bve.geometry.export import json_bytes
from bve.run import create_package, verify_package
from bve.run.__main__ import main
from bve.run.errors import RunError
from bve.run.model import ARTIFACTS_V4, FILE_SET, FILE_SETS
from bve.run.verification import check_versions
from test_buildable_geometry import CASE, project, raw_shape


def create(tmp_path, *, value=None, shape=None, name='package', **kwargs):
    p=tmp_path/(name+'-input.json');p.write_bytes(canonical_json_bytes(project() if value is None else value))
    b=tmp_path/(name+'-domain.geojson');b.write_bytes(json_bytes(raw_shape() if shape is None else shape))
    out=tmp_path/name
    summary=create_package(project=p,geometry=CASE/'site.geojson',format='geojson',area_basis='declared_project_area',
        floor_heights_m=[4,5,6,7,8],output=out,buildable_geometry=b,buildable_format='geojson',**kwargs)
    return out,summary


def rehash(output,kind):
    manifest=json.loads((output/'manifest.json').read_bytes(),parse_float=Decimal)
    manifest['artifacts'][kind]['reference']='sha256:'+sha256((output/ARTIFACTS_V4[kind]).read_bytes()).hexdigest()
    (output/'manifest.json').write_bytes(canonical_json_bytes(manifest))


def test_p12_v4_deterministic_six_files(tmp_path):
    a,summary=create(tmp_path,name='a');b,_=create(tmp_path,name='b')
    assert summary.package_version=='sdg-run-package-v0.4'
    assert {p.name for p in a.iterdir()}==FILE_SET|{'buildable-area.geojson'}
    assert {p.name:p.read_bytes() for p in a.iterdir()}=={p.name:p.read_bytes() for p in b.iterdir()}
    assert verify_package(a)==summary
    assert (summary.evaluated,summary.accepted,summary.rejected)==(5,5,0)


@pytest.mark.parametrize('version,name',[('0.1','project.json'),('0.2','project-far-stack.json'),('0.3','project-height-stack.json'),('0.4','project-buildable-area.json')])
def test_p12_four_cli_routes(version,name,tmp_path,capsys):
    out=tmp_path/'package';args=['create','--project',str(CASE/name),'--geometry',str(CASE/'site.geojson'),
        '--format','geojson','--area-basis','declared_project_area','--floor-height-m','4','--output',str(out)]
    if version=='0.4':args+=['--buildable-geometry',str(CASE/'buildable-area.geojson'),'--buildable-format','geojson']
    assert main(args)==0 and main(['verify','--package',str(out)])==0
    assert capsys.readouterr().out.count('packageVersion=sdg-run-package-v'+version)==2
    assert {p.name for p in out.iterdir()}==FILE_SETS['sdg-run-package-v'+version]


@pytest.mark.parametrize('mode',['missing-all','missing-format','legacy-path','legacy-format','legacy-layer','legacy-unit'])
def test_p12_buildable_arguments_explicit(tmp_path,mode):
    kwargs={};name='project-buildable-area.json';code='BUILDABLE_AREA_REQUIRED'
    if mode=='missing-format':kwargs={'buildable_geometry':CASE/'buildable-area.geojson'}
    if mode.startswith('legacy'):
        name='project-height-stack.json';code='INVALID_ARGUMENTS'
        kwargs={ {'legacy-path':'buildable_geometry','legacy-format':'buildable_format','legacy-layer':'buildable_layer','legacy-unit':'buildable_unit'}[mode]: 'm' }
    with pytest.raises(RunError,match='code='+code+'$'):
        create_package(project=CASE/name,geometry=CASE/'site.geojson',format='geojson',area_basis='declared_project_area',
                       floor_heights_m=[4],output=tmp_path/'package',**kwargs)
    assert list(tmp_path.iterdir())==[]


def test_p12_missing_sixth_file_guard_before_artifact_reads(tmp_path,monkeypatch):
    import bve.run.verification as module
    output,_=create(tmp_path);(output/'buildable-area.geojson').unlink()
    original=module.read_regular;reads=[]
    def observed(path,*args):
        reads.append(path.name);return original(path,*args)
    monkeypatch.setattr(module,'read_regular',observed)
    with pytest.raises(RunError,match='code=FILE_SET_MISMATCH$'):verify_package(output)
    assert reads==['manifest.json']


@pytest.mark.parametrize('legacy',['project.json','project-far-stack.json','project-height-stack.json'])
def test_p12_legacy_sixth_file_rejected_before_artifact_reads(tmp_path,legacy,monkeypatch):
    import bve.run.verification as module
    output=tmp_path/'package';create_package(project=CASE/legacy,geometry=CASE/'site.geojson',format='geojson',
        area_basis='declared_project_area',floor_heights_m=[4],output=output)
    (output/'buildable-area.geojson').write_bytes(b'{}')
    reads=[];original=module.read_regular
    def observed(path,*args):reads.append(path.name);return original(path,*args)
    monkeypatch.setattr(module,'read_regular',observed)
    with pytest.raises(RunError,match='code=FILE_SET_MISMATCH$'):verify_package(output)
    assert reads==['manifest.json']


@pytest.mark.parametrize('kind',list(ARTIFACTS_V4))
def test_p12_matrix_and_hash_mismatch(kind,tmp_path):
    output,_=create(tmp_path);path=output/ARTIFACTS_V4[kind];data=json.loads(path.read_bytes(),parse_float=Decimal)
    data['schemaVersion']='9.9';path.write_bytes(canonical_json_bytes(data))
    with pytest.raises(RunError,match='code=HASH_MISMATCH$'):verify_package(output)
    rehash(output,kind)
    with pytest.raises(RunError,match='code=ARTIFACT_VERSION_MISMATCH$'):verify_package(output)


@pytest.mark.parametrize('mode,code',[('site','BUILDABLE_AREA_SITE_REFERENCE_MISMATCH'),('status','BUILDABLE_AREA_STATUS_MISMATCH'),
    ('outside','BUILDABLE_AREA_OUTSIDE_SITE'),('search-context','ARTIFACT_SEMANTIC_MISMATCH'),
    ('search-ref','REFERENCE_MISMATCH'),('candidate-ref','ARTIFACT_SEMANTIC_MISMATCH')])
def test_p12_rehashed_tamper_still_semantically_rejected(mode,code,tmp_path):
    output,_=create(tmp_path)
    if mode in ('site','status','outside'):
        path=output/'buildable-area.geojson';data=json.loads(path.read_bytes())
        if mode=='site':data['properties']['siteReference']='sha256:'+'0'*64
        elif mode=='status':data['properties']['sourceStatus']='assumed'
        else:
            for point in data['geometry']['coordinates'][0]:point[0]+=20
            data['properties']['bounds']=[21.0,1.0,28.0,15.0]
        path.write_bytes(json_bytes(data));rehash(output,'buildableArea')
    else:
        path=output/'search-result.json';data=json.loads(path.read_bytes(),parse_float=Decimal)
        if mode=='search-context':data['spatialContext']['buildableArea']['areaM2']=97
        elif mode=='search-ref':data['inputReferences']['buildableArea']='sha256:'+'0'*64
        else:data['rankedCandidates'][0]['candidate']['inputReferences']['buildableArea']='sha256:'+'0'*64
        path.write_bytes(canonical_json_bytes(data));rehash(output,'search')
    with pytest.raises(RunError,match='code='+code+'$'):verify_package(output)


def test_p12_outside_domain_leaves_no_partial_package(tmp_path):
    shape=raw_shape([[1,1],[11,1],[11,15],[1,15],[1,1]])
    with pytest.raises(RunError,match='stage=spatial code=BUILDABLE_AREA_OUTSIDE_SITE$'):create(tmp_path,shape=shape)
    assert {p.name for p in tmp_path.iterdir()}=={'package-input.json','package-domain.geojson'}


@pytest.mark.parametrize('path',['../outside','/absolute','nested/buildable-area.geojson','site.geojson'])
def test_p12_manifest_path_never_traversed(path,tmp_path,monkeypatch):
    import bve.run.verification as module
    output,_=create(tmp_path);data=json.loads((output/'manifest.json').read_bytes(),parse_float=Decimal)
    data['artifacts']['buildableArea']['path']=path;(output/'manifest.json').write_bytes(canonical_json_bytes(data))
    reads=[];original=module.read_regular
    def observed(p,*args):reads.append(p.name);return original(p,*args)
    monkeypatch.setattr(module,'read_regular',observed)
    with pytest.raises(RunError,match='code=MANIFEST_SCHEMA_INVALID$'):verify_package(output)
    assert reads==['manifest.json']


def test_p12_package_always_supplies_original_project_to_reader(tmp_path,monkeypatch):
    import bve.run.verification as module
    output,_=create(tmp_path);original=module.load_constraint_result;seen=[]
    def observed(raw,*,project=None):seen.append(project);return original(raw,project=project)
    monkeypatch.setattr(module,'load_constraint_result',observed);verify_package(output)
    assert len(seen)==1 and seen[0].schema_version=='0.4'


@pytest.mark.parametrize('version,name',[('0.1','project.json'),('0.2','project-far-stack.json'),('0.3','project-height-stack.json')])
def test_p12_preimplementation_legacy_exact_bytes(version,name,tmp_path):
    output=tmp_path/'package';create_package(project=CASE/name,geometry=CASE/'site.geojson',format='geojson',
        area_basis='declared_project_area',floor_heights_m=[4,5,6,7,8],output=output)
    assert {p.name:sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}==LEGACY_HASHES[version]
    verify_package(output)


# Captured from the exact Phase 12 base before any implementation; includes all nested candidates.
LEGACY_HASHES = {
  "0.1": {
    "constraints.json": "64ea97e8ace732231deb420b6614ae67efab8d2b4f2e275b916173c7a6dc066f",
    "manifest.json": "ec9a7945aa62f195943ae6cbf05b9fb9c8bc1d25a7d40910d1c9743ad8b228d9",
    "project.json": "0ff11ad1392fdb07d9bcf793167313e14ccec5bc8771decbd2c0464cd25e7125",
    "search-result.json": "d80e60867e7fe5aa5a53ca2e362ccc75fef000dfa67c4dfb37f864a10af96262",
    "site.geojson": "2b2555cbda288250663a375ee8f358ea21230a42ab112cb6989e29cbe20b7ccb"
  },
  "0.2": {
    "constraints.json": "25751f04fdfec3e6442b02323510b27681afd4ee7a09b882b9c2994ed2c40cdc",
    "manifest.json": "816840f7102911893bdc4cde2e52919c6088d408a807c3096a18c1877898ad4f",
    "project.json": "1d26380d1c5b7de387ac7c74605642de83fdd29dff4c228315aff175a3fe6bef",
    "search-result.json": "022b9ad95e139c357ced54c79c70f2a0fa78bb415660c3cd0634958055aac860",
    "site.geojson": "2b2555cbda288250663a375ee8f358ea21230a42ab112cb6989e29cbe20b7ccb"
  },
  "0.3": {
    "constraints.json": "081bd7cfb0314e605194ae96993ee14237df9efe22c675bafe957e29805892ee",
    "manifest.json": "e06e906ad4289a8b35cda208426313b56a84d70f997831c7685414770e1b4a44",
    "project.json": "3a11fa1ad7770db5087217465f76db5f1b6b3de66a278108699c7ef98f2b35ef",
    "search-result.json": "5944fe984207da0654875a86e40aaaeb6be78c78bec9c38cd4363f1eb0e4b154",
    "site.geojson": "2b2555cbda288250663a375ee8f358ea21230a42ab112cb6989e29cbe20b7ccb"
  }
}
