#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Print the catalogue text an audit of one skill needs: the rules left to judgment.

Usage:
    judgment_rules.py <skill-dir>

Prints, for both catalogues, the Snapshot and Terms sections and then every
judgment rule that the mechanical checker did not already decide as n/a for
<skill-dir>, each rule block verbatim. The first line names the rules left
out and who decides them. Reads files only.

Exit 0 on success; 2 on a usage error, with the reason on stderr.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # importing the sibling checker must not modify the skill
import check_mechanical as checker  # noqa: E402

CATALOGUES = [Path(__file__).resolve().parents[1] / "references" / name
              for name in ("best-practices-rules.md", "other-official-sources.md")]
WHOLE = ("## Snapshot", "## Terms")  # sections printed in full; a rule section prints only its kept rules
RULE = re.compile(r"^### ((?:BP|OS)-\d\d) ")


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 2:
            raise checker.UsageError("expected exactly one argument: the path to a skill directory")
        root = Path(argv[1])
        if not (root / "SKILL.md").is_file():
            raise checker.UsageError(f"no SKILL.md in {root}; pass the directory that holds the skill's SKILL.md")
        mechanical, _, skipped = checker.audit(root)
        texts = [path.read_text(encoding="utf-8") for path in CATALOGUES]
    except (checker.UsageError, OSError, UnicodeDecodeError) as error:
        print(f"judgment_rules: {error}\nusage: judgment_rules.py <skill-dir>", file=sys.stderr)
        return 2
    out: list[str] = []
    for path, text in zip(CATALOGUES, texts):
        out.append(f"# {path.name}\n")
        judged = set(re.findall(r"^### ((?:BP|OS)-\d\d) .*\n\nType: judgment", text, re.MULTILINE)) - set(skipped)
        keep = False
        for line in text.splitlines():
            rule = RULE.match(line)
            if line.startswith("## "):
                keep = line in WHOLE
            elif rule:
                keep = rule.group(1) in judged
            if keep:
                out.append(line)
    print(f"Left out, decided by scripts: mechanical {', '.join(mechanical)}; "
          f"not applicable {', '.join(f'{k} ({v})' for k, v in skipped.items()) or 'none'}.\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
