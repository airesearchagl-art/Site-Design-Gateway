"""Failure injection checks source/unrelated bytes and absence of partial output."""
from pathlib import Path
from types import SimpleNamespace
import stat

import pytest

from bve.constraints import Code as ConstraintCode, ConstraintError
from bve.geometry import Code as GeometryCode, GeometryError
from bve.search import Code as SearchCode, SearchError
from bve.run import Code, RunError, Stage, create_package, verify_package
from bve.run import filesystem, orchestration
from bve.run.__main__ import main


def create(inputs, target, **kwargs):
    options = dict(project=inputs / "project.json", geometry=inputs / "site.geojson", format="geojson",
                   area_basis="declared_project_area", floor_heights_m=[4], output=target)
    options.update(kwargs)
    return create_package(**options)


@pytest.mark.parametrize("name,stage,error,code", [
    ("project_bytes", Stage.PROJECT, ConstraintError(ConstraintCode.PROJECT_SCHEMA_INVALID), "PROJECT_SCHEMA_INVALID"),
    ("read_geojson", Stage.GEOMETRY, GeometryError(GeometryCode.INVALID_POLYGON), "INVALID_POLYGON"),
    ("compute_constraints", Stage.CONSTRAINTS, ConstraintError(ConstraintCode.AREA_BASIS_UNAVAILABLE), "AREA_BASIS_UNAVAILABLE"),
    ("search_massing_candidates", Stage.SEARCH, SearchError(SearchCode.DUPLICATE_SEARCH_VALUE), "DUPLICATE_SEARCH_VALUE"),
    ("manifest_bytes", Stage.MANIFEST, RunError(Stage.MANIFEST, Code.MANIFEST_SCHEMA_INVALID), "MANIFEST_SCHEMA_INVALID"),
    ("verify_package", Stage.VERIFY, RunError(Stage.VERIFY, Code.HASH_MISMATCH), "HASH_MISMATCH"),
    ("write_new", Stage.WRITE, OSError("synthetic diagnostic must not escape"), "IO_ERROR"),
    ("publish_new", Stage.PUBLISH, OSError("synthetic diagnostic must not escape"), "IO_ERROR"),
])
def test_stage_failure_is_atomic_and_preserves_inputs(run_inputs, tmp_path, monkeypatch, name, stage, error, code):
    target = tmp_path / "package"
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_bytes(b"keep")
    source = {p.name: p.read_bytes() for p in run_inputs.iterdir()}
    before = set(tmp_path.iterdir())
    original = getattr(orchestration, name)
    calls = 0
    def fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        if name == "write_new" and calls < 3:
            return original(*args, **kwargs)
        raise error
    monkeypatch.setattr(orchestration, name, fail)
    with pytest.raises(RunError) as caught:
        create(run_inputs, target)
    assert caught.value.stage == stage and caught.value.code.value == code
    assert not target.exists() and set(tmp_path.iterdir()) == before
    assert unrelated.read_bytes() == b"keep"
    assert {p.name: p.read_bytes() for p in run_inputs.iterdir()} == source
    assert "diagnostic" not in str(caught.value)


@pytest.mark.parametrize("kind", ["file", "empty-directory", "nonempty-directory", "symlink", "dangling-symlink"])
def test_existing_output_rejected_before_core(run_inputs, tmp_path, monkeypatch, kind):
    target = tmp_path / "output"
    if kind == "file":
        target.write_bytes(b"untouched")
    elif "directory" in kind:
        target.mkdir()
        if kind == "nonempty-directory":
            (target / "user.txt").write_bytes(b"untouched")
    else:
        referent = tmp_path / "referent"
        if kind == "symlink":
            referent.mkdir()
        target.symlink_to(referent, target_is_directory=True)
    before = target.lstat()
    def unexpected(*args):
        pytest.fail("Core must not run for an existing output")
    monkeypatch.setattr(orchestration, "project_bytes", unexpected)
    with pytest.raises(RunError, match="code=OUTPUT_EXISTS$"):
        create(run_inputs, target)
    assert target.lstat().st_ino == before.st_ino
    if kind == "file":
        assert target.read_bytes() == b"untouched"
    elif kind == "nonempty-directory":
        assert (target / "user.txt").read_bytes() == b"untouched"


def test_no_clobber_even_when_target_appears_after_preflight(tmp_path, monkeypatch):
    staging, target = tmp_path / "staging", tmp_path / "target"
    staging.mkdir()
    (staging / "keep").write_bytes(b"staging")
    target.mkdir()
    inode = target.stat().st_ino
    # Exercise the native no-replace operation, not only the early lstat guard.
    monkeypatch.setattr(filesystem, "require_absent", lambda path: None)
    with pytest.raises(RunError, match="code=OUTPUT_EXISTS$"):
        filesystem.publish_new(staging, target)
    assert target.stat().st_ino == inode and list(target.iterdir()) == []
    assert (staging / "keep").read_bytes() == b"staging"


