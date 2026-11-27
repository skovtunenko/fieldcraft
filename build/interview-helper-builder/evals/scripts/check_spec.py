#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check an interview spec against eval cases C11 and C17 (hard failures) and C15 (warnings)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "skills").is_dir())
SKILL = next(ROOT.glob("skills/**/interview-helper-builder/SKILL.md")).parent
sys.path.insert(0, str(SKILL / "scripts"))
from generate_interview_helper import section_minutes, untranslated_cyrillic

POS_RANGE = (8, 12)
NEG_RANGE = (6, 10)
MAX_WORDS = 12
BRIEF_MAX = 4
DURATION_TEXT = re.compile(r"\b\d+\s*-?\s*min(?:ute)?s?\b", re.IGNORECASE)
CYRILLIC = re.compile(r"[Ѐ-ӿ]")
STOPWORDS = {
    "about", "after", "answer", "before", "being", "candidate", "could", "every",
    "their", "there", "these", "those", "which", "while", "would", "whether",
    "should", "other", "where", "without", "within",
}


def cyrillic_paths(node: Any, path: str = "$") -> list[str]:
    if isinstance(node, str):
        return [path] if CYRILLIC.search(node) else []
    if isinstance(node, dict):
        found = [f"{path} (key {k!r})" for k in node if CYRILLIC.search(str(k))]
        for k, v in node.items():
            found += cyrillic_paths(v, f"{path}.{k}")
        return found
    if isinstance(node, list):
        return [p for i, v in enumerate(node) for p in cyrillic_paths(v, f"{path}[{i}]")]
    return []


def stems(text: str) -> set[str]:
    # ponytail: 5-letter prefix match stands in for stemming; swap for a real stemmer if warnings get noisy.
    words = re.findall(r"[a-z]+", text.lower())
    return {w[:5] for w in words if len(w) >= 5 and w not in STOPWORDS}


def joins_two_clauses(signal: str) -> bool:
    # ponytail: heuristic, flags " and " with 3+ words on its right and no list comma before it.
    for m in re.finditer(r"(?<!,) and ", signal):
        if len(signal[m.end():].split()) >= 3 and len(signal[: m.start()].split()) >= 2:
            return True
    return False


def check(spec: Any) -> tuple[list[str], list[str], int]:
    failures: list[str] = []
    warnings: list[str] = []
    if not isinstance(spec, dict):
        return ["spec root is not a JSON object"], warnings, 0

    if untranslated_cyrillic(spec):
        for path in cyrillic_paths({key: value for key, value in spec.items() if key != "candidate"}):
            failures.append(f"Cyrillic text at {path}")

    duration = spec.get("durationMinutes")
    total = 0.0
    questions = 0
    sections = spec.get("sections")
    if not isinstance(sections, list) or not sections:
        failures.append("sections missing or empty")
        sections = []
    for s in sections:
        sid = s.get("id", "?")
        try:
            total += section_minutes(s.get("minutes"))
        except ValueError as exc:
            failures.append(f"section {sid}: {exc}")
        for q in s.get("questions") or []:
            questions += 1
            qid = q.get("id", "?")
            pos = q.get("positives") or []
            neg = q.get("negatives") or []
            if not POS_RANGE[0] <= len(pos) <= POS_RANGE[1]:
                failures.append(f"{qid}: {len(pos)} positives, expected {POS_RANGE[0]}-{POS_RANGE[1]}")
            if not NEG_RANGE[0] <= len(neg) <= NEG_RANGE[1]:
                failures.append(f"{qid}: {len(neg)} negatives, expected {NEG_RANGE[0]}-{NEG_RANGE[1]}")
            seen: set[str] = set()
            for sig in pos + neg:
                norm = " ".join(str(sig).casefold().split()).rstrip(".")
                if norm in seen:
                    failures.append(f"{qid}: duplicate signal {sig!r}")
                seen.add(norm)
                if len(str(sig).split()) > MAX_WORDS:
                    warnings.append(f"{qid}: signal over {MAX_WORDS} words: {sig!r}")
                if joins_two_clauses(str(sig)):
                    warnings.append(f"{qid}: signal may join two clauses with 'and': {sig!r}")
            signal_stems = set().union(*(stems(str(x)) for x in pos + neg)) if pos + neg else set()
            if not stems(str(q.get("purpose", ""))) & signal_stems:
                warnings.append(f"{qid} (section {sid}): no signal shares a distinctive word with its purpose")

    brief = spec.get("candidateBriefing") or []
    if len(brief) > BRIEF_MAX:
        failures.append(f"candidateBriefing has {len(brief)} items, expected at most {BRIEF_MAX}")
    for item in brief:
        if DURATION_TEXT.search(str(item)):
            failures.append(f"candidateBriefing states the duration: {item!r}")

    if not isinstance(duration, (int, float)) or isinstance(duration, bool):
        failures.append(f"durationMinutes is not a number: {duration!r}")
    elif abs(total - duration) > 0.01:
        failures.append(f"section minutes sum to {total:g}, durationMinutes is {duration}")
    return failures, warnings, questions


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_spec.py <spec.json>", file=sys.stderr)
        return 2
    try:
        spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL: cannot read spec: {exc}")
        return 1
    failures, warnings, questions = check(spec)
    for f in failures:
        print(f"FAIL: {f}")
    for w in warnings:
        print(f"WARN: {w}")
    verdict = "FAIL" if failures else "PASS"
    print(f"{verdict}: {questions} questions, {len(failures)} failures, {len(warnings)} warnings")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
