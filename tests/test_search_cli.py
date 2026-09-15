"""Local CLI fixed summaries; synthetic runtime data stays in temporary paths."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from bve.constraints.export import result_bytes
from bve.search.__main__ import main
from test_search_engine import inputs


@pytest.fixture
def cli_inputs(project_document, normalized_document, tmp_path):
    _, caps = inputs(project_document, normalized_document)
    geometry, constraints = tmp_path / 'geometry.geojson', tmp_path / 'constraints.json'
    geometry.write_text(json.dumps(normalized_document), encoding='utf-8')
    constraints.write_bytes(result_bytes(caps.result))
    return ['--geometry', str(geometry), '--constraints', str(constraints)]


def flags(heights):
    return [arg for height in heights for arg in ('--floor-height-m', str(height))]


@pytest.mark.parametrize('heights,summary', [([4, 5, 6, 7, 8], '5 accepted=5 rejected=0'),
    ([4, 32], '2 accepted=1 rejected=1'), ([32, 40], '2 accepted=0 rejected=2')])
def test_cli_success(cli_inputs, heights, summary, capsys):
    assert main(cli_inputs + flags(heights)) == 0
    captured = capsys.readouterr()
    assert captured.out == f'PASS evaluated={summary} reviewRequired=true\n'
    assert captured.err == ''


@pytest.mark.parametrize('heights,code', [([], 'SEARCH_SPACE_REQUIRED'), ([4, 4.0], 'DUPLICATE_SEARCH_VALUE'),
    (list(range(1, 66)), 'SEARCH_SPACE_TOO_LARGE'), (['sensitive-value-m'], 'INVALID_FLOOR_HEIGHT')])
def test_cli_invalid_heights(cli_inputs, heights, code, capsys):
    assert main(cli_inputs + flags(heights)) == 1
    captured = capsys.readouterr()
    assert captured.out == f'FAIL code={code}\n' and captured.err == ''


def test_cli_determinism_subprocess(cli_inputs, tmp_path):
    outputs = []
    for i, (seed, heights) in enumerate([(1, [4, 5, 6, 7, 8]), (23, [4, 5, 6, 7, 8]),
        (997, [4, 5, 6, 7, 8]), (23, [8, 6, 4, 7, 5]), (23, ['4e0', '5.000', 6, 7, 8])]):
        output = tmp_path / f'result-{i}.json'
        run = subprocess.run([sys.executable, '-m', 'bve.search', *cli_inputs, *flags(heights), '--output', str(output)],
                             capture_output=True, text=True, env={**os.environ, 'PYTHONHASHSEED': str(seed)}, check=False, timeout=30)
        assert (run.returncode, run.stdout, run.stderr) == (0, 'PASS evaluated=5 accepted=5 rejected=0 reviewRequired=true\n', '')
        outputs.append(output.read_bytes())
    assert len(set(outputs)) == 1


def test_cli_never_overwrites_input(cli_inputs, capsys):
    for input_path in (cli_inputs[1], cli_inputs[3]):
        before = Path(input_path).read_bytes()
        assert main(cli_inputs + flags([4]) + ['--output', input_path]) == 2
        captured = capsys.readouterr()
        assert captured.out == 'FAIL code=OUTPUT_EXISTS\n' and captured.err == ''
        assert Path(input_path).read_bytes() == before


@pytest.mark.parametrize('change,code', [('unknown', 'INVALID_ARGUMENTS'), ('duplicate-geometry', 'INVALID_ARGUMENTS'),
    ('missing-file', 'IO_ERROR'), ('bad-geometry', 'INVALID_JSON'), ('bad-constraints', 'INVALID_JSON'),
    ('tampered-constraints', 'CONSTRAINT_SEMANTIC_MISMATCH'), ('reference', 'INPUT_REFERENCE_MISMATCH')])
def test_cli_fixed_failure_no_disclosure(cli_inputs, tmp_path, capsys, change, code):
    args = cli_inputs.copy()
    if change == 'unknown': args += ['--synthetic-sensitive-extra']
    if change == 'duplicate-geometry': args += ['--geometry', 'synthetic-sensitive-duplicate']
    if change == 'missing-file': args[1] = str(tmp_path / 'synthetic-sensitive-missing')
    if change == 'bad-geometry': Path(args[1]).write_bytes(b'{"synthetic-sensitive":')
    if change == 'bad-constraints': Path(args[3]).write_bytes(b'{"synthetic-sensitive":')
    if change == 'tampered-constraints':
        data = json.loads(Path(args[3]).read_bytes())
        data['constraints']['buildingCoverage']['maxFootprintAreaM2'] = 161
        Path(args[3]).write_text(json.dumps(data), encoding='utf-8')
    if change == 'reference':
        Path(args[1]).write_text(json.dumps(json.loads(Path(args[1]).read_bytes()), indent=2), encoding='utf-8')
    output = tmp_path / 'must-not-exist.json'
    assert main(args + flags([32, 40]) + ['--output', str(output)]) in (1, 2)
    captured = capsys.readouterr()
    assert captured.out == f'FAIL code={code}\n' and captured.err == ''
    assert not output.exists()


def test_cli_unexpected_exception_fixed(cli_inputs, capsys, monkeypatch):
    from bve.search import __main__ as cli
    def fail(*args, **kwargs): raise RuntimeError('synthetic-sensitive-raw-diagnostic')
    monkeypatch.setattr(cli, 'search_massing_candidates', fail)
    assert main(cli_inputs + flags([4])) == 2
    captured = capsys.readouterr()
    assert captured.out == 'FAIL code=INTERNAL_ERROR\n' and captured.err == ''


def test_cli_no_output_means_no_file(cli_inputs, tmp_path, capsys):
    before = set(tmp_path.iterdir())
    assert main(cli_inputs + flags([4])) == 0
    assert set(tmp_path.iterdir()) == before
    assert capsys.readouterr().err == ''


def test_cli_tie_ranking(project_document, normalized_document, tmp_path, capsys):
    project_document['zoning']['floorAreaRatio']['value'] = 80
    _, caps = inputs(project_document, normalized_document)
    geometry, constraints, output = [tmp_path / name for name in ['site.json', 'caps.json', 'result.json']]
    geometry.write_text(json.dumps(normalized_document), encoding='utf-8')
    constraints.write_bytes(result_bytes(caps.result))
    assert main(['--geometry', str(geometry), '--constraints', str(constraints), *flags([8, 4, 6]), '--output', str(output)]) == 0
    data = json.loads(output.read_bytes())
    assert [e['candidate']['generator']['floorHeightM'] for e in data['rankedCandidates']] == [4, 6, 8]
    assert [e['grossFloorAreaM2'] for e in data['rankedCandidates']] == [160, 160, 160]
    assert capsys.readouterr().err == ''