def test_exclusive_output_guard_independently(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    with pytest.raises(RunError, match="code=OUTPUT_EXISTS$"):
        filesystem.require_absent(target)


def test_interrupt_before_publication_cleans_owned_staging(run_inputs, tmp_path, monkeypatch):
    before = set(tmp_path.iterdir())
    def interrupt(*args):
        raise KeyboardInterrupt
    monkeypatch.setattr(orchestration, "verify_package", interrupt)
    with pytest.raises(KeyboardInterrupt):
        create(run_inputs, tmp_path / "output")
    assert set(tmp_path.iterdir()) == before


def test_missing_parent_does_not_create_directories(run_inputs, tmp_path):
    parent = tmp_path / "missing-parent"
    with pytest.raises(RunError, match="code=IO_ERROR$"):
        create(run_inputs, parent / "output")
    assert not parent.exists()


def test_unsupported_atomic_platform_fails_closed(tmp_path, monkeypatch):
    staging = tmp_path / "staging"
    staging.mkdir()
    target = tmp_path / "output"
    monkeypatch.setattr(filesystem, "os", SimpleNamespace(name="posix"))
    monkeypatch.setattr(filesystem, "sys", SimpleNamespace(platform="unsupported"))
    with pytest.raises(RunError, match="code=ATOMIC_PUBLISH_UNAVAILABLE$"):
        filesystem.publish_new(staging, target)
    assert staging.is_dir() and not target.exists()


@pytest.mark.parametrize("name", ["manifest.json", "project.json", "site.geojson", "constraints.json", "search-result.json"])
def test_artifact_symlink_is_rejected(run_package, tmp_path, name):
    artifact = run_package / name
    external = tmp_path / "external"
    raw = artifact.read_bytes()
    external.write_bytes(raw)
    artifact.unlink()
    artifact.symlink_to(external)
    with pytest.raises(RunError, match="code=NOT_REGULAR_FILE$"):
        verify_package(run_package)
    assert external.read_bytes() == raw


def test_package_directory_symlink_is_rejected(run_package, tmp_path):
    link = tmp_path / "package-link"
    link.symlink_to(run_package, target_is_directory=True)
    with pytest.raises(RunError, match="code=NOT_PACKAGE_DIRECTORY$"):
        verify_package(link)


def test_reparse_file_guard_without_following_it(tmp_path, monkeypatch):
    target = tmp_path / "file"
    target.write_bytes(b"keep")
    info = target.lstat()
    # Windows reparse files can otherwise look regular. This guard is tested
    # independently of the OS's additional O_NOFOLLOW defense on Linux.
    synthetic = SimpleNamespace(st_mode=info.st_mode, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
                                st_dev=info.st_dev, st_ino=info.st_ino, st_size=info.st_size)
    monkeypatch.setattr(Path, "lstat", lambda self: synthetic)
    with pytest.raises(RunError, match="code=NOT_REGULAR_FILE$"):
        filesystem.read_regular(target, 100, Stage.VERIFY)


@pytest.mark.parametrize("field,values,code,stage", [
    ("floor_heights_m", [], "SEARCH_SPACE_REQUIRED", "search"),
    ("floor_heights_m", [4, "4.0"], "DUPLICATE_SEARCH_VALUE", "search"),
    ("floor_heights_m", [0], "INVALID_FLOOR_HEIGHT", "search"),
    ("floor_heights_m", [float("nan")], "INVALID_FLOOR_HEIGHT", "search"),
    ("floor_heights_m", list(range(1, 66)), "SEARCH_SPACE_TOO_LARGE", "search"),
    ("area_basis", None, "AREA_BASIS_REQUIRED", "constraints"),
    ("area_basis", "automatic", "INVALID_AREA_BASIS", "constraints"),
])
def test_core_errors_keep_stage_and_code(run_inputs, tmp_path, field, values, code, stage):
    target = tmp_path / "output"
    with pytest.raises(RunError) as caught:
        create(run_inputs, target, **{field: values})
    assert caught.value.stage.value == stage and caught.value.code.value == code
    assert not target.exists()


def test_cli_io_and_argument_failures_do_not_disclose_paths(tmp_path, capsys):
    missing = tmp_path / "sensitive-placeholder"
    assert main(["verify", "--package", str(missing)]) == 1
    assert capsys.readouterr().out == "FAIL stage=verify code=IO_ERROR\n"
    assert main(["create", "--project", str(missing), "--geometry", str(missing), "--format", "geojson",
                 "--layer", "synthetic-layer", "--area-basis", "geometry_area", "--floor-height-m", "4",
                 "--output", str(tmp_path / "output")]) == 1
    assert capsys.readouterr().out == "FAIL stage=arguments code=INVALID_ARGUMENTS\n"
