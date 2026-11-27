#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Print the H2 to H4 headings of a Markdown file, or the heading ids of an HTML page.

Usage:
    python3 headings.py <md-file>
    python3 headings.py --ids <html-file>

Markdown: prints one line per heading, such as "H3 Concise is key". Fences
follow CommonMark: a fence opens with three or more backticks or tildes, and
only a line of the same character, at least as long, closes it, so a ``` block
nested inside a ```` block stays code.

--ids: prints one line per h2 to h4 element whose id is a slug (lowercase
words joined by hyphens), in page order, such as "H3 solve-dont-punt".
Generated ids such as "_R_pl4plb_" are skipped.

Exit 0 on success; 2 on a usage error or when the file cannot be read, with
the reason on stderr.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")  # CommonMark: 4+ spaces of indent make an indented code line, not a fence
HEADING = re.compile(r"^ {0,3}(#{2,4})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class HeadingIds(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.found: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        anchor = dict(attrs).get("id") or ""
        if tag in ("h2", "h3", "h4") and SLUG.match(anchor):
            self.found.append(f"H{tag[1]} {anchor}")


def headings(text: str) -> list[str]:
    found: list[str] = []
    fence = ""  # the open fence's marker, empty outside code
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) and not match.group(2).strip():
                fence = ""
            continue
        if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
            fence = match.group(1)
            continue
        heading = HEADING.match(line)
        if heading:
            found.append(f"H{len(heading.group(1))} {heading.group(2)}")
    return found


def main(argv: list[str]) -> int:
    ids = len(argv) == 3 and argv[1] == "--ids"
    if len(argv) != 2 and not ids:
        print("usage: python3 headings.py <md-file> | --ids <html-file>", file=sys.stderr)
        return 2
    try:
        text = Path(argv[-1]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"headings: cannot read {argv[-1]}: {error}", file=sys.stderr)
        return 2
    if ids:
        parser = HeadingIds()
        parser.feed(text)
        print("\n".join(parser.found))
    else:
        print("\n".join(headings(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
