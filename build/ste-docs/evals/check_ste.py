#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Check the countable STE rules of ste-docs on a Markdown document.

Usage: check_ste.py DOC.md...   (exit 1 on any violation)
       check_ste.py --self-test
Limits: 20 words per sentence in numbered steps, 25 elsewhere;
6 sentences per paragraph; no claim of STE compliance.
Prints sentence statistics so a with-skill run can be compared to a baseline.
"""

import re
import sys

STEP = re.compile(r"^\s*\d+[.)]\s+")
BULLET = re.compile(r"^\s*[-*+]\s+")
COMPLIANCE = re.compile(r"STE[- ]compliant|compliant with (ASD-)?STE", re.I)
# shortcut: splits on . ! ? followed by space; abbreviations such as "e.g." split early, which only shortens counts.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def blocks(text: str) -> list[tuple[str, str]]:
    """Return (kind, text) for prose: kind is step, bullet, or paragraph."""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^\1", "", text, flags=re.S | re.M)
    text = re.sub(r"`[^`]*`", "CODE", text)
    result: list[tuple[str, str]] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            result.append(("paragraph", " ".join(paragraph)))
            paragraph.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|", ">", "<!--")):
            flush()
        elif STEP.match(line):
            flush()
            item = STEP.sub("", line)
            # shortcut: a numbered item that opens with a bold label is a list of options, not a step; judge others by hand.
            result.append(("bullet" if item.startswith("**") else "step", item))
        elif BULLET.match(line):
            flush()
            result.append(("bullet", BULLET.sub("", line)))
        elif result and result[-1][0] != "paragraph" and not paragraph and line.startswith(" "):
            kind, prev = result.pop()  # continuation line of a list item
            result.append((kind, f"{prev} {stripped}"))
        else:
            paragraph.append(stripped)
    flush()
    return result


def check(text: str) -> tuple[list[str], dict]:
    errors: list[str] = []
    lengths: list[int] = []
    for kind, block in blocks(text):
        sentences = [s for s in SENTENCE_END.split(block) if s.strip()]
        limit = 20 if kind == "step" else 25
        for sentence in sentences:
            words = len(sentence.split())
            lengths.append(words)
            if words > limit:
                errors.append(f"{kind} sentence has {words} words (max {limit}): {sentence[:70]}…")
        if kind == "paragraph" and len(sentences) > 6:
            errors.append(f"paragraph has {len(sentences)} sentences (max 6): {block[:70]}…")
    if COMPLIANCE.search(text):
        errors.append("claims STE compliance; the skill allows only 'STE style'")
    stats = {
        "sentences": len(lengths),
        "max_words": max(lengths, default=0),
        "mean_words": round(sum(lengths) / len(lengths), 1) if lengths else 0,
    }
    return errors, stats


def self_test() -> None:
    good = "---\ntitle: x\n---\n# ADR\n\nThe cache stores results. It uses Redis.\n\n1. Stop the service.\n2. Start the service.\n\n```text\n" + "word " * 40 + "\n```\n"
    errors, stats = check(good)
    assert errors == [] and stats["sentences"] == 4, (errors, stats)
    long_step = "1. " + "word " * 21 + "end."
    assert "step sentence has 22" in check(long_step)[0][0]
    assert check("1. **Buy a service.** " + "word " * 20 + "end.")[0] == [], "labelled option, 25-word limit"
    long_desc = "- " + "word " * 25 + "end."
    assert "bullet sentence has 26" in check(long_desc)[0][0]
    assert check("- " + "word " * 24 + "end.")[0] == []
    seven = " ".join(["One short sentence."] * 7)
    assert "7 sentences" in check(seven)[0][0]
    assert check("This document is STE-compliant.")[0]
    wrapped = "- short start\n  " + "word " * 30 + "end."
    assert check(wrapped)[0], "continuation lines belong to the list item"
    print("check_ste self-test: ok")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    failed = 0
    for path in argv:
        errors, stats = check(open(path, encoding="utf-8").read())
        print(f"{'PASS' if not errors else 'FAIL'} {path} {stats}")
        for error in errors:
            print(f"  - {error}")
        failed += bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
