#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Mechanical tests for scripts/check_mechanical.py.

Usage: uv run --script evals/scripts/test_check_mechanical.py

Copies each fixture to a temp dir (renaming SKILL.md.fixture to SKILL.md, so the
repo's own skill checks never see the fixtures as skills; the compliant fixture
goes into a folder named after its skill, as OS-02 requires), runs the checker,
and asserts expected statuses. Also checks usage errors, read-only behaviour,
frontmatter edge cases, both catalogues' structure and source anchors, and that
the script decides exactly the mechanical rule IDs of both catalogues. Exits 1
after all checks when any failed.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "skills").is_dir())
SKILL = next(ROOT.glob("skills/**/auditing-skill-best-practices/SKILL.md")).parent
SCRIPT = SKILL / "scripts" / "check_mechanical.py"
HEADINGS = SKILL / "scripts" / "headings.py"
CATALOGUE = SKILL / "references" / "best-practices-rules.md"
OS_CATALOGUE = SKILL / "references" / "other-official-sources.md"
ARTICLE = "https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices"
CHECKLIST_ROWS = {44, 45, 46, 47}  # article-headings rows that map checklist items, not Section citations
HOSTS = {"all", "Claude Code", "API", "claude.ai", "plugins"}
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

EXPECTED = {
    "compliant": {
        "BP-04": "pass", "BP-05": "pass", "BP-06": "pass", "BP-07": "pass",
        "BP-08": "pass", "BP-09": "pass", "BP-10": "pass",
        "BP-17": "pass", "BP-21": "pass", "BP-22": "n/a", "BP-39": "pass",
        "BP-40": "pass",
        "OS-01": "pass", "OS-02": "pass", "OS-03": "pass", "OS-04": "pass",
        "OS-06": "n/a", "OS-08": "n/a", "OS-11": "pass",
    },
    "violating": {
        "BP-04": "pass", "BP-05": "fail", "BP-06": "pass", "BP-07": "fail",
        "BP-08": "pass", "BP-09": "fail", "BP-10": "fail",
        "BP-17": "fail", "BP-21": "fail", "BP-22": "fail", "BP-39": "fail",
        "BP-40": "fail",
        "OS-01": "pass", "OS-02": "fail", "OS-03": "fail", "OS-04": "pass",
        "OS-06": "n/a", "OS-08": "n/a", "OS-11": "fail",
    },
}
BROKEN_LINK = "See [the form rules](form-rules.md) for field limits.\n"  # OS-11 target, line 123 of basics.md
FOLDER = {"compliant": "filling-pdf-forms", "violating": "violating"}
# Findings that must point at a specific file (and line, when given).
EXPECTED_FINDINGS = {
    "violating": [
        ("BP-21", "references/doc2.md", None),
        ("BP-22", "references/basics.md", 1),
        ("BP-39", "scripts/unused_helper.py", None),
        ("BP-40", "SKILL.md", 15),
        ("OS-02", "SKILL.md", 2),
        ("OS-03", "SKILL.md", 3),
        ("OS-11", "references/basics.md", 123),
    ],
}

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def run(target: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "--quiet", "--script", str(SCRIPT), str(target)],
        capture_output=True, text=True, check=False,
    )


