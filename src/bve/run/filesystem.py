"""Regular-file reads and exclusive, atomic publication on Windows and Linux."""
import ctypes
import errno
import os
from pathlib import Path
import stat
import sys

from .errors import Code, RunError, Stage


def is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def read_regular(path: Path, limit: int, stage: Stage) -> bytes:
    before = path.lstat()
    if is_link(before) or not stat.S_ISREG(before.st_mode):
        raise RunError(stage, Code.NOT_REGULAR_FILE)
    if before.st_size > limit:
        raise RunError(stage, Code.INPUT_TOO_LARGE)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as source:
        opened = os.fstat(source.fileno())
        if not stat.S_ISREG(opened.st_mode) or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise RunError(stage, Code.NOT_REGULAR_FILE)
        raw = source.read(limit + 1)
    if len(raw) > limit:
        raise RunError(stage, Code.INPUT_TOO_LARGE)
    return raw


def require_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise RunError(Stage.PUBLISH, Code.OUTPUT_EXISTS)


def publish_new(staging: Path, output: Path) -> None:
    """Never use POSIX rename/replace, which can replace an existing empty dir.

    The parent must be a trusted, stable local directory. Crash durability and
    hostile concurrent directory replacement are outside this local contract.
    """
    require_absent(output)
    try:
        if os.name == "nt":
            os.rename(staging, output)  # Windows rename rejects every existing target.
        elif sys.platform == "linux":
            library = ctypes.CDLL(None, use_errno=True)
            rename = getattr(library, "renameat2", None)
            if rename is None:
                raise RunError(Stage.PUBLISH, Code.ATOMIC_PUBLISH_UNAVAILABLE)
            rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
            rename.restype = ctypes.c_int
            if rename(-100, os.fsencode(staging), -100, os.fsencode(output), 1) != 0:
                number = ctypes.get_errno()
                if number == errno.EEXIST:
                    raise RunError(Stage.PUBLISH, Code.OUTPUT_EXISTS)
                if number in (errno.ENOSYS, errno.EINVAL, errno.ENOTSUP):
                    raise RunError(Stage.PUBLISH, Code.ATOMIC_PUBLISH_UNAVAILABLE)
                raise RunError(Stage.PUBLISH, Code.IO_ERROR)
        else:
            raise RunError(Stage.PUBLISH, Code.ATOMIC_PUBLISH_UNAVAILABLE)
    except FileExistsError:
        raise RunError(Stage.PUBLISH, Code.OUTPUT_EXISTS) from None


def write_new(path: Path, payload: bytes) -> None:
    with path.open("xb") as target:
        target.write(payload)
