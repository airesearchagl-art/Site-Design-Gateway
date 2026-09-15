"""Local search execution summary only; PASS makes no buildability claim."""
import argparse
from pathlib import Path

from bve.constraints import ConstraintError, load_constraint_result
from bve.constraints.reader import MAX_RESULT_BYTES
from bve.geometry import GeometryError, load_normalized_geometry
from bve.geometry.geojson import MAX_INPUT_BYTES as GEOMETRY_LIMIT
from bve.massing import MassingError

from .engine import search_massing_candidates
from .errors import Code, SearchError
from .export import write_output


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise SearchError(Code.INVALID_ARGUMENTS)


class _Once(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            raise SearchError(Code.INVALID_ARGUMENTS)
        setattr(namespace, self.dest, values)


def _read(path: str, limit: int) -> bytes:
    try:
        with Path(path).open("rb") as source:
            return source.read(limit + 1)
    except (OSError, ValueError):
        raise SearchError(Code.IO_ERROR) from None


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(prog="python -m bve.search", allow_abbrev=False,
                     description="Explicit floor-height search; GFA order only, no legal verification.")
    parser.add_argument("--geometry", required=True, action=_Once)
    parser.add_argument("--constraints", required=True, action=_Once)
    parser.add_argument("--floor-height-m", action="append")
    parser.add_argument("--output", action=_Once, type=Path)
    try:
        args = parser.parse_args(argv)
        site = load_normalized_geometry(_read(args.geometry, GEOMETRY_LIMIT))
        constraints = load_constraint_result(_read(args.constraints, MAX_RESULT_BYTES))
        result = search_massing_candidates(site, constraints, floor_heights_m=args.floor_height_m)
        if args.output is not None:
            write_output(result, args.output)
    except (SearchError, MassingError, ConstraintError, GeometryError) as error:
        print(f"FAIL code={error.code.value}")
        return 2 if error.code.value in ("INVALID_ARGUMENTS", "IO_ERROR", "OUTPUT_EXISTS", "SCHEMA_UNAVAILABLE",
                                        "OUTPUT_SCHEMA_INVALID", "OUTPUT_SEMANTIC_INVALID", "INTERNAL_ERROR") else 1
    except Exception:
        print("FAIL code=INTERNAL_ERROR")
        return 2
    print(f"PASS evaluated={len(result.floor_heights_m)} accepted={len(result.ranked_candidates)} "
          f"rejected={len(result.rejections)} reviewRequired={str(result.review_required).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
