"""Constraint CLI: counts/fixed codes only; no input values or diagnostics."""
import argparse
from pathlib import Path

from bve.geometry import GeometryError, load_normalized_geometry
from bve.geometry.geojson import MAX_INPUT_BYTES as GEOMETRY_LIMIT
from bve.validation import MAX_INPUT_BYTES as PROJECT_LIMIT

from .engine import compute_constraints
from .errors import Code, ConstraintError
from .export import constraint_summary, result_bytes, write_output
from .inputs import load_project


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ConstraintError(Code.INVALID_ARGUMENTS)


class _Once(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            raise ConstraintError(Code.INVALID_ARGUMENTS)
        setattr(namespace, self.dest, values)


def _read(path: str, limit: int) -> bytes:
    try:
        with Path(path).open("rb") as source:
            return source.read(limit + 1)
    except (OSError, ValueError):
        raise ConstraintError(Code.IO_ERROR) from None


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(prog="python -m bve.constraints", allow_abbrev=False,
                     description="Transform existing conditions only; not regulatory verification.")
    parser.add_argument("--project", required=True, action=_Once, help="local Project JSON")
    parser.add_argument("--geometry", required=True, action=_Once, help="normalized local XY Geometry JSON")
    parser.add_argument("--area-basis", action=_Once, metavar="{declared_project_area,geometry_area}")
    parser.add_argument("--output", action=_Once, type=Path, help="new Constraint Result JSON file")
    try:
        args = parser.parse_args(argv)
        project = load_project(_read(args.project, PROJECT_LIMIT))
        geometry = load_normalized_geometry(_read(args.geometry, GEOMETRY_LIMIT))
        result = compute_constraints(project, geometry, area_basis=args.area_basis)
        if args.output is not None:
            write_output(result, args.output)
        else:
            result_bytes(result)  # Same output contract validation without creating a file.
        summary = constraint_summary(result)
    except (ConstraintError, GeometryError) as error:
        print(f"FAIL code={error.code.value}")
        return 2 if error.code.value in ("INVALID_ARGUMENTS", "IO_ERROR", "OUTPUT_EXISTS",
                                        "SCHEMA_UNAVAILABLE", "OUTPUT_SCHEMA_INVALID", "INTERNAL_ERROR") else 1
    except Exception:
        print("FAIL code=INTERNAL_ERROR")
        return 2
    print(f"PASS reviewRequired={str(summary['reviewRequired']).lower()} computed={summary['computed']} "
          f"unavailable={summary['unavailable']} absent={summary['absent']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
