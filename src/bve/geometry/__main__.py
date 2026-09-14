"""Independent geometry CLI; stdout/stderr never contain input values or paths."""
import argparse
from pathlib import Path

from .dxf import read_dxf
from .errors import Code, GeometryError
from .export import write_outputs
from .geojson import MAX_INPUT_BYTES, read_geojson


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise GeometryError(Code.INVALID_ARGUMENTS)


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(prog="python -m bve.geometry", allow_abbrev=False,
                     description="Validate local XY geometry; only explicit output files contain coordinates.")
    parser.add_argument("input", help="local input file")
    parser.add_argument("--format", required=True, choices=("geojson", "dxf"))
    parser.add_argument("--layer", help="DXF boundary layer")
    parser.add_argument("--unit", choices=("m", "mm"), help="DXF unknown-unit override only")
    parser.add_argument("--output", type=Path, help="new normalized GeoJSON file")
    parser.add_argument("--summary", type=Path, help="new summary JSON file")
    try:
        args = parser.parse_args(argv)
        if args.format == "geojson" and (args.layer is not None or args.unit is not None):
            raise GeometryError(Code.INVALID_ARGUMENTS)
        try:
            with Path(args.input).open("rb") as source:
                payload = source.read(MAX_INPUT_BYTES + 1)
        except (OSError, ValueError):
            raise GeometryError(Code.IO_ERROR) from None
        site = (read_geojson(payload) if args.format == "geojson" else
                read_dxf(payload, layer=args.layer, unit_override=args.unit))
        write_outputs(site, output=args.output, summary=args.summary)
    except GeometryError as error:
        print(f"FAIL code={error.code.value}")
        return 2 if error.code in (Code.INVALID_ARGUMENTS, Code.IO_ERROR, Code.OUTPUT_EXISTS) else 1
    print(f"PASS code=VALID warnings={len(site.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
