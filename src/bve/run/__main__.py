"""No argument values, project contents, coordinates or paths in console output."""
import argparse
from pathlib import Path

from .errors import Code, RunError, Stage
from .orchestration import create_package
from .verification import verify_package


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise RunError(Stage.ARGUMENTS, Code.INVALID_ARGUMENTS)


class _Once(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            raise RunError(Stage.ARGUMENTS, Code.INVALID_ARGUMENTS)
        setattr(namespace, self.dest, values)


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(prog="python -m bve.run", allow_abbrev=False,
                     description="Local Run Package; no legal or optimization claim.")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", allow_abbrev=False)
    for name in ("project", "geometry", "output"):
        create.add_argument("--" + name, required=True, type=Path, action=_Once)
    create.add_argument("--format", required=True, choices=("geojson", "dxf"), action=_Once)
    create.add_argument("--area-basis", required=True, choices=("declared_project_area", "geometry_area"), action=_Once)
    create.add_argument("--floor-height-m", required=True, action="append")
    create.add_argument("--layer", action=_Once)
    create.add_argument("--unit", choices=("m", "mm"), action=_Once)
    create.add_argument("--buildable-geometry", type=Path, action=_Once)
    create.add_argument("--buildable-format", choices=("geojson", "dxf"), action=_Once)
    create.add_argument("--buildable-layer", action=_Once)
    create.add_argument("--buildable-unit", choices=("m", "mm"), action=_Once)
    verify = sub.add_parser("verify", allow_abbrev=False)
    verify.add_argument("--package", required=True, type=Path, action=_Once)
    try:
        args = parser.parse_args(argv)
        if args.command == "verify":
            summary = verify_package(args.package)
        else:
            summary = create_package(project=args.project, geometry=args.geometry, format=args.format,
                                     area_basis=args.area_basis, floor_heights_m=args.floor_height_m,
                                     output=args.output, layer=args.layer, unit=args.unit,
                                     buildable_geometry=args.buildable_geometry, buildable_format=args.buildable_format,
                                     buildable_layer=args.buildable_layer, buildable_unit=args.buildable_unit)
    except RunError as error:
        print(f"FAIL stage={error.stage.value} code={error.code.value}")
        return 1
    except Exception:
        print("FAIL stage=arguments code=INTERNAL_ERROR")
        return 2
    print(summary.console())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
