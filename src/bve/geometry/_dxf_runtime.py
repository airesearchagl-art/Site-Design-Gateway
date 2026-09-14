"""Scoped diagnostics suppression for ezdxf's synchronous geometry-only use."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from functools import lru_cache
import importlib
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import RLock

_LOCK = RLock()


class _Discard:
    def write(self, text):
        return len(text)

    def flush(self):
        pass


@contextmanager
def quiet_dxf():
    # ezdxf can print/log input tags and import-time machine paths. Do not collect
    # these diagnostics into another buffer. Restore process state even on failure.
    with _LOCK:
        previous = logging.root.manager.disable
        logging.disable(logging.CRITICAL)
        try:
            with redirect_stdout(_Discard()), redirect_stderr(_Discard()):
                yield
        finally:
            logging.disable(previous)


@lru_cache(maxsize=1)
def ezdxf_module():
    # ezdxf 1.4.4 eagerly scans system fonts on import if no cache exists. Geometry
    # requires no fonts. A disposable empty v2 cache avoids scanning/writing home
    # directories. This contains no drawing data and restores the original setting.
    with quiet_dxf(), TemporaryDirectory(prefix="sdg-fontless-") as temporary:
        cache = Path(temporary) / "ezdxf"
        cache.mkdir()
        (cache / "font_manager_cache.json").write_text(
            '{"version":2,"font-faces":[]}', encoding="utf-8")
        previous = os.environ.get("XDG_CACHE_HOME")
        os.environ["XDG_CACHE_HOME"] = temporary
        try:
            return importlib.import_module("ezdxf")
        finally:
            if previous is None:
                os.environ.pop("XDG_CACHE_HOME", None)
            else:
                os.environ["XDG_CACHE_HOME"] = previous
