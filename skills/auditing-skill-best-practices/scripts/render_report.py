#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Render full findings JSON to Markdown and optional HTML; stdout is paths/counts only.

Usage: uv run --script render_report.py --new <target>
       uv run --script render_report.py <findings.json> [<out.md>] [--page] [--mechanical]
--mechanical runs the mechanical checker on the target, adds every rule it
decides that the findings omit, and saves the completed findings file. A rule
the findings give a status the checker contradicts is an error.
Without uv: python3 render_report.py with the same arguments (Python 3.10+,
standard library only); use python if that is the interpreter's command name.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # importing the sibling renderer must not modify the skill
import check_mechanical as checker  # noqa: E402
import render_review_page as page  # noqa: E402
from stale_scope import save_baseline  # noqa: E402


def report_labels(data: object) -> dict:
    """English report labels with the findings' translations on top; malformed ones are left for validate()."""
    given = data.get("labels") if isinstance(data, dict) else None
    given = given.get("report") if isinstance(given, dict) else None
    return {**page.english()["report"], **(given if isinstance(given, dict) else {})}


def code(value: str) -> str:
    """Keep arbitrary single-line evidence literal, including backticks and HTML."""
    fence = "`" * (max((len(m) for m in re.findall(r"`+", value)), default=0) + 1)
    return f"{fence} {value} {fence}"


def literal(value: str) -> str:
    if "\n" not in value:
        return code(value)
    fence = "`" * max(3, max((len(m) for m in re.findall(r"`+", value)), default=0) + 1)
    return f"\n\n  {fence}text\n" + "\n".join("  " + line for line in value.split("\n")) + f"\n  {fence}\n"


def counts(data: dict) -> dict:
    return {group: {status: sum(r["status"] == status for r in data["rules"] if r["id"].startswith(prefix))
                    for status in page.STATUSES} for group, prefix in (("article", "BP-"), ("other", "OS-"))}


def markdown(data: dict, known: dict, totals: dict) -> str:
    labels = report_labels(data)
    catalogue_text = page.CATALOGUES[0].read_text(encoding="utf-8")
    snapshot = re.search(r"^## Snapshot\n(.*?)(?=^## |\Z)", catalogue_text, re.M | re.S)
    if not snapshot:
        raise page.Invalid("article catalogue must have a Snapshot section")
    title = re.search(r"^- Title: (.+)$", snapshot[1], re.M)
    source = re.search(r"^- Source: <([^>]+)>", snapshot[1], re.M)
    if not title or not source:
        raise page.Invalid("article catalogue Snapshot must name its Title and Source")
    lines = [f"# {labels['title']}: {code(data['target'])}", "",
             f"{labels['source']}: [{title[1]}]({source[1]}), {labels['captured']} {data['snapshot']} · {labels['hosts']}: {code(data['hosts'])}", ""]
    lines.append(" · ".join(f"{labels[group]}: ✅ {totals[group]['pass']} · ❌ {totals[group]['fail']} · n/a {totals[group]['n/a']}"
                            for group in ("article", "other")))
    verdicts = {rule["id"]: rule for rule in data["rules"]}
    for group, prefix in (("article", "BP-"), ("other", "OS-")):
        lines += ["", f"## {labels[group]}", ""]
        failures = [f for f in data["failures"] if f["rule"].startswith(prefix)]
        if not failures:
            lines.append(labels["none"])
        for level in page.LEVELS:
            selected = [f for f in failures if known[f["rule"]]["level"] == level]
            if not selected:
                continue
            lines += ["", f"### {level}", ""]
            for failure in selected:
                rid = failure["rule"]
                url = verdicts[rid].get("source", known[rid]["sources"][0])
                lines += [f"- **{rid} {known[rid]['title']}** — {code(failure['location'])} · [{labels['source']}]({url})",
                          f"  {labels['why']}: {literal(failure['why'])}",
                          f"  {labels['evidence']}: {literal(failure['evidence'])}"]
                if "reviewer_reason" in failure:
                    lines.append(f"  {labels['rejected']}: {literal(failure['reviewer_reason'])}")
                    continue
                where = f" {labels['in']} {code(failure['fix_location'])}" if "fix_location" in failure else ""
                label = f"{labels['fix']}{where}"
                if "fix_ref" in failure:
                    lines.append(f"  {label}: {labels['same']} {failure['fix_ref']}")
                    continue
                if "range" in failure:
                    lines.append(f"  {label}: {code(failure['range'])} — {literal(failure['fix'])}")
                elif "fix" in failure:
                    lines.append(f"  {label}: {literal(failure['fix'])}")
                else:
                    lines.append(f"  {label}:")
                if "before" in failure:
                    lines += [f"  {labels['before']}: {literal(failure['before'])}",
                              f"  {labels['after']}: {literal(failure['after'])}"]
    if data.get("not_evaluated"):
        lines += ["", f"## {labels['unavailable']}", ""]
        lines += [f"- {item['rule']} — {literal(item['reason'])}" for item in data["not_evaluated"]]
    return "\n".join(lines).rstrip() + "\n"


