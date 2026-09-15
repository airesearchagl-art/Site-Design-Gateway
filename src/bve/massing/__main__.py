"""Local massing CLI: floor count/review flag or fixed failure only."""
import argparse
from pathlib import Path

from bve.constraints import ConstraintError, load_constraint_result
from bve.constraints.reader import MAX_RESULT_BYTES
from bve.geometry import GeometryError, load_normalized_geometry
from bve.geometry.geojson import MAX_INPUT_BYTES as GEOMETRY_LIMIT

from .engine import generate_massing_candidate
from .errors import Code, MassingError
from .export import candidate_bytes, write_output


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise MassingError(Code.INVALID_ARGUMENTS)


class _Once(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            raise MassingError(Code.INVALID_ARGUMENTS)
        setattr(namespace, self.dest, values)


def _read(path: str, limit: int) -> bytes:
    try:
        with Path(path).open("rb") as source:
            return source.read(limit + 1)
    except (OSError, ValueError):
        raise MassingError(Code.IO_ERROR) from None


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(prog="python -m bve.massing", allow_abbrev=False,
                     description="One constraint-bounded conceptual candidate; no legal verification.")
    parser.add_argument("--geometry", required=True, action=_Once)
    parser.add_argument("--constraints", required=True, action=_Once)
    parser.add_argument("--floor-height-m", action=_Once)
    parser.add_argument("--output", action=_Once, type=Path)
    try:
        args = parser.parse_args(argv)
        site = load_normalized_geometry(_read(args.geometry, GEOMETRY_LIMIT))
        constraints = load_constraint_result(_read(args.constraints, MAX_RESULT_BYTES))
        candidate = generate_massing_candidate(site, constraints, floor_height_m=args.floor_height_m)
        if args.output is None:
            candidate_bytes(candidate)
        else:
            write_output(candidate, args.output)
    except (MassingError, ConstraintError, GeometryError) as error:
        print(f"FAIL code={error.code.value}")
        return 2 if error.code.value in ("INVALID_ARGUMENTS", "IO_ERROR", "OUTPUT_EXISTS", "SCHEMA_UNAVAILABLE",
                                        "OUTPUT_SCHEMA_INVALID", "INTERNAL_ERROR") else 1
    except Exception:
        print("FAIL code=INTERNAL_ERROR")
        return 2
    print(f"PASS floors={candidate.floor_count} reviewRequired={str(candidate.review_required).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
