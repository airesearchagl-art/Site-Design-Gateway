"""Run ``python -m bve FILE``; output only a result and error count."""

from pathlib import Path
import sys

from .validation import MAX_INPUT_BYTES, validate_json


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print("FAIL errors=1")
        return 2
    try:
        with Path(arguments[0]).open("rb") as source:
            payload = source.read(MAX_INPUT_BYTES + 1)
    except (OSError, ValueError):
        print("FAIL errors=1")
        return 2
    result = validate_json(payload)
    print(f"{'PASS' if result.valid else 'FAIL'} errors={result.error_count}")
    if result.code == "schema_unavailable":
        return 2
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
