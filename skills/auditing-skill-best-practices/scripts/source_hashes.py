#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Download the catalogues' source documents and compare them with stored hashes.

Usage:
    source_hashes.py <download-dir> [--offline] [--print-table] [--table <file>]

Reads the table in references/source-hashes.md (or --table), saves every
source into <download-dir> under its File name, and prints one JSON object:

    {"all_unchanged": false,
     "changed": ["skills.md"], "unreachable": [], "unchanged": [...],
     "sources": [{"file", "url", "mode", "status", "sha256", "error"}]}

status is "unchanged", "changed", "unreachable" (with error), or "fetched"
(mode "none": saved for later steps, never compared). all_unchanged is true
only when every compared source is unchanged and none is unreachable.

--offline      hash the files already in <download-dir>; fetch nothing.
--print-table  print the table with live hashes instead of JSON; a row that
               could not be read keeps its stored hash.

Modes: "bytes" hashes the file as served; "text" hashes the visible text and
element ids of an HTML page's <article>, because the page's markup differs
between fetches; "none" stores no hash.

Exit 0 when the comparison ran, whatever it found; 2 on a usage error or a
malformed table, with the reason on stderr.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_TABLE = Path(__file__).resolve().parent.parent / "references" / "source-hashes.md"
FILE_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MODES = ("bytes", "text", "none")
MAX_BYTES = 20 * 1024 * 1024
HEADER = "| File | URL | Mode | sha256 |"
USER_AGENT = "Mozilla/5.0 (source-hashes)"


class ArticleText(HTMLParser):
    """Visible text and ids inside <article>; the whole page when it has none."""

    def __init__(self) -> None:
        super().__init__()
        self.depth = 0  # nesting inside <article>
        self.skip = 0  # nesting inside <script>/<style>
        self.inside: list[str] = []
        self.everything: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag == "article":
            self.depth += 1
        ident = dict(attrs).get("id")
        if ident:
            self._add(f"#{ident}")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag == "article" and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if not self.skip:
            self._add(data)

    def _add(self, piece: str) -> None:
        self.everything.append(piece)
        if self.depth:
            self.inside.append(piece)

    def text(self) -> str:
        return " ".join(" ".join(self.inside or self.everything).split())


def digest(data: bytes, mode: str) -> str:
    if mode == "text":
        parser = ArticleText()
        parser.feed(data.decode("utf-8", errors="replace"))
        data = parser.text().encode()
    return hashlib.sha256(data).hexdigest()


def fail(message: str) -> None:
    print(f"source_hashes: {message}", file=sys.stderr)
    raise SystemExit(2)


def read_table(path: Path) -> tuple[list[str], list[dict]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        fail(f"cannot read the table {path}: {error}")
    if HEADER not in lines:
        fail(f"{path} has no table headed '{HEADER}'")
    rows, seen = [], set()
    for number, line in enumerate(lines[lines.index(HEADER) + 2:], lines.index(HEADER) + 3):
        if not line.startswith("|"):
            break
        cells = [cell.strip().strip("`<>") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            fail(f"{path}:{number}: expected 4 cells, found {len(cells)}")
        name, url, mode, stored = cells
        if not FILE_NAME.match(name) or name in seen:
            fail(f"{path}:{number}: File '{name}' is not a unique lowercase file name")
        if not url.startswith("https://"):
            fail(f"{path}:{number}: URL must start with https://")
        if mode not in MODES:
            fail(f"{path}:{number}: Mode must be one of {', '.join(MODES)}")
        if (mode == "none") != (stored == "—") or (mode != "none" and not SHA256.match(stored)):
            fail(f"{path}:{number}: sha256 must be 64 hex digits, or — for mode none")
        seen.add(name)
        rows.append({"file": name, "url": url, "mode": mode, "stored": stored})
    if not rows:
        fail(f"{path}: the table has no rows")
    return lines, rows


def fetch(url: str) -> bytes:
    """curl first (it retries and detects a truncated body); urllib when curl is absent or fails."""
    errors = []
    curl = shutil.which("curl")
    if curl:
        done = subprocess.run(
            [curl, "-fsSL", "--retry", "3", "--retry-all-errors", "--max-time", "90",
             "--max-filesize", str(MAX_BYTES), "-A", USER_AGENT, "--", url],
            capture_output=True, check=False)
        if done.returncode == 0 and done.stdout.strip():
            return done.stdout
        errors.append(f"curl exit {done.returncode}: {done.stderr.decode(errors='replace').strip()[:200]}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for _ in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                # read() to EOF: read(n) returns short on chunked responses, and a
                # truncated body would hash as a false "changed"
                data = response.read()
            if len(data) > MAX_BYTES:
                raise ValueError(f"larger than {MAX_BYTES} bytes")
            if not data.strip():
                raise ValueError("empty response")
            return data
        except Exception as error:  # noqa: BLE001 - every failure means unreachable
            last = f"{type(error).__name__}: {error}"
    errors.append(last)
    raise RuntimeError("; ".join(errors))


def main(argv: list[str]) -> int:
    flags = {"--offline": False, "--print-table": False}
    table, positional = DEFAULT_TABLE, []
    arguments = iter(argv)
    for argument in arguments:
        if argument in flags:
            flags[argument] = True
        elif argument == "--table":
            table = Path(next(arguments, "") or fail("--table needs a file"))
        elif argument.startswith("-"):
            fail(f"unknown option {argument}; see the usage in refresh.md")
        else:
            positional.append(argument)
    if len(positional) != 1:
        fail("usage: source_hashes.py <download-dir> [--offline] [--print-table] [--table <file>]")
    directory = Path(positional[0])
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        fail(f"cannot create {directory}: {error}")

    lines, rows = read_table(table)
    for row in rows:
        target = directory / row["file"]
        try:
            if flags["--offline"]:
                data = target.read_bytes()
                if not data.strip():
                    raise ValueError("empty file")
            else:
                data = fetch(row["url"])
                target.write_bytes(data)
        except Exception as error:  # noqa: BLE001
            row.update(status="unreachable", sha256=None, error=str(error))
            continue
        if row["mode"] == "none":
            row.update(status="fetched", sha256=None, error=None)
            continue
        live = digest(data, row["mode"])
        row.update(status="unchanged" if live == row["stored"] else "changed", sha256=live, error=None)

    if flags["--print-table"]:
        start = lines.index(HEADER)
        print("\n".join(lines[start:start + 2]))
        for row in rows:
            print(f"| `{row['file']}` | <{row['url']}> | {row['mode']} | {row['sha256'] or row['stored']} |")
        return 0

    def names(status: str) -> list[str]:
        return [row["file"] for row in rows if row["status"] == status]

    print(json.dumps({
        "all_unchanged": not names("changed") and not names("unreachable"),
        "changed": names("changed"),
        "unreachable": names("unreachable"),
        "unchanged": names("unchanged"),
        "sources": [{key: row[key] for key in ("file", "url", "mode", "status", "sha256", "error")} for row in rows],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
