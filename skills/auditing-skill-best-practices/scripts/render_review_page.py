#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Render the offline review page of one audit from its findings JSON.

Usage:
    python3 render_review_page.py --new <target>
    python3 render_review_page.py <findings.json> [<out.html>]

--new creates an empty, never-used findings file,
$TMPDIR/skill-audit-<target folder>-<YYYYMMDD-HHMMSS>.json (with -2, -3, ...
when that name exists), and prints its path, so parallel audits and repeated
pages never share a file.

<findings.json> follows the schema in references/review-page.md. The script
validates it, embeds it and the English page labels of assets/labels.json in
assets/review-page-template.html with every "<"
written as \\u003c (so text such as "</script>" cannot close the data block),
and writes one HTML file. Default output: $TMPDIR/<findings file name without .json>.html.
It refuses an output path whose resolved real path lies inside the audited
skill ("target" in the JSON) or inside this skill's own directory, and then
writes nothing.

Exit 0: prints the absolute path of the written page on stdout. Exit 2: usage,
validation, or path error; every problem is printed on stderr, one per line,
with its JSON path (such as "failures[2].why: ...").
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_DIR / "assets" / "review-page-template.html"
PLACEHOLDER = "__AUDIT_DATA__"
LABELS = SKILL_DIR / "assets" / "labels.json"
LABELS_PLACEHOLDER = "__PAGE_LABELS__"
TOKEN = re.compile(r"\{[a-z]\}")
CATALOGUES = (SKILL_DIR / "references" / "best-practices-rules.md", SKILL_DIR / "references" / "other-official-sources.md")
RULE_HEADING = re.compile(r"^### ((?:BP|OS)-\d\d) — (.+)$")

LEVELS = ("must", "should", "consider")
TYPES = ("mechanical", "judgment")
STATUSES = ("pass", "fail", "n/a")
RULE_ID = re.compile(r"^(?:BP|OS)-\d\d$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOP_KEYS = {"schema", "lang", "target", "snapshot", "audited", "hosts", "auditor", "labels", "rules", "failures",
            "not_evaluated"}
RULE_KEYS = {"id", "status", "evidence", "source"}  # title, level, type: filled from the catalogue
FAILURE_KEYS = {"rule", "location", "why", "evidence", "before", "after", "fix", "fix_location", "fix_ref", "range",
                "placeholders", "reviewer_reason"}
EDIT_KEYS = ("before", "after", "fix", "fix_location", "range", "placeholders")  # absent on a fix_ref entry
RANGE = re.compile(r"^\S.*:\d+(?:-\d+)?$")


class Invalid(Exception):
    pass


