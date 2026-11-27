#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check a JSON value mapping against a list of form field names.

Usage: python3 check_fields.py <fields.txt> <values.json>
Prints one line per unknown field and exits 1 when any is found; exits 2,
with the reason on stderr, when an input cannot be read or is not a JSON object.
"""

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check_fields.py <fields.txt> <values.json>", file=sys.stderr)
        return 2
    try:
        lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
        fields = [line.strip() for line in lines if line.strip()]
        values = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"cannot read input: {error}", file=sys.stderr)
        return 2
    if not isinstance(values, dict):
        print(f"values must be a JSON object of field name to value, got {type(values).__name__}", file=sys.stderr)
        return 2
    problems = [f"unknown field {key!r}; valid fields: {', '.join(fields)}" for key in values if key not in fields]
    print("\n".join(problems) or "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
