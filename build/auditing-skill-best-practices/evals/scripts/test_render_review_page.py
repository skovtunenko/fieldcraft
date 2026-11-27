#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Tests for scripts/render_review_page.py and assets/review-page-template.html.

Usage: uv run --script evals/scripts/test_render_review_page.py

Renders evals/fixtures/review/findings-violating.json and variants into a temp
dir and asserts: markup in evidence round-trips without closing the data block,
rules gain their title, level, type, and source from the catalogues,
schema errors are reported with JSON paths, output paths inside the audited
skill or this skill (also through a symlink) are refused with nothing written,
the default output goes to $TMPDIR, zero-failure renders work, the page labels
are English unless the findings carry translated labels, which are validated, no
shipped file holds Cyrillic text, and the template loads nothing from the network. Exits 1 when any check failed.
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "skills").is_dir())
SKILL = next(ROOT.glob("skills/**/auditing-skill-best-practices/SKILL.md")).parent
SCRIPT = SKILL / "scripts" / "render_review_page.py"
TEMPLATE = SKILL / "assets" / "review-page-template.html"
LABELS = json.loads((SKILL / "assets" / "labels.json").read_text(encoding="utf-8"))
SAMPLE = Path(__file__).resolve().parents[1] / "fixtures" / "review" / "findings-violating.json"
sys.dont_write_bytecode = True  # no __pycache__ inside the shipped scripts/
sys.path.insert(0, str(SCRIPT.parent))
import render_review_page as renderer  # noqa: E402
from render_review_page import catalogue  # noqa: E402

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def render(findings: Path, out: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    args = ["uv", "run", "--quiet", "--script", str(SCRIPT), str(findings)] + ([str(out)] if out else [])
    return subprocess.run(args, capture_output=True, text=True, check=False, env=env)


def embedded(page: Path) -> dict:
    html = page.read_text(encoding="utf-8")
    block = re.search(r'<script type="application/json" id="audit-data">(.*?)</script>', html, re.DOTALL)
    return json.loads(block.group(1))


def page_labels(page: Path) -> dict:
    html = page.read_text(encoding="utf-8")
    return json.loads(re.search(r'<script type="application/json" id="page-labels">(.*?)</script>', html, re.DOTALL).group(1))


def main() -> int:
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")
    check(not re.search(r"<link\b|@import|url\(|\bsrc=|https?://(?!platform)", template.split("<script>", 1)[0])
          and "fetch(" not in template and "XMLHttpRequest" not in template,
          "template loads no external resource and makes no request")
    check(".innerHTML" not in template, "template inserts text with textContent, never innerHTML")
    cyrillic = [str(p.relative_to(SKILL)) for p in sorted(SKILL.rglob("*"))
                if p.is_file() and re.search("[\u0400-\u04ff]", p.read_bytes().decode("utf-8", "replace"))]
    check(not cyrillic, f"no shipped file holds Cyrillic text (found in {cyrillic})")
    check("var LABELS" not in template and "__PAGE_LABELS__" in template
          and 'Object.assign(JSON.parse(document.getElementById("page-labels").textContent), data.labels && data.labels.page)' in template
          and "document.documentElement.lang = data.lang;" in template,
          "template holds no language table: English labels from assets/labels.json, translated labels on top, html lang from the findings")
    check(set(LABELS) == {"page", "report"} and all(isinstance(v, str) and v for part in LABELS.values() for v in part.values())
          and all(f"L.{key}" in template for key in ("auditor", "editDraft", "saveChange", "placeholderNote", "acceptTitle")),
          "assets/labels.json holds the page and report labels as strings, and the template reads its page keys")

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw).resolve()

        def write(name: str, data: object) -> Path:
            path = tmp / name
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return path

        page = tmp / "out" / "review.html"
        page.parent.mkdir()
        result = render(SAMPLE, page)
        check(result.returncode == 0 and result.stdout.strip() == str(page) and page.is_file(),
              f"sample renders, exit 0, prints the page path (stderr: {result.stderr.strip()[:200]})")
        html = page.read_text(encoding="utf-8")
        data_block = html.split('id="audit-data">', 1)[1].split("</script>", 1)[0]
        check("<" not in data_block, "embedded JSON holds no raw '<'")
        back = embedded(page)
        known = catalogue()
        filled = [dict(r, title=known[r["id"]]["title"], level=known[r["id"]]["level"], type=known[r["id"]]["type"],
                       source=known[r["id"]]["sources"][0]) for r in sample["rules"]]
        check(back["failures"] == sample["failures"] and back["rules"] == filled,
              "embedded JSON round-trips the findings; each rule carries the catalogue's title, level, type, first source")
        check("</script><!--" in back["failures"][1]["evidence"], "`</script>` and `<!--` in evidence survive the round-trip")
        check(back["audit_id"].startswith(f"{sample['target']}|{sample['snapshot']}|{sample['audited']}|"),
              "audit_id = target|snapshot|audited|failures hash (LocalStorage key)")
        reordered = copy.deepcopy(sample)
        reordered["failures"].reverse()
        result = render(write("reordered.json", reordered), tmp / "out" / "reordered.html")
        check(result.returncode == 0 and embedded(tmp / "out" / "reordered.html")["audit_id"] != back["audit_id"],
              "a same-day re-audit with changed failures gets a new audit_id, so old marks do not carry over")
        check(html.count("__AUDIT_DATA__") == 0, "placeholder replaced")
        version = re.search(r'^\s+version:\s*"([^"]+)"', (SKILL / "SKILL.md").read_text(encoding="utf-8"), re.MULTILINE).group(1)
        check(back.get("skill_version") == version and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} [+-]\d{2}:\d{2}", back.get("generated", "")),
              f"page is stamped with the generation time and skill version {version} (got {back.get('generated')}, {back.get('skill_version')})")
        check("auditor" not in back, "a findings file without auditor still renders")
        named = dict(sample, auditor="Opus 5.5 in Claude Code $&")
        result = render(write("auditor.json", named), tmp / "out" / "auditor.html")
        check(result.returncode == 0 and embedded(tmp / "out" / "auditor.html").get("auditor") == named["auditor"]
              and "fact(L.auditor, " in template and LABELS["page"]["auditor"] == "Auditor",
              "auditor round-trips and the header facts name it")
        result = render(write("auditor-empty.json", dict(sample, auditor=" ")), tmp / "out" / "auditor-empty.html")
        check(result.returncode == 2 and "auditor: optional" in result.stderr and not (tmp / "out" / "auditor-empty.html").exists(),
              "an empty auditor exits 2 naming auditor, nothing written")
        check('http-equiv="Content-Security-Policy"' in template and "connect-src 'none'" in template,
              "template carries a CSP that blocks network access")

        check(page_labels(page) == LABELS["page"] and "labels" not in back,
              "without labels the page embeds the English page labels of assets/labels.json")
        ru = copy.deepcopy(sample)
        ru["lang"] = "ru"
        ru["labels"] = {"page": {"accept": "Принять", "progress": "Просмотрено {n} из {m}"},  # test data: a Russian override
                        "report": {"article": "Правила статьи"}}
        second = known["BP-04"]["sources"][1]
        next(r for r in ru["rules"] if r["id"] == "BP-04")["source"] = second
        result = render(write("ru.json", ru), tmp / "out" / "ru.html")
        page_ru = embedded(tmp / "out" / "ru.html") if result.returncode == 0 else {}
        check(page_ru.get("lang") == "ru" and page_ru.get("labels") == ru["labels"]
              and page_labels(tmp / "out" / "ru.html") == LABELS["page"],
              f"translated labels reach the page beside the English ones (stderr: {result.stderr.strip()[:200]})")
        check(any(r["id"] == "BP-04" and r["source"] == second for r in page_ru.get("rules", [])),
              "an explicit source from the rule's Source links replaces the first one")
        de = copy.deepcopy(sample)
        de["lang"] = "de"
        check(render(write("de.json", de), tmp / "out" / "de.html").returncode == 0, "another lang without labels renders (EN labels)")
        bad_labels = copy.deepcopy(sample)
        bad_labels["labels"] = {"page": {"nope": "x", "accept": 3, "progress": "{n} reviewed", "copy": ""},
                                "report": [], "extra": {}}
        result = render(write("bad-labels.json", bad_labels), tmp / "out" / "bad-labels.html")
        missing = [e for e in ("labels.extra: unknown field", "labels.page.nope: unknown label", "labels.page.accept: expected a non-empty string",
                               "labels.page.copy: expected a non-empty string", "labels.page.progress: must keep the tokens",
                               "labels.report: expected an object") if e not in result.stderr]
        check(result.returncode == 2 and not missing and not (tmp / "out" / "bad-labels.html").exists(),
              f"labels: unknown parts and keys, non-strings, and changed tokens exit 2 with JSON paths (missing: {missing})")
        result = render(write("labels-list.json", dict(sample, labels=[])), tmp / "out" / "labels-list.html")
        check(result.returncode == 2 and "labels: optional, an object" in result.stderr, "labels that is not an object exits 2")

        zero = copy.deepcopy(sample)
        for rule in zero["rules"]:
            if rule["status"] == "fail":
                rule["status"] = "pass"
        zero["failures"] = []
        result = render(write("zero.json", zero), tmp / "out" / "zero.html")
        check(result.returncode == 0 and embedded(tmp / "out" / "zero.html")["failures"] == []
              and "noFailures" in template, "zero-failure audit renders the No failures state")

        env = dict(os.environ, TMPDIR=str(tmp / "out"))
        result = render(SAMPLE, env=env)
        default = tmp / "out" / "findings-violating.html"
        check(result.returncode == 0 and result.stdout.strip() == str(default) and default.is_file(),
              "without a page path the page goes to $TMPDIR/<findings file name>.html")
        first, second = (subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPT), "--new", str(tmp / "skills" / "violating")],
                                        capture_output=True, text=True, check=False, env=env) for _ in range(2))
        paths = [Path(r.stdout.strip()) for r in (first, second)]
        check(first.returncode == 0 == second.returncode and paths[0] != paths[1]
              and all(p.parent == tmp / "out" and re.fullmatch(r"skill-audit-violating-\d{8}-\d{6}(-\d+)?\.json", p.name)
                      and p.is_file() and p.stat().st_size == 0 for p in paths),
              f"--new creates a fresh empty findings file per call (got {[p.name for p in paths]})")
        os.environ["TMPDIR"] = str(tmp / "same-second")
        (tmp / "same-second").mkdir()
        renderer.datetime = type("Frozen", (), {"now": staticmethod(lambda: datetime(2026, 10, 19, 10, 0, 0))})
        names = [renderer.new_findings_path(str(tmp / "violating")).name for _ in range(3)]
        check(names == ["skill-audit-violating-20261019-100000.json", "skill-audit-violating-20261019-100000-2.json",
                        "skill-audit-violating-20261019-100000-3.json"],
              f"three --new calls in one second get -2 and -3, never a shared file (got {names})")

        broken = copy.deepcopy(sample)
        del broken["hosts"]
        broken["extra"] = 1
        broken["rules"][0]["level"] = "high"
        broken["rules"][1]["source"] = "javascript:alert(1)"
        broken["failures"][0]["why"] = ""
        broken["failures"][1].pop("after")
        broken["failures"][4].pop("fix")
        broken["failures"].append({"rule": "BP-01", "location": "SKILL.md", "why": "x", "evidence": "y", "fix": "z"})
        broken["failures"] = [f for f in broken["failures"] if f["rule"] != "BP-52"]
        at = {f["rule"]: n for n, f in enumerate(broken["failures"])}
        out = tmp / "out" / "broken.html"
        result = render(write("broken.json", broken), out)
        expected = ["hosts: required", "extra: unknown field", "rules[0].level:", "rules[1].source:", "failures[0].why:",
                    "failures[1]: give before and after together", "failures[4].fix: required", f'failures[{at["BP-01"]}].rule: "BP-01"',
                    "rule BP-52 has status fail but no failure entry"]
        missing = [e for e in expected if e not in result.stderr]
        check(result.returncode == 2 and not missing and not out.exists(),
              f"schema errors: exit 2, each named with its JSON path, nothing written (missing: {missing})")
        typed = copy.deepcopy(sample)
        typed["rules"][0]["id"] = {"x": 1}
        typed["failures"][0]["rule"] = ["BP-07"]
        typed["failures"][1]["fix"] = 3
        typed["failures"][3]["before"] = ["a"]  # BP-26, a plain text edit
        result = render(write("typed.json", typed), tmp / "out" / "typed.html")
        missing = [e for e in ("rules[0].id:", 'failures[0].rule: ["BP-07"]', "failures[1].fix: optional, a string",
                               "failures[3].before/after:") if e not in result.stderr]
        check(result.returncode == 2 and "Traceback" not in result.stderr and not missing,
              f"wrong JSON types: exit 2 with JSON paths, no traceback (missing: {missing})")
        forms = copy.deepcopy(sample)
        idx = {f["rule"]: n for n, f in enumerate(forms["failures"])}
        forms["failures"][idx["BP-05"]]["fix_ref"] = "BP-99"
        forms["failures"][idx["BP-17"]]["before"] = "x"
        forms["failures"][idx["BP-55"]]["placeholders"] = ["<host>"]
        forms["failures"][idx["BP-53"]].pop("fix")
        forms["failures"][idx["BP-21"]]["fix_location"] = ""
        result = render(write("forms.json", forms), tmp / "out" / "forms.html")
        missing = [e for e in (f'failures[{idx["BP-05"]}].fix_ref: "BP-99"', f'failures[{idx["BP-17"]}].before: not allowed with fix_ref',
                               f"failures[{idx['BP-55']}].placeholders: '<host>' does not occur",
                               f"failures[{idx['BP-53']}].fix: required with range", f"failures[{idx['BP-21']}].fix_location:")
                   if e not in result.stderr]
        check(result.returncode == 2 and not missing, f"fix_ref, range, placeholders, fix_location are validated (missing: {missing})")
        prior = copy.deepcopy(sample)
        idx = {f["rule"]: n for n, f in enumerate(prior["failures"])}
        prior["failures"][idx["BP-26"]]["reviewer_reason"] = " "
        prior["failures"][idx["BP-43"]]["reviewer_reason"] = "Constants here are self-explanatory."
        for k in ("before", "after", "fix", "fix_location", "range", "placeholders"):
            prior["failures"][idx["BP-43"]].pop(k, None)  # no fix left to accept: refused
        result = render(write("prior.json", prior), tmp / "out" / "prior.html")
        missing = [e for e in (f"failures[{idx['BP-26']}].reviewer_reason: optional", f"failures[{idx['BP-43']}].fix: required")
                   if e not in result.stderr]
        check(result.returncode == 2 and not missing, f"reviewer_reason: non-empty, and its fix still required (missing: {missing})")
        prior = copy.deepcopy(sample)
        prior["failures"][idx["BP-43"]]["reviewer_reason"] = "Constants here are self-explanatory."  # beside its own fix
        prior["failures"][idx["BP-05"]]["reviewer_reason"] = "No reason given"  # beside fix_ref
        result = render(write("prior-ok.json", prior), tmp / "out" / "prior-ok.html")
        check(result.returncode == 0, f"reviewer_reason renders beside a fix and beside fix_ref (stderr: {result.stderr.strip()})")
        cat = copy.deepcopy(sample)
        rid = {r["id"]: n for n, r in enumerate(cat["rules"])}
        cat["rules"][rid["BP-03"]]["source"] = "https://example.com/page#x"
        cat["rules"][rid["BP-04"]]["title"] = "Something else"
        cat["rules"][rid["BP-02"]]["id"] = "BP-99"
        idx = {f["rule"]: n for n, f in enumerate(cat["failures"])}
        cat["failures"].append(copy.deepcopy(cat["failures"][idx["BP-07"]]))
        result = render(write("catalogue.json", cat), tmp / "out" / "catalogue.html")
        missing = [e for e in (f"rules[{rid['BP-03']}].source: optional, but not one of",
                               f"rules[{rid['BP-04']}].title: unknown field", "BP-99 is not a rule of either catalogue",
                               "rules: BP-02 is missing", f"failures[{idx['BP-05']}].fix_ref: BP-07 has 2 fixes")
                   if e not in result.stderr]
        check(result.returncode == 2 and not missing,
              f"rules are checked against both catalogues, title is not a rule field; an ambiguous fix_ref is refused (missing: {missing})")
        check("does not occur exactly once" in template, "export tells the agent to stop on a Before that is not found exactly once")
        check(all(k in template for k in ("fix_ref", "fix_location", "placeholders", "Resolves: ", "first changed span", 'el("mark"')),
              "template shows shared edits, fix location, ranges, and highlights placeholders")
        check("A new audit requires a separate explicit request from the user." in template
              and "Offer to rerun the audit on request." in template
              and "Run the auditing-skill-best-practices skill on " not in template,
              "export offers a re-audit, then stops and requires a separate user request")
        check(all(k in template for k in ("apply the fixes from the bottom up", "rename it after every other fix",
                                          "naming its new path if a fix renamed the folder", "var value=reviewHasSaved(e)?e.edited:base")),
              "export orders line-based fixes bottom-up, renames the folder last, and an edited large edit keeps its first span")
        check("exportArea.value = state.instruction" in template and "state.instruction = null" in template,
              "a hand-edited instruction is saved with the marks and cleared by Rebuild")
        bad = tmp / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        result = render(bad, tmp / "out" / "bad.html")
        check(result.returncode == 2 and "not valid JSON" in result.stderr, "invalid JSON: exit 2 with the reason")

        target = tmp / "audited" / "my-skill"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("---\nname: my-skill\n---\n", encoding="utf-8")
        inside = copy.deepcopy(sample)
        inside["target"] = str(target)
        findings = write("inside.json", inside)
        before = sorted(p.name for p in target.rglob("*"))
        result = render(findings, target / "review.html")
        check(result.returncode == 2 and "inside the audited skill" in result.stderr and not (target / "review.html").exists(),
              "a page path inside the audited skill is refused, nothing written")
        (tmp / "link").symlink_to(target, target_is_directory=True)
        result = render(findings, tmp / "link" / "review.html")
        check(result.returncode == 2 and "inside the audited skill" in result.stderr and sorted(p.name for p in target.rglob("*")) == before,
              "a page path reaching the audited skill through a symlink is refused, nothing written")
        result = render(findings, SKILL / "assets" / "review.html")
        check(result.returncode == 2 and "auditing-skill-best-practices skill directory" in result.stderr
              and not (SKILL / "assets" / "review.html").exists(), "a page path inside this skill's directory is refused")
        result = render(findings, tmp / "out" / "review.txt")
        check(result.returncode == 2 and "must end in .html" in result.stderr, "a page path without .html is refused")
        result = render(findings, tmp / "missing" / "review.html")
        check(result.returncode == 2 and "does not exist" in result.stderr, "a page path in a missing folder is refused")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPT)], capture_output=True, text=True, check=False)
        check(result.returncode == 2 and "usage:" in result.stderr, "no argument: exit 2 with usage")

    print(f"\n{'FAILED' if FAILURES else 'PASSED'}: {len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