def text(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def catalogue() -> dict[str, dict]:
    """Every live rule of both catalogues: {id: {title, type, level, sources}}."""
    rules: dict[str, dict] = {}
    for path in CATALOGUES:
        try:
            live = path.read_text(encoding="utf-8").split("\n## Retired rules", 1)[0]
        except (OSError, UnicodeDecodeError) as error:
            raise Invalid(f"cannot read the catalogue {path}: {error}") from error
        current: dict = {}
        for line in live.splitlines():
            heading = RULE_HEADING.match(line)
            if heading:
                current = rules[heading.group(1)] = {"title": heading.group(2), "sources": []}
            elif current and line.startswith("Type: "):
                fields = dict(part.split(": ", 1) for part in line.split(" · ") if ": " in part)
                current["type"], current["level"] = fields.get("Type"), fields.get("Level")
            elif current and line.startswith("Source: "):
                current["sources"] = re.findall(r"<(https://[^>]+)>", line)
    bad = [rid for rid, e in rules.items() if e.get("level") not in LEVELS or e.get("type") not in TYPES or not e["sources"]]
    if bad:
        raise Invalid(f"catalogue rules without a valid Type/Level line or a Source link: {', '.join(bad)}")
    return rules


def english() -> dict[str, dict[str, str]]:
    """The English labels: {"page": {key: text}, "report": {key: text}}."""
    try:
        return json.loads(LABELS.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Invalid(f"cannot read the labels {LABELS}: {error}") from error


def check_labels(labels: object) -> list[str]:
    """Problems of the optional translated labels; a key they leave out stays English."""
    base = english()
    if not isinstance(labels, dict):
        return ["labels: optional, an object with page and report label maps"]
    errors = [f"labels.{k}: unknown field; allowed: {', '.join(sorted(base))}" for k in sorted(set(labels) - set(base))]
    for part in sorted(set(labels) & set(base)):
        if not isinstance(labels[part], dict):
            errors.append(f"labels.{part}: expected an object of label strings")
            continue
        for key, value in labels[part].items():
            at = f"labels.{part}.{key}"
            if key not in base[part]:
                errors.append(f"{at}: unknown label; use a key of assets/labels.json")
            elif not text(value):
                errors.append(f"{at}: expected a non-empty string")
            elif sorted(TOKEN.findall(value)) != sorted(TOKEN.findall(base[part][key])):
                errors.append(f"{at}: must keep the tokens of the English label {base[part][key]!r}")
    return errors


def validate(data: object, known: dict[str, dict]) -> list[str]:
    """Return every schema problem, each prefixed with its JSON path; an empty list means valid."""
    if not isinstance(data, dict):
        return ["(top level): expected a JSON object"]
    errors = [f"{k}: unknown field; allowed: {', '.join(sorted(TOP_KEYS))}" for k in sorted(set(data) - TOP_KEYS)]
    if data.get("schema") != 1:
        errors.append("schema: required, the number 1")
    for key in ("lang", "target", "hosts"):
        if not text(data.get(key)):
            errors.append(f"{key}: required, a non-empty string")
    for key in ("snapshot", "audited"):
        if not (isinstance(data.get(key), str) and DATE.match(data[key])):
            errors.append(f"{key}: required, a date as YYYY-MM-DD")
    if "auditor" in data and not text(data["auditor"]):  # optional, so findings files from before it still render
        errors.append("auditor: optional, the model and harness as a non-empty string")
    if "labels" in data:
        errors += check_labels(data["labels"])

    rules = data.get("rules")
    status: dict[str, str] = {}
    if not (isinstance(rules, list) and rules):
        errors.append("rules: required, a non-empty list with one entry per catalogue rule")
        rules = []
    for n, rule in enumerate(rules):
        at = f"rules[{n}]"
        if not isinstance(rule, dict):
            errors.append(f"{at}: expected an object")
            continue
        errors += [f"{at}.{k}: unknown field; allowed: {', '.join(sorted(RULE_KEYS))}" for k in sorted(set(rule) - RULE_KEYS)]
        rid = rule.get("id")
        if not (isinstance(rid, str) and RULE_ID.match(rid)):
            errors.append(f"{at}.id: required, BP-NN or OS-NN")
        elif rid in status:
            errors.append(f"{at}.id: {rid} appears twice")
        if not text(rule.get("evidence")):
            errors.append(f"{at}.evidence: required, a non-empty string")
        if rule.get("status") not in STATUSES:
            errors.append(f"{at}.status: required, one of {', '.join(STATUSES)}")
        if isinstance(rid, str):
            status.setdefault(rid, rule.get("status"))
        entry = known.get(rid) if isinstance(rid, str) else None
        if isinstance(rid, str) and RULE_ID.match(rid) and entry is None:
            errors.append(f"{at}.id: {rid} is not a rule of either catalogue")
        elif entry and "source" in rule and rule["source"] not in entry["sources"]:
            errors.append(f"{at}.source: optional, but not one of the rule's Source links: {', '.join(entry['sources'])}")
    errors += [f"rules: {rid} is missing; every catalogue rule needs one entry" for rid in sorted(set(known) - set(status))]

    unavailable = data.get("not_evaluated", [])
    if not isinstance(unavailable, list):
        errors.append("not_evaluated: optional, a list of rule/reason objects")
        unavailable = []
    seen: set[str] = set()
    for n, item in enumerate(unavailable):
        at = f"not_evaluated[{n}]"
        if not isinstance(item, dict):
            errors.append(f"{at}: expected a rule/reason object")
            continue
        errors += [f"{at}.{key}: unknown field" for key in sorted(set(item) - {"rule", "reason"})]
        rid = item.get("rule")
        if not isinstance(rid, str) or rid not in known or status.get(rid) not in ("fail", "n/a"):
            errors.append(f"{at}.rule: required, a known rule with status fail or n/a")
        elif rid in seen:
            errors.append(f"{at}.rule: {rid} appears twice; combine its reasons")
        else:
            seen.add(rid)
        if not text(item.get("reason")):
            errors.append(f"{at}.reason: required, a non-empty string")

    failures = data.get("failures")
    if not isinstance(failures, list):
        errors.append("failures: required, a list (empty when no rule failed)")
        failures = []
    covered: set[str] = set()
    owners: dict[str, int] = {}  # rule -> failure entries that carry their own fix
    refs: list[tuple[str, str, object]] = []
    for n, item in enumerate(failures):
        at = f"failures[{n}]"
        if not isinstance(item, dict):
            errors.append(f"{at}: expected an object")
            continue
        errors += [f"{at}.{k}: unknown field; allowed: {', '.join(sorted(FAILURE_KEYS))}" for k in sorted(set(item) - FAILURE_KEYS)]
        rid = item.get("rule")
        if not isinstance(rid, str) or status.get(rid) != "fail":
            errors.append(f"{at}.rule: {json.dumps(rid)} is not a rule with status fail in rules")
            rid = None
        covered.add(rid)
        for key in ("location", "why", "evidence"):
            if not text(item.get(key)):
                errors.append(f"{at}.{key}: required, a non-empty string")
        # rejected in an earlier round: the page starts it rejected, and its fix stays so the reviewer can still accept it
        if "reviewer_reason" in item and not text(item["reviewer_reason"]):
            errors.append(f"{at}.reviewer_reason: optional, the reviewer's reason as a non-empty string")
        if "fix_ref" in item:
            refs.append((at, rid, item["fix_ref"]))
            errors += [f"{at}.{k}: not allowed with fix_ref; the referenced entry holds the edit" for k in EDIT_KEYS if k in item]
            continue
        owners[rid] = owners.get(rid, 0) + 1
        before, after, fix = item.get("before"), item.get("after"), item.get("fix")
        if fix is not None and not isinstance(fix, str):
            errors.append(f"{at}.fix: optional, a string")
            fix = None
        if (before is None) != (after is None):
            errors.append(f"{at}: give before and after together (a text edit), or neither (a structural fix)")
        elif before is not None and not (isinstance(before, str) and isinstance(after, str) and before != after):
            errors.append(f"{at}.before/after: strings that differ; before is the exact current text")
            before = after = None
        elif before is None and not text(fix):
            errors.append(f"{at}.fix: required when there is no before/after, a non-empty string")
        if "fix_location" in item and not text(item["fix_location"]):
            errors.append(f"{at}.fix_location: optional, a non-empty string such as SKILL.md:17")
        if "range" in item:
            if not (isinstance(item["range"], str) and RANGE.match(item["range"])):
                errors.append(f"{at}.range: optional, an exact line range such as SKILL.md:21-520")
            if not text(fix):
                errors.append(f"{at}.fix: required with range, the concrete step for those lines")
        if "placeholders" in item:
            marks = item["placeholders"]
            if not (isinstance(marks, list) and marks and all(text(m) for m in marks)):
                errors.append(f"{at}.placeholders: optional, a non-empty list of strings such as \"<server>\"")
            else:
                shown = (after if isinstance(after, str) else "") + (fix or "")
                errors += [f"{at}.placeholders: {m!r} does not occur in after or fix" for m in marks if m not in shown]
    for at, rid, ref in refs:
        if not (isinstance(ref, str) and ref in owners) or ref == rid:
            errors.append(f"{at}.fix_ref: {json.dumps(ref)} must name another rule whose failure entry holds the edit")
        elif owners[ref] > 1:
            errors.append(f"{at}.fix_ref: {ref} has {owners[ref]} fixes of its own, so the reference is ambiguous; "
                          "point at a rule with one fix")
    for rid in sorted(r for r, s in status.items() if s == "fail" and r not in covered):
        errors.append(f"failures: rule {rid} has status fail but no failure entry")
    return errors


def skill_version() -> str:
    """This skill's metadata.version, stamped on the page so a reviewer knows which release built it."""
    try:
        match = re.search(r'^\s+version:\s*"([^"]+)"', (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"), re.MULTILINE)
    except (OSError, UnicodeDecodeError):
        match = None
    return match.group(1) if match else "unknown"


def inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def temp_dir() -> Path:
    return Path(os.environ.get("TMPDIR") or tempfile.gettempdir())


def new_findings_path(target: str) -> Path:
    """Create and return a findings file no other run uses; exclusive create, so two runs never get the same one."""
    stem = f"skill-audit-{Path(target).expanduser().resolve().name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    for n in itertools.count(1):  # ends at the first free name
        path = temp_dir() / (stem + (f"-{n}" if n > 1 else "") + ".json")
        try:
            with path.open("x", encoding="utf-8"):
                return path
        except FileExistsError:
            continue
        except OSError as error:
            raise Invalid(f"cannot create {path}: {error}") from error


def main(argv: list[str]) -> int:
    try:
        if len(argv) == 3 and argv[1] == "--new":
            print(new_findings_path(argv[2]))
            return 0
        if len(argv) not in (2, 3):
            raise Invalid("expected <findings.json> and an optional <out.html>")
        try:
            data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as error:
            raise Invalid(f"cannot read {argv[1]}: {error}") from error
        except json.JSONDecodeError as error:
            raise Invalid(f"{argv[1]} is not valid JSON: {error}") from error
        known = catalogue()
        errors = validate(data, known)
        if errors:
            raise Invalid("\n".join(errors))
        for rule in data["rules"]:  # the catalogue is the only copy of these; the page reads them from each rule
            entry = known[rule["id"]]
            rule.update(title=entry["title"], level=entry["level"], type=entry["type"],
                        source=rule.get("source", entry["sources"][0]))
        target = Path(data["target"]).expanduser().resolve()
        if len(argv) == 3:
            out = Path(argv[2]).expanduser()
        else:
            out = temp_dir() / (Path(argv[1]).stem + ".html")  # one page per findings file, so a re-render never overwrites another audit
        out = out.resolve()  # real path: a symlinked folder cannot smuggle the page into a protected directory
        for root, what in ((target, "the audited skill"), (SKILL_DIR, "the auditing-skill-best-practices skill directory")):
            if inside(out, root):
                raise Invalid(f"refused: {out} is inside {what} ({root}); name an output path outside it")
        if out.suffix.lower() != ".html":
            raise Invalid(f"refused: {out} must end in .html")
        if not out.parent.is_dir():
            raise Invalid(f"refused: folder {out.parent} does not exist")
        try:
            template = TEMPLATE.read_text(encoding="utf-8")
        except OSError as error:
            raise Invalid(f"cannot read the template {TEMPLATE}: {error}") from error
        for mark in (PLACEHOLDER, LABELS_PLACEHOLDER):
            if template.count(mark) != 1:
                raise Invalid(f"template {TEMPLATE} must hold {mark} exactly once")
        # Marks are stored per failure position: a hash of the failures makes changed fixes start unmarked.
        digest = hashlib.sha256(json.dumps(data["failures"], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]  # 64 bits: enough to tell audits apart, short enough to read
        data["audit_id"] = f"{data['target']}|{data['snapshot']}|{data['audited']}|{digest}"
        stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")
        data["generated"] = stamp[:-2] + ":" + stamp[-2:]  # +HH:MM, as the interview pages write it
        data["skill_version"] = skill_version()
        embedded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
        labels = json.dumps(english()["page"], ensure_ascii=False).replace("<", "\\u003c")
        page = template.replace(LABELS_PLACEHOLDER, labels).replace(PLACEHOLDER, embedded)  # labels first: data may hold either mark
        try:
            out.write_text(page, encoding="utf-8")
        except OSError as error:
            raise Invalid(f"cannot write {out}: {error}") from error
    except Invalid as error:
        print(f"render_review_page: {error}\nusage: python3 render_review_page.py --new <target> | <findings.json> [<out.html>]",
              file=sys.stderr)
        return 2
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