def digest(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        h.update(str(path.relative_to(root)).encode())
        if path.is_file():
            h.update(path.read_bytes())
    return h.hexdigest()


def run_rules(target: Path) -> dict:
    return json.loads(run(target).stdout)["rules"]


def materialize(fixture: str, tmp: Path) -> Path:
    target = tmp / FOLDER[fixture]
    shutil.copytree(FIXTURES / fixture, target)
    (target / "SKILL.md.fixture").rename(target / "SKILL.md")
    if fixture == "violating":  # the broken link lives only in the copy, so the repo's link checker never sees it
        with (target / "references" / "basics.md").open("a", encoding="utf-8") as handle:
            handle.write(BROKEN_LINK)
    return target


def skill(tmp: Path, label: str, text: str) -> dict:
    target = tmp / label
    target.mkdir()
    (target / "SKILL.md").write_text(text, encoding="utf-8")
    result = run(target)
    check(result.returncode == 0, f"{label}: exit 0")
    return json.loads(result.stdout)["rules"]


def check_os_catalogue() -> set[str]:
    """Structure of the OS catalogue; returns its mechanical rule IDs."""
    text = OS_CATALOGUE.read_text(encoding="utf-8")
    ids = re.findall(r"^### (OS-\d\d)\b", text, re.MULTILINE)
    check(ids == [f"OS-{n:02d}" for n in range(1, len(ids) + 1)], f"OS IDs are contiguous OS-01..OS-{len(ids):02d}")
    check(12 <= len(ids) <= 18, f"OS catalogue holds 12 to 18 rules (got {len(ids)})")
    blocks = re.split(r"^### ", text, flags=re.MULTILINE)[1:len(ids) + 1]
    meta = [re.search(r"^Type: (mechanical|judgment) · Level: (must|should|consider) · Applies to: .+ · Hosts: (.+)$", b, re.MULTILINE)
            for b in blocks]
    check(all(meta), "every OS rule has one type, level, applies-to, and Hosts")
    hosts_ok = all(m and set(h.strip() for h in m.group(3).split(",")) <= HOSTS for m in meta)
    check(hosts_ok, "every OS rule's Hosts uses only all, Claude Code, API, claude.ai, plugins")
    sources = [re.search(r"^Source: (.+)$", b, re.MULTILINE) for b in blocks]
    check(all(s and all(re.fullmatch(r"<https://[^>#]+#[^>]+>", x.strip()) for x in s.group(1).split(";")) for s in sources),
          "every OS rule has Source links of the form <https://...#anchor>")
    check(all(re.search(r"^- Why: ", b, re.MULTILINE) for b in blocks), "every OS rule has a Why line")
    mechanical = {i for i, m in zip(ids, meta) if m and m.group(1) == "mechanical"}
    count = {k: sum(1 for m in meta if m and k in m.groups()) for k in ("mechanical", "judgment", "must", "should", "consider")}
    stated = (f"- Rules: {len(ids)} (OS-01 to OS-{len(ids):02d}); {count['mechanical']} mechanical, {count['judgment']} judgment; "
              f"levels: {count['must']} must,\n  {count['should']} should, {count['consider']} consider")
    check(stated in text, "OS Snapshot counts match its rules")
    listed = set(re.findall(r"OS-\d\d", text.split("- Mechanical rules:", 1)[1].split("decides exactly", 1)[0]))
    check(listed == mechanical, "OS mechanical-rule list matches the Type lines")
    return mechanical


def main() -> int:
    catalogue = CATALOGUE.read_text(encoding="utf-8")
    mechanical = set(re.findall(r"^### (BP-\d\d)\b.*\n\nType: mechanical", catalogue, re.MULTILINE))
    all_ids = re.findall(r"^### (BP-\d\d)\b", catalogue, re.MULTILINE)
    check(sorted(all_ids) == [f"BP-{n:02d}" for n in range(1, len(all_ids) + 1)] and len(set(all_ids)) == len(all_ids),
          f"catalogue IDs are unique and contiguous BP-01..BP-{len(all_ids):02d}")
    types = re.findall(r"^Type: (mechanical|judgment) · Level: (must|should|consider) · Applies to: ", catalogue, re.MULTILINE)
    check(len(types) == len(all_ids), "every rule has one type, one level, applies-to")
    count = {k: sum(1 for t in types if k in t) for k in ("mechanical", "judgment", "must", "should", "consider")}
    stated = (f"- Rules: {len(all_ids)} (BP-01 to BP-{len(all_ids):02d}); {count['mechanical']} mechanical, "
              f"{count['judgment']} judgment; levels: {count['must']} must,\n  {count['should']} should, {count['consider']} consider")
    check(stated in catalogue, "catalogue Snapshot counts match its rules")
    listed = set(re.findall(r"BP-\d\d", catalogue.split("- Mechanical rules:", 1)[1].split("decides exactly", 1)[0]))
    check(listed == mechanical, "catalogue mechanical-rule list matches the Type lines")
    headings = (SKILL / "references" / "article-headings.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\d+) \| H[234] \| (.*?) \| `([a-z0-9-]+)` \| (.*?) \|$", headings, re.MULTILINE)
    check(len(rows) == 48 and [int(r[0]) for r in rows] == list(range(1, 49)), "article-headings.md keeps 48 headings, each with an anchor")
    anchor = {h: a for _, h, a, _ in rows}

    def expand(cell: str) -> set[str]:
        return set(re.findall(r"BP-\d\d", cell)) | {f"BP-{i:02d}" for a, b in re.findall(r"BP-(\d\d) to BP-(\d\d)", cell)
                                                    for i in range(int(a), int(b) + 1)}
    column = {h: expand(c) for _, h, _, c in rows}
    cited = re.findall(r"^### (BP-\d\d)\b.*\n\nType: .*· Section: (.*)\n\nSource: (.*)$", catalogue, re.MULTILINE)
    check(len(cited) == len(all_ids), f"every BP rule has a Source line right after its Type line ({len(cited)} of {len(all_ids)})")
    missing = [(rid, h.strip()) for rid, sec, _ in cited for h in sec.split(";") if rid not in column.get(h.strip(), set())]
    check(not missing, f"article-headings Rules column covers every rule's Section field (missing: {missing})")
    sections = {rid: {h.strip() for h in sec.split(";")} for rid, sec, _ in cited}
    drift = [(h, rid) for n, h, _, c in rows if int(n) not in CHECKLIST_ROWS for rid in expand(c) if h not in sections.get(rid, set())]
    check(not drift, f"article-headings rows outside the checklist list only rules that cite them (drift: {drift})")
    wrong = [rid for rid, sec, src in cited
             if src != "; ".join(f"<{ARTICLE}#{anchor.get(h.strip(), '?')}>" for h in sec.split(";"))]
    check(not wrong, f"each BP Source line links the stored anchor of every Section heading, in order (wrong: {wrong})")
    check(all("solve-dont-punt" in src for rid, sec, src in cited if "Solve, don't defer" in sec),
          "rules under \"Solve, don't defer\" link #solve-dont-punt, the page's real id")
    check(next(s for r, s, _ in cited if r == "BP-18").startswith("Progressive disclosure patterns"),
          "BP-18 cites its parent section Progressive disclosure patterns")
    mechanical |= check_os_catalogue()

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        for fixture, expected in EXPECTED.items():
            target = materialize(fixture, tmp)
            before = digest(target)
            result = run(target)
            check(result.returncode == 0 and result.stderr == "", f"{fixture}: exit 0, nothing on stderr, JSON only on stdout")
            rules = json.loads(result.stdout)["rules"]
            check(set(rules) == mechanical, f"{fixture}: script rule IDs equal catalogue mechanical IDs")
            for rule_id, status in expected.items():
                got = rules.get(rule_id, {}).get("status")
                check(got == status, f"{fixture}: {rule_id} is {status} (got {got})")
            for rule_id, file, line in EXPECTED_FINDINGS.get(fixture, []):
                hits = [f for f in rules[rule_id]["findings"] if f["file"] == file and (line is None or f["line"] == line)]
                check(bool(hits) and all(f["fix"] for f in hits), f"{fixture}: {rule_id} finding at {file}:{line} with a fix")
            check(digest(target) == before, f"{fixture}: target unchanged after the run")

        r = skill(tmp, "long-name", f"---\nname: {'a' * 65}\ndescription: Does a thing. Use when asked.\n---\n")
        check(r["BP-04"]["status"] == "fail", "65-character name fails BP-04")
        r = skill(tmp, "newline-name", '---\nname: "abc\\n"\ndescription: Does a thing.\n---\n')
        check(r["BP-05"]["status"] == "fail", "BP-05: a name ending in a newline fails")
        r = skill(tmp, "comment-name", "---\nname: 'abc' # short name\ndescription: Does a thing. # c\n---\n")
        check(r["BP-05"]["status"] == "pass", "BP-05: a YAML inline comment after a quoted name is ignored")
        r = skill(tmp, "comparison", "---\nname: pdf-tools\ndescription: Checks that x <= 5 and y >= 3.\n---\n")
        check(r["BP-10"]["status"] == "pass", "BP-10: <= and >= are not tags")
        block = "\n".join("  " + "a" * 99 for _ in range(10)) + "\n  " + "a" * 14  # 10 x 99 + 10 breaks + 14 = 1014
        r = skill(tmp, "literal-clip", f"---\nname: pdf-tools\ndescription: |\n{block}{'a' * 10}\n---\n")
        check(r["BP-09"]["status"] == "fail", "BP-09: literal block of 1024 chars plus YAML's kept newline is 1025")
        r = skill(tmp, "literal-strip", f"---\nname: pdf-tools\ndescription: |-\n{block}{'a' * 10}\n---\n")
        check(r["BP-09"]["status"] == "pass", "BP-09: |- strips the final newline, 1024 passes")
        line = "  " + "b" * 1023
        r = skill(tmp, "folded-clip", f"---\nname: pdf-tools\ndescription: >\n{line}\n---\n")
        check(r["BP-09"]["status"] == "pass", "BP-09: folded 1023 chars plus newline is 1024")
        r = skill(tmp, "folded-over", f"---\nname: pdf-tools\ndescription: >\n{line}b\n---\n")
        check(r["BP-09"]["status"] == "fail", "BP-09: folded 1024 chars plus newline is 1025")
        r = skill(tmp, "tagged", "---\nname: pdf-<b>x</b>\ndescription: Does a thing.\n---\n")
        check(r["BP-06"]["status"] == "fail" and r["BP-05"]["status"] == "fail", "tag in name fails BP-05 and BP-06")
        r = skill(tmp, "reserved", "---\nname: claudette-tools\ndescription: Does a thing.\n---\n")
        check(r["BP-07"]["status"] == "fail", "reserved word as substring fails BP-07")
        r = skill(tmp, "no-desc", "---\nname: pdf-tools\n---\n")
        check((r["BP-08"]["status"], r["BP-09"]["status"], r["BP-10"]["status"]) == ("fail", "n/a", "n/a"),
              "missing description: BP-08 fail, BP-09 and BP-10 n/a")
        r = skill(tmp, "no-frontmatter", "# Title\n\nBody.\n")
        check(r["BP-04"]["status"] == "fail" and r["BP-05"]["status"] == "n/a", "no frontmatter: BP-04 fail, BP-05 n/a")
        folded = "\n".join("  " + "word " * 20 for _ in range(12))  # 12 lines x 99 chars + 11 spaces = 1199
        r = skill(tmp, "folded-long", f"---\nname: pdf-tools\ndescription: >-\n{folded}\n---\n")
        check(r["BP-09"]["status"] == "fail", "folded description over 1024 fails BP-09")
        folded = "\n".join("  " + "word " * 20 for _ in range(5))
        r = skill(tmp, "folded-short", f"---\nname: pdf-tools\ndescription: >-\n{folded}\nmetadata:\n  version: \"1\"\n---\n")
        check(r["BP-09"]["status"] == "pass" and r["BP-08"]["status"] == "pass", "folded description under 1024 passes")
        r = skill(tmp, "quoted", '---\nname: "pdf-tools"\ndescription: "Fills <x> forms."\n---\n')
        check(r["BP-05"]["status"] == "pass" and r["BP-10"]["status"] == "fail", "quoted scalars are unquoted")
        regex_line = "Match `\\d\\d:\\d\\dZ` and `[A-Za-z]:\\\\[\\w.-]+\\.md` in code."
        r = skill(tmp, "regex-text", f"---\nname: pdf-tools\ndescription: Does a thing.\n---\n\n{regex_line}\n")
        check(r["BP-40"]["status"] == "pass", "regex escapes are not backslash paths")
        r = skill(tmp, "recall", "---\nname: pdf-tools\ndescription: Does a thing.\n---\n\n"
                  "Run scripts\\run.rb, fill templates\\form, see assets\\t.xml.\n"
                  "Regex `[-\\d.eE]`, `\\w+\\.md`, `foo\\.md`, and HKEY_LOCAL_MACHINE\\Software.\n")
        found = sorted(f["message"] for f in r["BP-40"]["findings"])
        check(found == ["backslash path `assets\\t.xml`", "backslash path `scripts\\run.rb`", "backslash path `templates\\form`"],
              f"BP-40 catches backslash paths of any type, skips regex and registry text (got {found})")
        r = skill(tmp, "windows", "---\nname: pdf-tools\ndescription: Does a thing.\n---\n\nOpen C:\\data\\me\\form.pdf.\n")
        check(r["BP-40"]["status"] == "fail", "drive-letter path fails BP-40")
        messages = [(f["message"], f["fix"]) for f in r["BP-40"]["findings"]]
        check(messages == [("backslash path `C:\\data\\me\\form.pdf`", "Write it with forward slashes: `C:/data/me/form.pdf`.")],
              "BP-40 shows the whole path as written and its forward-slash form")
        r = skill(tmp, "renamed", "---\nname: Claude_PDF_Helper\ndescription: Does a thing.\n---\n")
        fix = r["BP-05"]["findings"][0]["fix"]
        check("a-z, 0-9, and hyphens" in fix and "`" not in fix, "BP-05 fix states the constraint and proposes no name")

        def named(label: str, text: str, folder: str = "pdf-tools") -> dict:
            (tmp / label).mkdir()
            return skill(tmp / label, folder, text)

        for i, bad_name in enumerate(("-pdf-tools", "pdf-tools-", "pdf--tools")):
            r = named(f"hyphen{i}", f"---\nname: {bad_name}\ndescription: Does a thing.\n---\n", bad_name)
            check(r["OS-01"]["status"] == "fail" and r["OS-02"]["status"] == "pass", f"OS-01 fails `{bad_name}`; OS-02 passes in a matching folder")
        r = named("folder", "---\nname: pdf-tools\ndescription: Does a thing.\n---\n", "pdf-forms")
        check(r["OS-02"]["status"] == "fail" and "pdf-forms" in r["OS-02"]["findings"][0]["message"], "OS-02 fails when name and folder differ")
        (tmp / "plugin-root" / ".claude-plugin").mkdir(parents=True)
        (tmp / "plugin-root" / ".claude-plugin" / "plugin.json").write_text("{}\n", encoding="utf-8")
        (tmp / "plugin-root" / "SKILL.md").write_text("---\nname: pdf-tools\ndescription: Does a thing.\n---\n", encoding="utf-8")
        check(run_rules(tmp / "plugin-root")["OS-02"]["status"] == "n/a", "OS-02 is n/a for SKILL.md at a plugin root")
        yaml_cases = {
            "colon": ("description: Use when: the user asks\n", "fail"),
            "colon-end": ("description: Use when:\n", "fail"),
            "colon-continuation": ("description: Does a thing\n  and more: here\n", "fail"),
            "backtick": ("description: `pdf` forms\n", "fail"),
            "unclosed": ('description: "Does a thing\n', "fail"),
            "after-quote": ('description: "Does" a thing\n', "fail"),
            "bare-line": ("description: Does a thing.\njust words\n", "fail"),
            "tab": ("description: Does a thing\n\tand more\n", "fail"),
            "duplicate": ("description: Does a thing.\ndescription: Again.\n", "fail"),
            "quoted-colon": ('description: "Use when: the user asks"\n', "pass"),
            "folded-colon": ("description: >\n  Use when: the user asks\n", "pass"),
            "comment-colon": ("description: Does a thing # note: fine\n", "pass"),
            "url": ("description: See https://example.com at 10:30.\n", "pass"),
            "indentless-list": ("description: Does a thing.\npaths:\n- src/**\n", "pass"),
        }
        for label, (body, status) in yaml_cases.items():
            r = named(f"yaml-{label}", f"---\nname: pdf-tools\n{body}---\n")
            check(r["OS-03"]["status"] == status, f"OS-03 {status} on {label} (got {r['OS-03']['status']}: {r['OS-03']['findings'][:1]})")
        for label, text in (("blank-first", "\n---\nname: pdf-tools\ndescription: Does a thing.\n---\n"),
                            ("bom", "\ufeff---\nname: pdf-tools\ndescription: Does a thing.\n---\n")):
            r = named(label, text)
            check(r["OS-03"]["status"] == "fail" and r["BP-04"]["status"] == "fail", f"OS-03 fails when the block does not start on line 1 ({label})")
        r = named("no-block", "# Title\n\n---\n\nText.\n")
        check(r["OS-03"]["status"] == "n/a" and r["OS-04"]["status"] == "n/a", "OS-03 and OS-04 are n/a without a frontmatter block")
        r = named("keys", "---\nname: pdf-tools\ndescription: Does a thing.\nallowed_tools: Read\nversion: 1\nuser-invocable: false\n---\n")
        check(sorted(f["line"] for f in r["OS-04"]["findings"]) == [4, 5], "OS-04 flags `allowed_tools` and a top-level `version` only")
        known = set(re.findall(r'"([\w-]+)"', re.search(r"KNOWN_KEYS = \{(.*?)\}", SCRIPT.read_text(encoding="utf-8"), re.S).group(1)))
        rule = re.search(r"### OS-04 .*?- Rule: (.*?)\n- Why", (SKILL / "references" / "other-official-sources.md").read_text(encoding="utf-8"), re.S).group(1)
        check(known == set(re.findall(r"`([\w-]+)`", rule)), "KNOWN_KEYS equals the field list in OS-04's Rule line")
        meta_cases = {
            "string": ('metadata:\n  version: "0.1"\n  author: ana\n', "pass"),
            "float": ("metadata:\n  version: 0.1\n", "fail"),
            "bool": ("metadata:\n  internal: yes\n", "fail"),
            "date": ("metadata:\n  created: 2026-10-18\n", "fail"),
            "nested": ("metadata:\n  owner:\n    team: docs\n", "fail"),
            "scalar": ("metadata: v1\n", "fail"),
            "list": ("metadata:\n  - a\n", "fail"),
            "compat-long": (f"compatibility: {'x' * 501}\n", "fail"),
            "compat-number": ("compatibility: 3\n", "fail"),
            "compat-ok": ("compatibility: Requires uv and network access\n", "pass"),
        }
        for label, (body, status) in meta_cases.items():
            r = named(f"meta-{label}", f"---\nname: pdf-tools\ndescription: Does a thing.\n{body}---\n")
            check(r["OS-06"]["status"] == status, f"OS-06 {status} on {label} (got {r['OS-06']['status']})")
        r = named("meta-flow", '---\nname: pdf-tools\ndescription: Does a thing.\nmetadata: {version: "0.1"}\n---\n')
        check(r["OS-06"]["status"] == "n/a" and r["OS-06"]["not_evaluated"], "OS-06: flow-style metadata is not evaluated, never a silent pass")
        check(named("meta-none", "---\nname: pdf-tools\ndescription: Does a thing.\n---\n")["OS-06"]["status"] == "n/a",
              "OS-06 is n/a without metadata and compatibility")
        r = named("listing-over", f"---\nname: pdf-tools\ndescription: {'d' * 1000}\nwhen_to_use: {'w' * 537}\n---\n")
        check(r["OS-08"]["status"] == "fail", "OS-08 fails at 1,537 characters of description plus when_to_use")
        r = named("listing-at", f"---\nname: pdf-tools\ndescription: {'d' * 1000}\nwhen_to_use: {'w' * 536}\n---\n")
        check(r["OS-08"]["status"] == "pass", "OS-08 passes at exactly 1,536 characters")
        target = tmp / "links" / "pdf-tools"
        (target / "references").mkdir(parents=True)
        (target / "references" / "guide.md").write_text("# Guide\n\nBack to [the skill](../SKILL.md#top), [up](../../x.md).\n", encoding="utf-8")
        (target / "SKILL.md").write_text(
            "---\nname: pdf-tools\ndescription: Does a thing.\n---\n\nRead [the guide](references/guide.md#intro) and "
            "[gone](references/gone.md), see [docs](https://example.com) and [top](#top).\n\n"
            "```markdown\n[example](references/example.md)\n```\n\nInline `[x](references/x.md)` is code.\n", encoding="utf-8")
        found = sorted((f["file"], f["line"], "outside" in f["message"]) for f in run_rules(target)["OS-11"]["findings"])
        check(found == [("SKILL.md", 6, False), ("references/guide.md", 3, True)],
              f"OS-11 flags a missing file and a link out of the skill; skips URLs, anchors, and code (got {found})")
        forms = tmp / "forms" / "pdf-tools"
        (forms / "references").mkdir(parents=True)
        (forms / "references" / "my guide.md").write_text("# Guide\n", encoding="utf-8")
        (tmp / "forms" / "outside").mkdir()
        (tmp / "forms" / "outside" / "shared.md").write_text("# Shared\n", encoding="utf-8")
        (forms / "shared").symlink_to("../outside")
        (forms / "SKILL.md").write_text(
            "---\nname: pdf-tools\ndescription: Does a thing.\n---\n\nRead [the guide](<references/my guide.md>), "
            "[ref][gone], and [shared](shared/shared.md).[^1]\n\n[gone]: references/gone.md\n[^1]: A footnote, not a link.\n",
            encoding="utf-8")
        found = sorted((f["line"], f["message"]) for f in run_rules(forms)["OS-11"]["findings"])
        check([n for n, _ in found] == [6, 8] and "symlink" in found[0][1] and "missing" in found[1][1],
              f"OS-11 reads <path with spaces> and reference-style links, flags a symlink out, skips footnotes (got {found})")
        linked_root = tmp / "forms" / "linked-root"
        linked_root.symlink_to(target)
        r = run_rules(linked_root)["OS-11"]["findings"]
        check(sorted(f["line"] for f in r) == [3, 6], f"OS-11: a skill folder that is itself a symlink is audited like the real one (got {r})")
        r = named("quoted-keys", "---\n\"name\": pdf-tools\n'description': Fills PDF forms. Use when a PDF form must be filled.\n---\n")
        bad = sorted(k for k in ("BP-04", "BP-05", "BP-09", "OS-02", "OS-03") if r[k]["status"] != "pass")
        check(not bad, f"quoted top-level keys name the same fields for every rule (not passing: {bad})")
        r = named("meta-unclosed",'---\nname: pdf-tools\ndescription: Does a thing.\nmetadata:\n  version: "0.3\n---\n')
        check(r["OS-03"]["status"] == "fail" and r["OS-03"]["findings"][0]["line"] == 5,
              f"OS-03 fails on an unclosed quote inside metadata (got {r['OS-03']})")
        r = named("meta-multiline", '---\nname: pdf-tools\ndescription: Does a thing.\nmetadata:\n  note: "two\n    lines"\n---\n')
        check(r["OS-03"]["status"] == "pass", "OS-03 passes a nested quoted value closed on a later line")

        nested = tmp / "nested.md"
        nested.write_text("# Title\n\n## Real one\n\n````markdown\n## Fake inside\n```bash\n## Still fake\n```\n### Fake after inner close\n````\n\n### Real two\n#### Real three ###\n~~~\n## Fake tilde\n~~~~\n##### Too deep\n", encoding="utf-8")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(HEADINGS), str(nested)], capture_output=True, text=True, check=False)
        check(result.returncode == 0 and result.stdout.split("\n")[:3] == ["H2 Real one", "H3 Real two", "H4 Real three"]
              and len(result.stdout.strip().splitlines()) == 3, "headings.py skips nested fences by CommonMark rules")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(HEADINGS), str(tmp / "absent.md")], capture_output=True, text=True, check=False)
        check(result.returncode == 2 and "cannot read" in result.stderr, "headings.py: unreadable file exits 2 with the reason")
        indented = tmp / "indented.md"
        indented.write_text("## One\n\n    ```\n## Two\n\n   ```\n## Fake\n   ```\n### Three\n", encoding="utf-8")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(HEADINGS), str(indented)], capture_output=True, text=True, check=False)
        check(result.stdout.splitlines() == ["H2 One", "H2 Two", "H3 Three"],
              f"headings.py: a fence indented 4 spaces is code text, 0-3 spaces opens a fence (got {result.stdout.splitlines()})")
        page = tmp / "page.html"
        page.write_text('<h2 id="core-principles">Core</h2><h3 id="_R_x_">Gen</h3><h3 id="solve-dont-punt">Solve</h3><h5 id="deep">x</h5>',
                        encoding="utf-8")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(HEADINGS), "--ids", str(page)], capture_output=True, text=True, check=False)
        check(result.returncode == 0 and result.stdout.split() == ["H2", "core-principles", "H3", "solve-dont-punt"],
              "headings.py --ids lists slug ids of h2-h4 only, skipping generated ids")

        target = tmp / "unreadable"
        (target / "references").mkdir(parents=True)
        (target / "assets").mkdir()
        (target / "SKILL.md").write_text("---\nname: pdf-tools\ndescription: Does a thing.\n---\n\n"
                                         "See `references/legacy.md`, `references/schema.json`, `assets/logo.png`.\n", encoding="utf-8")
        latin = "# Legacy\n\n" + "Caf\u00e9 r\u00e9sum\u00e9 line.\n" * 150 + "Open C:\\data\\x\\file.md\n"
        (target / "references" / "legacy.md").write_bytes(latin.encode("latin-1"))
        (target / "references" / "schema.json").write_text("{}\n", encoding="utf-8")
        (target / "assets" / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00binary")
        result = run(target)
        out = json.loads(result.stdout)
        r = out["rules"]
        check([u["file"] for u in out["unreadable"]] == ["references/legacy.md"] and "not UTF-8" in out["unreadable"][0]["reason"],
              "Latin-1 file is listed as unreadable; the binary PNG is not")
        check(all(r[k]["status"] == "n/a" and r[k]["not_evaluated"][0]["file"] == "references/legacy.md" for k in ("BP-22", "BP-40")),
              "Latin-1 reference: BP-22 and BP-40 not evaluated, not a silent pass")
        check(r["BP-21"]["status"] == "pass", "a .json file in references/ counts as a reference file and is linked")
        (target / "references" / "run.md").write_text("Run scripts\\fill.rb now.\n", encoding="utf-8")
        r = run_rules(target)
        check(r["BP-40"]["status"] == "fail" and r["BP-40"]["not_evaluated"]
              and any(f["file"] == "references/run.md" for f in r["BP-40"]["findings"]),
              "confirmed BP-40 failure plus an unreadable file stays fail, with not_evaluated listed")
        (target / "references" / "run.md").unlink()
        (target / "SKILL.md").write_text("---\nname: pdf-tools\ndescription: Does a thing.\n---\n\nNo links.\n", encoding="utf-8")
        r = run_rules(target)
        check(any(f["file"] == "references/schema.json" for f in r["BP-21"]["findings"]), "unlinked .json reference fails BP-21")
        locked = target / "references" / "locked"
        locked.mkdir()
        locked.chmod(0)
        try:
            out = json.loads(run(target).stdout)
            check(any(u["file"] == "references/locked/" for u in out["unreadable"])
                  and all(out["rules"][k].get("not_evaluated")
                          and out["rules"][k]["status"] == ("fail" if out["rules"][k]["findings"] else "n/a")
                          for k in ("BP-21", "BP-39", "BP-40")),
                  "unlistable folder is reported and marks the file-list rules not evaluated")
        finally:
            locked.chmod(0o755)

        target = tmp / "plain-text"
        (target / "references").mkdir(parents=True)
        (target / "SKILL.md").write_text("---\nname: pdf-tools\ndescription: Does a thing.\n---\n\nRead `references/codes.txt`.\n", encoding="utf-8")
        (target / "references" / "codes.txt").write_text("Error codes\n\n" + "E1 means x.\n" * 120, encoding="utf-8")
        check(run_rules(target)["BP-22"]["status"] == "fail", "BP-22: a long .txt reference without contents fails")
        (target / "references" / "codes.txt").write_text("Error codes\n\nContents: E1 to E9\n" + "E1 means x.\n" * 120, encoding="utf-8")
        check(run_rules(target)["BP-22"]["status"] == "pass", "BP-22: a plain 'Contents' line counts in a .txt reference")

        target = tmp / "linked"
        (target / "shared").mkdir(parents=True)
        (tmp / "outside").mkdir()
        (tmp / "outside" / "guide.md").write_text("# Guide\n", encoding="utf-8")
        (target / "shared" / "loop").symlink_to(target, target_is_directory=True)  # cycle back to the root
        (target / "references").symlink_to(tmp / "outside", target_is_directory=True)
        (target / "SKILL.md").write_text("---\nname: pdf-tools\ndescription: Does a thing.\n---\n\nNo links.\n", encoding="utf-8")
        result = run(target)
        r = json.loads(result.stdout)["rules"]
        files = [f["file"] for f in r["BP-21"]["findings"]]
        check(result.returncode == 0 and files == ["references/guide.md"],
              f"symlinked folders are followed once, cycles stop (BP-21 findings: {files})")

        result = run(tmp / "missing")
        check(result.returncode == 2 and "not a directory" in result.stderr, "missing path: exit 2, names the problem")
        (tmp / "empty").mkdir()
        result = run(tmp / "empty")
        check(result.returncode == 2 and "no SKILL.md" in result.stderr, "dir without SKILL.md: exit 2, names the problem")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPT)], capture_output=True, text=True, check=False)
        check(result.returncode == 2 and "expected exactly one argument" in result.stderr, "no argument: exit 2")

    # not_applicable: judgment rules the skill's composition alone decides as n/a.
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        bare = tmp / "bare"
        bare.mkdir()
        (bare / "SKILL.md").write_text("---\nname: bare\ndescription: Does a thing.\n---\n\nBody.\n", encoding="utf-8")
        skipped = json.loads(run(bare).stdout)["not_applicable"]
        evaluation = set(re.findall(r"^### (BP-\d\d)\b.*\n\nType: judgment · Level: \w+ · Applies to: evaluation material\b",
                                    catalogue, re.MULTILINE)) - {"BP-32"}
        check({k for k, v in skipped.items() if "evaluation" in v} == evaluation - {"BP-54"} and len(evaluation) == 8,
              f"a skill with no evaluation folder: every evaluation judgment rule but BP-32 is n/a (got {sorted(skipped)})")
        check(skipped.get("BP-52") == skipped.get("BP-54") == "no bundled files" and {"OS-10", "OS-17"} <= set(skipped),
              "a bare skill: BP-52, BP-54, OS-10, OS-17 are n/a with their reasons")
        check(not set(skipped) & mechanical, "not_applicable never names a mechanical rule")
        full = tmp / "full"
        (full / "tools" / "evals").mkdir(parents=True)
        (full / "references").mkdir()
        (full / "references" / "guide.md").write_text("# Guide\n", encoding="utf-8")
        (full / "SKILL.md").write_text("---\nname: full\ndescription: Does a thing.\nallowed-tools: Bash(git status *)\n---\n\n"
                                       "Branch: !`git status`\n\nSee [guide](references/guide.md).\n", encoding="utf-8")
        check(json.loads(run(full).stdout)["not_applicable"] == {},
              "nested evaluation folder, bundled file, injected command, allowed-tools: nothing is pre-decided")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPT.with_name("judgment_rules.py")), str(bare)],
                                capture_output=True, text=True, check=False)
        printed = set(re.findall(r"^### ((?:BP|OS)-\d\d) ", result.stdout, re.MULTILINE))
        judgment = set(re.findall(r"^### ((?:BP|OS)-\d\d)\b.*\n\nType: judgment", catalogue + OS_CATALOGUE.read_text(encoding="utf-8"),
                                  re.MULTILINE))
        check(result.returncode == 0 and printed == judgment - set(skipped) and "Type: mechanical" not in result.stdout,
              "judgment_rules.py prints exactly the judgment rules left to the model")
        check(result.stdout.count("## Terms") == 2 and "## Retired rules" not in result.stdout and "Left out" in result.stdout,
              "judgment_rules.py keeps both Terms sections, names what it left out, and skips the other sections")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPT.with_name("judgment_rules.py")), str(tmp / "none")],
                                capture_output=True, text=True, check=False)
        check(result.returncode == 2 and "no SKILL.md" in result.stderr, "judgment_rules.py: missing skill exits 2 and names the problem")

    result = run(SKILL)
    rules = json.loads(result.stdout)["rules"]
    check(all(v["status"] in ("pass", "n/a") for v in rules.values()), "the skill itself passes every mechanical rule (BP and OS)")

    print(f"\n{'FAILED' if FAILURES else 'PASSED'}: {len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
