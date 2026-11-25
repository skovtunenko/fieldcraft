#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Check the mechanical rules of reply-contract on saved replies.

Usage: check_reply.py [--work] REPLY.md...   (exit 1 on any violation)
       check_reply.py --self-test
--work also requires the Evidence / How I check it / Decided without me block.
"""

import re
import sys

# shortcut: FE0F is optional because "1⃣" and "1️⃣" render the same; make it strict if a host shows a difference.
KEYCAP = r"[0-9]️?⃣"
NONE_LINE = "⏸️ Nothing needed from you right now."
NEEDED = re.compile(rf"^⏩ Needed from you: ((?:{KEYCAP})+) ⤴️$")
ITEM = re.compile(rf"^((?:{KEYCAP})+)\s+\S")
WORK_LABELS = ("**Evidence**", "**How I check it**", "**Decided without me**")


def keycap_number(text: str) -> int:
    return int("".join(re.findall(r"[0-9]", text)))


def check(reply: str, work: bool = False) -> list[str]:
    lines = reply.rstrip().splitlines()
    if not lines:
        return ["empty reply"]
    last = lines[-1].strip()
    errors: list[str] = []
    match = NEEDED.match(last)
    if last == NONE_LINE:
        expected = 0
    elif match:
        expected = keycap_number(match.group(1))
    else:
        return [f"last line is not a contract line: {last!r}"]

    items = [(i, keycap_number(m.group(1))) for i, line in enumerate(lines[:-1]) if (m := ITEM.match(line))]
    numbers = [n for _, n in items]
    if numbers != list(range(1, expected + 1)):
        errors.append(f"last line says {expected} asks, items are numbered {numbers}")
    for i, n in items:
        if i == 0 or lines[i - 1].strip():
            errors.append(f"item {n} has no empty line before it")

    if work:
        positions = [reply.find(label) for label in WORK_LABELS]
        missing = [label for label, pos in zip(WORK_LABELS, positions) if pos < 0]
        if missing:
            errors.append(f"work report misses {missing}")
        elif positions != sorted(positions):
            errors.append("work report labels are out of order")
        elif items and max(positions) > reply.find(lines[items[0][0]]):
            errors.append("work report comes after the asks")
    return errors


def self_test() -> None:
    ok_none = "Answer.\n\n⏸️ Nothing needed from you right now.\n"
    ok_two = "Text.\n\n## What I need from you\n\n1️⃣ Do A, reply 'done'.\n\n2️⃣ Do B.\n\nMeanwhile I wait.\n\n⏩ Needed from you: 2️⃣ ⤴️"
    keycaps = lambda n: "".join(d + "️⃣" for d in str(n))
    ok_ten = "## Asks\n" + "".join(f"\n{keycaps(n)} Do {n}.\n" for n in range(1, 11)) + "\n⏩ Needed from you: 1️⃣0️⃣ ⤴️"
    work = "Done.\n\n**Evidence**: ran it.\n\n**How I check it**: run x.\n\n**Decided without me**: none.\n\n" + NONE_LINE
    assert check(ok_none) == [], check(ok_none)
    assert check(ok_two) == [], check(ok_two)
    assert check(ok_ten) == [], check(ok_ten)
    assert check(work, work=True) == []
    assert "last line" in check("Answer without a contract line.")[0]
    assert check(ok_two.replace("2️⃣ ⤴️", "3️⃣ ⤴️"))  # count mismatch
    assert check(ok_two.replace("\n\n2️⃣", "\n2️⃣"))  # merged paragraphs
    assert check(ok_none, work=True)  # work block missing
    assert check(ok_none.replace("right now.", "right now"))  # not verbatim
    print("check_reply self-test: ok")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    work = "--work" in argv
    paths = [a for a in argv if a != "--work"]
    if not paths:
        print(__doc__, file=sys.stderr)
        return 2
    failed = 0
    for path in paths:
        errors = check(open(path, encoding="utf-8").read(), work)
        print(f"{'PASS' if not errors else 'FAIL'} {path}")
        for error in errors:
            print(f"  - {error}")
        failed += bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
