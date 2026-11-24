# Usage arguments for mise tasks

Official contracts checked on 2026-10-26: [mise task arguments](https://mise.jdx.dev/tasks/task-arguments.html), [Usage arg](https://usage.jdx.dev/spec/reference/arg), and [Usage flag](https://usage.jdx.dev/spec/reference/flag). Verify features against the installed mise build, which embeds its own Usage support; the latest standalone Usage documentation is not proof of compatibility. The Python example below was verified on mise 2026.11.3 on 2026-11-07, including parser and data-error cases.

## Declare the interface once

Use `#USAGE` comments in a file task and the `usage` field in a TOML task. Both describe the same interface. mise parses the input and provides help/completions; a separate Usage CLI is not required. Prefer these to legacy `arg()`/`flag()`/`option()` templates or a new handwritten parser. [Task arguments](https://mise.jdx.dev/tasks/task-arguments.html)

```bash
#!/usr/bin/env bash
#MISE description="Count newline characters in a readable text file"
#USAGE arg "<file>" help="Readable file, relative to the task working directory"
#USAGE flag "--format <format>" help="Output representation" default="count" {
#USAGE   choices "count" "summary"
#USAGE }
set -euo pipefail

input=${usage_file:?Input file is required}
[[ -f "$input" && -r "$input" ]] || {
  printf 'error: not a readable file: %s\n' "$input" >&2
  exit 1
}
count=$(wc -l < "$input")
count=${count//[[:space:]]/}
case "${usage_format?}" in
  count) printf '%s\n' "$count" ;;
  summary) printf '%s: %s newline characters\n' "$input" "$count" ;;
  *) printf 'error: unsupported format\n' >&2; exit 1 ;;
esac
```

This example changes no files; stdout is its result. A final unterminated line is not a newline character. It illustrates the interface, not a task that every workspace needs.

## Python through uv

When Python is the selected task language, the same declarations work in a file task run by `uv`. Inline script metadata declares interpreter requirements and dependencies next to the code, so the task needs no project environment:

```py
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
# MISE description="Summarize one numeric column of a CSV file"
# USAGE arg "<file>" help="Readable CSV file with a header row, relative to the mise.toml directory"
# USAGE arg "<column>" help="Header name of a numeric column"
# USAGE flag "--decimals <n>" default="2" help="Rounding, integer 0-6" {
# USAGE   arg "<n>" validate="int(value) >= 0 && int(value) <= 6" validate_error="must be an integer from 0 to 6"
# USAGE }
# USAGE flag "--format <format>" default="text" help="Output representation" {
# USAGE   choices "text" "json"
# USAGE }
"""Print count, min, max, and mean of a CSV column; stdout is the result, nothing is written."""

import csv
import json
import math
import os
import pathlib
import statistics
import sys

path = pathlib.Path(os.environ["usage_file"])
column = os.environ["usage_column"]
decimals = int(os.environ["usage_decimals"])  # parser already enforced 0-6

if not path.is_file():
    sys.exit(f"error: not a readable file: {path}")
with path.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    if column not in (reader.fieldnames or []):
        sys.exit(
            f"error: no column {column!r}; columns: {', '.join(reader.fieldnames or [])}"
        )
    values = []
    for row in reader:
        cell = row[column]
        location = f"line {reader.line_num}, column {column!r}"
        if cell is None:
            sys.exit(f"error: missing cell at {location}; supply the missing CSV field")
        if not cell.strip():
            continue
        try:
            value = float(cell)
        except ValueError:
            sys.exit(f"error: not numeric at {location}: {cell!r}; supply a finite number")
        if not math.isfinite(value):
            sys.exit(f"error: not finite at {location}: {cell!r}; supply a finite number")
        values.append(value)
if not values:
    sys.exit(f"error: column {column!r} has no values")

stats = {
    "count": len(values),
    "min": round(min(values), decimals),
    "max": round(max(values), decimals),
    "mean": round(statistics.fmean(values), decimals),
}
if os.environ["usage_format"] == "json":
    print(json.dumps(stats, allow_nan=False))
else:
    print("\n".join(f"{k}\t{v}" for k, v in stats.items()))
print(f"Summarized {len(values)} values from {path}", file=sys.stderr)
```

- mise rejects a missing `<column>`, `--decimals 9`, and `--format xml` before the script starts; the script checks only what the parser cannot know: the file, the column, and numeric content.
- Blank selected cells are excluded. A missing selected field, a nonnumeric value, or a non-finite value fails with its line and column on stderr and no stdout result. JSON serialization also rejects non-finite statistics.
- Write the markers as `# MISE` and `# USAGE`: mise accepts the space, and Python formatters such as Ruff insert it into `#MISE`.
- Every `usage_*` value is a string. Index `os.environ` for required values and values with a default; use `os.environ.get` for optional ones without a default; a boolean flag is the string `"true"` when passed. Split a variadic value with `shlex.split`, which matches the parser's shell quoting.
- JavaScript, TypeScript, and Go tasks use `//MISE` and `//USAGE`.

## Common declarations

| Declaration | Contract |
| --- | --- |
| `arg "<input>"` | Required positional input. |
| `arg "[input]"` | Optional positional input; unset when omitted without a default. |
| `flag "--dry-run"` | Boolean; true when passed, otherwise unset without a default. The script must actually implement the preview. |
| `flag "-o --output <file>" required=#true` | Required value-taking flag. |
| `default="summary"`, `env="REPORT_FORMAT"` | Fallback value/environment; CLI wins over environment, then default. |
| `choices "count" "summary"` | Allowed values shown in help/completion and enforced by parsing. |
| `help="…"`, `long_help="…"` | Short/extended user-facing documentation. |
| `arg "<files>" var=#true` | Multiple values, with optional `var_min`/`var_max` bounds. |

KDL boolean literals are `#true`/`#false`. Keep defaults consistent with choices and validation. A `--dry-run` declaration alone does not make the code safe or prevent effects. [Argument contract](https://usage.jdx.dev/spec/reference/arg), [flag contract](https://usage.jdx.dev/spec/reference/flag)

## Semantic types and constraints

Usage values are strings. The argument name `<file>` helps filename completion; it does not prove a readable file exists. Document the semantic type and enforce actual conditions. Use runtime preflight for filesystem existence/readability, relationships to outputs, and other stateful checks.

Current Usage supports boolean validation expressions over `value`, for example:

```kdl
arg "<port>" validate="int(value) >= 1 && int(value) <= 65535" validate_error="must be a valid port"
```

Value-flag validation belongs on its nested argument:

```bash
#USAGE flag "--port <port>" {
#USAGE   arg "<port>" validate="int(value) >= 1 && int(value) <= 65535" validate_error="must be a valid port"
#USAGE }
```

The current arg/flag contracts document constraints rather than a universal `type="integer"` or `type="file"` field. Check rather than invent a type property. A conversion error such as `int("abc")` can produce an expression diagnostic instead of the custom false-result message. Test both the wrong type and the out-of-range case. [Validation expressions](https://usage.jdx.dev/spec/reference/arg)

If the installed mise does not enforce an advanced declaration, use supported syntax plus explicit runtime validation, or propose a mise upgrade for approval. Never silently drop an input constraint to make parsing pass. Some dynamic features, including `choices env=`, have documented library feature gates. [Choices](https://usage.jdx.dev/spec/reference/arg)

## Read values safely

mise exposes `usage_<name>` variables; hyphens become underscores, so `--dry-run` maps to `usage_dry_run`. Required scalar values can use `${usage_input:?message}`. Optional flags need `${usage_dry_run:-false}` with `set -u`.

```bash
args=(--output "${usage_output:?Output is required}")
if [[ "${usage_verbose:-false}" == "true" ]]; then
  args+=(--verbose)
fi
existing-command "${usage_input:?Input is required}" "${args[@]}"
```

Treat inputs as data, preserving argument boundaries. Avoid interpolating untrusted values into Tera-generated executable code. Use a CLI's option terminator when needed and supported, or reject ambiguous flag-like operands explicitly.

Variadic values have a distinct contract: they arrive as one shell-quoted serialized string. Quoting the variable as one scalar does not reconstruct the original arguments, and unquoted expansion breaks spaces. The mise docs describe reconstruction with `eval` for parser-produced serialization; arbitrary environment or log text is not that trusted serialization. Use the documented encoding for the chosen runtime and verify round-tripping, or choose a simpler explicit interface such as a manifest file. [Reading task arguments](https://mise.jdx.dev/tasks/task-arguments.html)

## Test the interface and behavior

Check definition parsing and help first, then valid input, missing required input, invalid choices, numeric conversion/range failures, and paths containing spaces. A parser rejection should happen before task side effects. Help should describe the real interface without running the routine; inspect dynamic metadata providers before invoking help. Verify defaults and environment fallback without exposing secret values.