def add_script_verdicts(data: dict, known: dict) -> None:
    """Complete data["rules"] with the rules the checker decides; malformed findings are left for validate()."""
    if not (isinstance(data, dict) and page.text(data.get("target")) and isinstance(data.get("rules"), list)):
        return
    try:
        rules, _, skipped = checker.audit(Path(data["target"]).expanduser())
    except (checker.UsageError, OSError) as error:
        raise page.Invalid(f"--mechanical: {error}") from error
    labels = report_labels(data)
    base = page.english()["report"]
    reasons = {base[key]: labels[key] for key in base if key.startswith("na_")}  # the checker gives its n/a reasons in English
    written = {r.get("id"): r for r in data["rules"] if isinstance(r, dict)}
    notes = data.get("not_evaluated", [])
    for rid, rule in rules.items():
        if rid in written:
            if written[rid].get("status") != rule["status"]:
                raise page.Invalid(f"rules: {rid} has status {written[rid].get('status')!r}, but the script decided "
                                   f"{rule['status']!r}; the script's status is binding")
            continue
        first = rule["findings"][0] if rule["findings"] else None
        evidence = f"{first['file']}{':%d' % first['line'] if first['line'] else ''} {first['message']}" if first else labels["script"]
        data["rules"].append({"id": rid, "status": rule["status"], "evidence": evidence})
        unread = "; ".join(f"{item['file']}: {item['reason']}" for item in rule.get("not_evaluated", []))
        if unread and isinstance(notes, list) and not any(isinstance(n, dict) and n.get("rule") == rid for n in notes):
            notes.append({"rule": rid, "reason": unread})
            data["not_evaluated"] = notes
    for rid, reason in skipped.items():
        if rid not in written:  # the model may judge one itself, e.g. with an evaluation location the user named
            data["rules"].append({"id": rid, "status": "n/a", "evidence": reasons.get(reason, reason)})
    order = {rid: n for n, rid in enumerate(known)}
    data["rules"].sort(key=lambda r: order.get(r.get("id"), len(order)) if isinstance(r, dict) else len(order))


def outside(path: Path, target: Path) -> None:
    for root, name in ((target, "the audited skill"), (page.SKILL_DIR, "the auditing-skill-best-practices skill directory")):
        if page.inside(path, root):
            raise page.Invalid(f"refused: {path} is inside {name} ({root})")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("findings", nargs="?")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--new", metavar="TARGET")
    parser.add_argument("--page", action="store_true")
    parser.add_argument("--mechanical", action="store_true")
    args = parser.parse_args(argv[1:])
    try:
        if args.new:
            if args.findings or args.output or args.page or args.mechanical:
                raise page.Invalid("--new cannot be combined with findings, output, --page, or --mechanical")
            outside(page.temp_dir().resolve(), Path(args.new).expanduser().resolve())
            print(page.new_findings_path(args.new))
            return 0
        if not args.findings:
            raise page.Invalid("expected <findings.json> and optional <out.md> and --page")
        findings = Path(args.findings).expanduser().resolve()
        data = json.loads(findings.read_text(encoding="utf-8"))
        known = page.catalogue()
        if args.mechanical:
            add_script_verdicts(data, known)
        errors = page.validate(data, known)
        if errors:
            raise page.Invalid("\n".join(errors))
        target = Path(data["target"]).expanduser().resolve()
        outside(findings, target)
        if args.mechanical:  # the saved file is the full snapshot the page, a page-only request, and a re-audit read
            findings.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        out = (Path(args.output).expanduser() if args.output else page.temp_dir() / (findings.stem + ".md")).resolve()
        outside(out, target)
        if out.suffix.lower() != ".md" or not out.parent.is_dir():
            raise page.Invalid(f"refused: {out} must end in .md and its folder must exist")
        totals = counts(data)
        report = markdown(data, known, totals)
        html = out.with_suffix(".html")
        if args.page:
            with contextlib.redirect_stdout(io.StringIO()):
                result = page.main(["render_review_page.py", str(findings), str(html)])
            if result:
                return result
        out.write_text(report, encoding="utf-8")
        save_baseline(target, findings)
    except (page.Invalid, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"render_report: {error}", file=sys.stderr)
        return 2
    summary = {"counts": totals, "findings": str(findings), "report": str(out)}
    if args.page:
        summary["page"] = str(html)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
