#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Semantic CLI regression tests for the JSON-to-Markdown/HTML pipeline."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "skills").is_dir())
SKILL = next(ROOT.glob("skills/**/auditing-skill-best-practices/SKILL.md")).parent
SCRIPT = SKILL / "scripts/render_report.py"
SAMPLE = Path(__file__).resolve().parents[1] / "fixtures/review/findings-violating.json"
# test data: a Russian override of some report and page labels; the shipped labels are English only
RU_LABELS = {"report": {"article": "Правила статьи", "rejected": "Отклонено рецензентом", "fix": "Исправление",
                        "script": "решено скриптом", "na_no_evaluation_material": "нет материалов оценки (BP-32)"},
             "page": {"accept": "Принять"}}


def digest(folder: Path) -> dict:
    return {str(path.relative_to(folder)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in folder.rglob("*") if path.is_file()}


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.target = self.root / "target"
        self.target.mkdir()
        (self.target / "SKILL.md").write_text("Original target bytes.\n")
        self.data = json.loads(SAMPLE.read_text())
        self.data["target"] = str(self.target)
        self.findings = self.root / "findings.json"
        self.env = {**os.environ, "TMPDIR": str(self.root)}

    def run_cli(self, *args, data=None, script=SCRIPT, env=None):
        self.findings.write_text(json.dumps(self.data if data is None else data, ensure_ascii=False))
        return subprocess.run(["uv", "run", "--quiet", "--script", str(script), *map(str, args)],
                              capture_output=True, text=True, env=env or self.env, check=False)

    def render(self, data=None, page=False):
        result = self.run_cli(self.findings, *(["--page"] if page else []), data=data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        summary = json.loads(result.stdout)
        report = Path(summary["report"]).read_text()
        return result, summary, report

    def test_full_report_counts_metadata_and_fix_forms(self):
        _, summary, report = self.render(page=True)
        for group, prefix in (("article", "BP-"), ("other", "OS-")):
            for status in ("pass", "fail", "n/a"):
                self.assertEqual(summary["counts"][group][status],
                                 sum(r["id"].startswith(prefix) and r["status"] == status for r in self.data["rules"]))
        self.assertIn("Skill authoring best practices (Anthropic)", report)
        self.assertIn(self.data["snapshot"], report)
        self.assertIn(self.data["hosts"], report)
        self.assertIn("## Article rules", report)
        self.assertIn("## Other official sources", report)
        unindented = "\n".join(line[2:] if line.startswith("  ") else line for line in report.splitlines())
        for finding in self.data["failures"]:
            self.assertIn(f"**{finding['rule']} ", report)
            self.assertIn(finding["location"], report)
            for key in ("why", "evidence", "before", "after", "fix", "range", "fix_location"):
                if key in finding:
                    self.assertIn(finding[key], unindented)
            if "fix_ref" in finding:
                self.assertIn("same edit as " + finding["fix_ref"], report)
        html = Path(summary["page"]).read_text()
        embedded = json.loads(re.search(r'<script type="application/json" id="audit-data">(.*?)</script>', html, re.S)[1])
        self.assertEqual([(r["id"], r["status"], r["evidence"]) for r in embedded["rules"]],
                         [(r["id"], r["status"], r["evidence"]) for r in self.data["rules"]])
        self.assertEqual(embedded["failures"], self.data["failures"])

    def test_compact_stdout_and_no_input_or_target_mutation(self):
        self.data["failures"][0]["evidence"] = "UNIQUE_EVIDENCE_MUST_NOT_ENTER_STDOUT"
        before_skill, before_target = digest(SKILL), digest(self.target)
        result, summary, report = self.render()
        self.assertEqual(set(summary), {"counts", "findings", "report"})
        self.assertEqual(len(result.stdout.strip().splitlines()), 1)
        self.assertNotIn("UNIQUE_EVIDENCE", result.stdout)
        self.assertIn("UNIQUE_EVIDENCE", report)
        self.assertEqual(json.loads(self.findings.read_text()), self.data)
        self.assertEqual(digest(SKILL), before_skill)
        self.assertEqual(digest(self.target), before_target)
        self.assertFalse((self.root / "findings.html").exists())

    def test_localization_literal_text_rejections_and_fix_location(self):
        self.data["lang"] = "ru"
        _, _, report = self.render()
        self.assertIn("## Article rules", report)  # no labels: English, whatever the language
        self.data["labels"] = RU_LABELS
        finding = self.data["failures"][0]
        finding["reviewer_reason"] = "Причина: `это` не нужно."
        self.data["failures"][1]["evidence"] = "строка <script> с `кодом`"
        own = next(f for f in self.data["failures"] if "before" in f and "reviewer_reason" not in f)
        own["before"] = "first\n```\nlast `tick`"
        own["after"] = "новый текст"
        own["fix_location"] = "references/guide.md:7"
        _, _, report = self.render()
        self.assertIn("## Правила статьи", report)
        self.assertIn("Отклонено рецензентом", report)
        self.assertIn(finding["reviewer_reason"], report)
        rejected_block = report.split(f"**{finding['rule']} ", 1)[1].split("\n- **", 1)[0]
        self.assertNotIn("Исправление:", rejected_block)
        self.assertIn("````text", report)
        self.assertIn("<script>", report)
        self.assertIn("references/guide.md:7", report)
        self.assertIn("новый текст", report)
        self.assertIn("## Other official sources", report)  # a label the override leaves out stays English
        _, summary, _ = self.render(page=True)
        html = Path(summary["page"]).read_text()
        embedded = json.loads(re.search(r'<script type="application/json" id="audit-data">(.*?)</script>', html, re.S)[1])
        self.assertEqual(embedded["labels"], RU_LABELS)  # the same override reaches the page
        self.data["labels"] = {"report": {"article": "Rules of {s}"}}
        result = self.run_cli(self.findings)
        self.assertEqual(result.returncode, 2)
        self.assertIn("labels.report.article: must keep the tokens", result.stderr)

    def test_not_evaluated_distinct_from_genuine_na(self):
        self.data["not_evaluated"] = [{"rule": "BP-03", "reason": "evidence unavailable"},
                                      {"rule": "BP-07", "reason": "one additional file unreadable"}]
        next(r for r in self.data["rules"] if r["id"] == "BP-03")["status"] = "n/a"
        _, _, report = self.render(page=True)
        unavailable = report.split("## Not evaluated", 1)[1]
        self.assertIn("BP-03 —", unavailable)
        self.assertIn("BP-07 —", unavailable)
        self.assertIn("evidence unavailable", unavailable)
        self.assertNotIn("OS-08", unavailable)
        self.data.pop("not_evaluated")
        _, _, report = self.render()
        self.assertNotIn("## Not evaluated", report)

    def test_invalid_inputs_write_no_views(self):
        variants = []
        missing = copy.deepcopy(self.data)
        missing["rules"].pop()
        variants.append((missing, "is missing"))
        for entries in (None, [1], [{"rule": ["BP-03"], "reason": "x"}],
                        [{"rule": "BP-99", "reason": "x"}], [{"rule": "BP-03", "reason": ""}],
                        [{"rule": "BP-04", "reason": "cannot mark a passing rule unavailable"}],
                        [{"rule": "BP-07", "reason": "x"}, {"rule": "BP-07", "reason": "y"}],
                        [{"rule": "BP-07", "reason": "x", "extra": "unknown field"}]):
            bad = copy.deepcopy(self.data)
            bad["not_evaluated"] = entries
            variants.append((bad, "not_evaluated"))
        for data, expected in variants:
            with self.subTest(expected=expected, data=data.get("not_evaluated")):
                result = self.run_cli(self.findings, "--page", data=data)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse((self.root / "findings.md").exists())
                self.assertFalse((self.root / "findings.html").exists())
        self.findings.write_text("{broken json")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPT), str(self.findings)],
                                capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_protected_destinations_symlinks_and_new_allocation(self):
        before = digest(self.target)
        link = self.root / "link"
        link.symlink_to(self.target, target_is_directory=True)
        for out in (self.target / "report.md", link / "report.md", SKILL / "report.md",
                    self.root / "report.txt", self.root / "missing/report.md"):
            result = self.run_cli(self.findings, out, "--page")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(out.exists())
        (self.root / "findings.html").symlink_to(self.target / "protected.html")
        result = self.run_cli(self.findings, "--page")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "findings.md").exists())
        self.assertEqual(digest(self.target), before)
        # Set protected TMPDIR after uv starts: uv itself creates launcher locks there.
        result = subprocess.run(["uv", "run", "--quiet", "python", "-c",
                                 "import os,runpy,sys; os.environ['TMPDIR']=sys.argv[1]; "
                                 "sys.argv=sys.argv[2:]; sys.path.insert(0,os.path.dirname(sys.argv[0])); "
                                 "runpy.run_path(sys.argv[0],run_name='__main__')",
                                 str(self.target), str(SCRIPT), "--new", str(self.target)],
                                capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(digest(self.target), before)
        names = [self.run_cli("--new", self.target).stdout.strip() for _ in range(2)]
        self.assertNotEqual(*names)
        self.assertTrue(all(Path(name).is_file() and Path(name).stat().st_size == 0 for name in names))

    def test_mechanical_flag_completes_the_findings(self):
        (self.target / "SKILL.md").write_text("---\nname: target\ndescription: Does a thing.\n---\n\nBody.\n")
        checker = json.loads(subprocess.run(
            ["uv", "run", "--quiet", "--script", str(SKILL / "scripts/check_mechanical.py"), str(self.target)],
            capture_output=True, text=True, check=True).stdout)
        decided = set(checker["rules"]) | set(checker["not_applicable"])
        self.assertTrue(all(rule["status"] != "fail" for rule in checker["rules"].values()))
        full = [{**rule, "status": "pass"} for rule in self.data["rules"]]
        partial = {**self.data, "failures": [], "lang": "ru", "labels": RU_LABELS,
                   "rules": [r for r in full if r["id"] not in decided]}
        self.assertEqual(self.run_cli(self.findings, data=partial).returncode, 2)  # incomplete without the flag
        result = self.run_cli(self.findings, "--mechanical", data=partial)
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = json.loads(self.findings.read_text())
        self.assertEqual([r["id"] for r in saved["rules"]], [r["id"] for r in full])  # complete, in catalogue order
        status = {r["id"]: r for r in saved["rules"]}
        for rid, rule in checker["rules"].items():
            self.assertEqual(status[rid]["status"], rule["status"])
        self.assertEqual(status["BP-04"]["evidence"], "решено скриптом")
        self.assertEqual((status["BP-33"]["status"], status["BP-33"]["evidence"]), ("n/a", "нет материалов оценки (BP-32)"))
        self.assertEqual(json.loads(result.stdout)["counts"]["other"]["fail"], 0)

        # the model may judge a pre-decided n/a rule itself; a mechanical status it contradicts is refused
        own = copy.deepcopy(partial)
        own["rules"].append({"id": "BP-33", "status": "pass", "evidence": "evaluations kept at a location the user named"})
        self.assertEqual(self.run_cli(self.findings, "--mechanical", data=own).returncode, 0)
        self.assertEqual({r["id"]: r["status"] for r in json.loads(self.findings.read_text())["rules"]}["BP-33"], "pass")
        own["rules"].append({"id": "BP-04", "status": "fail", "evidence": "model disagrees"})
        result = self.run_cli(self.findings, "--mechanical", data=own)
        self.assertEqual(result.returncode, 2)
        self.assertIn("BP-04", result.stderr)
        self.assertIn("binding", result.stderr)
        self.assertEqual(json.loads(self.findings.read_text()), own)  # a refused run leaves the findings as written

        # a mechanical failure still needs the model's failure entry
        (self.target / "SKILL.md").write_text("---\nname: Target\ndescription: Does a thing.\n---\n\nBody.\n")
        result = self.run_cli(self.findings, "--mechanical", data=partial)
        self.assertEqual(result.returncode, 2)
        self.assertIn("BP-05 has status fail but no failure entry", result.stderr)

    def test_compliant_report_and_installed_folder_alone(self):
        self.data["failures"] = []
        for rule in self.data["rules"]:
            rule["status"] = "pass"
        installed = self.root / "installed"
        shutil.copytree(SKILL, installed)
        before = digest(installed)
        result = self.run_cli(self.findings, "--page", script=installed / "scripts/render_report.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        report = Path(summary["report"]).read_text()
        self.assertEqual(report.count("No failures."), 2)
        self.assertEqual(summary["counts"]["article"]["fail"], 0)
        self.assertEqual(digest(installed), before)

    def test_plain_python_fallback_without_uv_on_path(self):
        installed = self.root / "portable-skill"
        shutil.copytree(SKILL, installed)
        before_skill, before_target = digest(installed), digest(self.target)
        for name in ("python3", "python"):
            with self.subTest(interpreter=name):
                bindir = self.root / name
                bindir.mkdir()
                # The outer test runs through uv; this is the user-requested runtime fallback.
                (bindir / name).symlink_to(sys.executable)
                env = {**self.env, "PATH": str(bindir), "PYTHONPATH": ""}
                self.assertIsNone(shutil.which("uv", path=env["PATH"]))

                def launch(script, *args):
                    return subprocess.run([name, str(installed / "scripts" / script), *map(str, args)],
                                          capture_output=True, text=True, env=env, check=False)

                mechanical = launch("check_mechanical.py", self.target)
                self.assertEqual(mechanical.returncode, 0, mechanical.stderr)
                self.assertTrue(json.loads(mechanical.stdout)["rules"])
                allocated = launch("render_report.py", "--new", self.target)
                self.assertEqual(allocated.returncode, 0, allocated.stderr)
                findings = Path(allocated.stdout.strip())
                findings.write_text(json.dumps(self.data))
                result = launch("render_report.py", findings, "--page")
                self.assertEqual(result.returncode, 0, result.stderr)
                summary = json.loads(result.stdout)
                self.assertEqual(set(summary), {"counts", "findings", "report", "page"})
                self.assertTrue(Path(summary["report"]).is_file())
                self.assertTrue(Path(summary["page"]).is_file())
                direct = launch("render_review_page.py", findings, self.root / f"{name}-direct.html")
                self.assertEqual(direct.returncode, 0, direct.stderr)
        self.assertEqual(digest(installed), before_skill)
        self.assertEqual(digest(self.target), before_target)


if __name__ == "__main__":
    unittest.main()
