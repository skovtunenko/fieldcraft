#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""One end-to-end check of Git scope selection and renderer baseline capture."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "skills").is_dir())
SKILL = next(ROOT.glob("skills/**/auditing-skill-best-practices/SKILL.md")).parent
SCRIPTS = SKILL / "scripts"
SAMPLE = Path(__file__).resolve().parents[1] / "fixtures/review/findings-violating.json"


class ScopeTest(unittest.TestCase):
    def test_audited_worktree_to_card(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target = root / "target"
            target.mkdir()

            def git(*args):
                return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

            def write(name, text):
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)

            def cli(script, *args):
                return subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPTS / script), *map(str, args)],
                                      env={**os.environ, "TMPDIR": str(root)}, capture_output=True, text=True, check=True)

            git("init", "-b", "main")
            write("SKILL.md", "Run scripts\\fill_form.py.\n")
            write("references/basics.md", "Initial\n")
            write("references/doc2.md", "Unchanged\n")
            write("scripts/fill_form.py", "# Not executed\n")
            write("scripts/unused_helper.py", "# Unchanged\n")
            write("old.md", "Renamed content\n" * 10)
            write("deleted.md", "Remove me\n")
            git("add", "target")
            git("-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "-m", "fixture")
            write("references/basics.md", "Already dirty at audit\n")
            write("untracked.md", "Already untracked at audit\n")
            data = json.loads(SAMPLE.read_text())
            data["target"] = str(target)
            data["rules"][0]["evidence"] = "scripts/fill_form.py:1"
            data["rules"][1]["evidence"] = "A quote without a file"
            data["rules"][2]["evidence"] = "references/doc2.md:1"
            findings = root / "prior.json"
            findings.write_text(json.dumps(data))
            stdout = json.loads(cli("render_report.py", findings).stdout)
            self.assertEqual(set(stdout), {"counts", "findings", "report"})
            self.assertEqual(json.loads(findings.read_text()), data)
            self.assertTrue(findings.with_suffix(".scope.json").is_file())
            self.assertEqual(json.loads(cli("stale_scope.py", target, findings).stdout)["read"], [])

            write("SKILL.md", "Run scripts/fill_form.py.\n")
            write("references/basics.md", "Already dirty at audit\nSee [missing](missing-notes.md).\n")
            write("added.md", "New\n")
            (target / "deleted.md").unlink()
            (target / "old.md").rename(target / "new.md")
            git("add", "target/SKILL.md")  # Include both staged and unstaged changes.
            result = cli("stale_scope.py", target, findings)
            self.assertEqual(result.stderr, "")
            self.assertEqual(len(result.stdout.splitlines()), 1)
            card = json.loads(result.stdout)
            self.assertEqual(card["changed"], ["SKILL.md", "references/basics.md"])
            self.assertEqual(card["added"], ["added.md"])
            self.assertEqual(card["deleted"], ["deleted.md"])
            self.assertEqual(card["renamed"], [{"from": "old.md", "to": "new.md"}])
            self.assertIn("scripts/fill_form.py", card["cited"])
            self.assertIn("references/missing-notes.md", card["cited"])
            self.assertIn(data["rules"][0]["id"], card["rules"])
            self.assertNotIn(data["rules"][1]["id"], card["rules"])
            self.assertNotIn(data["rules"][2]["id"], card["rules"])
            self.assertEqual(card["read"], ["SKILL.md", "added.md", "new.md", "references/basics.md", "scripts/fill_form.py"])
            saved = findings.with_suffix(".scope.json").read_bytes()
            cli("render_report.py", findings)
            self.assertEqual(findings.with_suffix(".scope.json").read_bytes(), saved)
            self.assertEqual(json.loads(cli("stale_scope.py", target, root / "absent.json").stdout)["fallback"], "full")
            findings.with_suffix(".scope.json").unlink()
            self.assertEqual(json.loads(cli("stale_scope.py", target, findings).stdout)["fallback"], "full")


if __name__ == "__main__":
    unittest.main()
