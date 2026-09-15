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
                             capture_output=True, env={**os.environ, 'PYTHONHASHSEED': str(seed)}, check=False)
        assert (run.returncode, run.stdout, run.stderr) == (0, b'PASS evaluated=5 accepted=5 rejected=0 reviewRequired=true\r\n' if os.name == 'nt' else b'PASS evaluated=5 accepted=5 rejected=0 reviewRequired=true\n', b'')
        outputs.append(output.read_bytes())
    assert len(set(outputs)) == 1


def test_cli_never_overwrites_input(cli_inputs, capsys):
    for input_path in (cli_inputs[1], cli_inputs[3]):
        before = Path(input_path).read_bytes()
        assert main(cli_inputs + flags([4]) + ['--output', input_path]) == 2
        captured = capsys.readouterr()
        assert captured.out == 'FAIL code=OUTPUT_EXISTS\n' and captured.err == ''
        assert Path(input_path).read_bytes() == before
