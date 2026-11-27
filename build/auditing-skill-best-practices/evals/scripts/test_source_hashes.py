#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Offline checks of the source hash gate: statuses, text mode, table round trip, bad tables."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "skills").is_dir())
SKILL = next(ROOT.glob("skills/**/auditing-skill-best-practices/SKILL.md")).parent
SCRIPT = SKILL / "scripts/source_hashes.py"
HEAD = "Intro\n\n| File | URL | Mode | sha256 |\n| --- | --- | --- | --- |\n"
ZERO = "0" * 64


def cli(*args):
    return subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True)


class SourceHashesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.files = self.dir / "files"
        self.files.mkdir()
        self.table = self.dir / "table.md"
        (self.files / "a.md").write_text("# Article\n")
        (self.files / "page.html").write_text(
            "<html><script>var n=1</script><article id='h_1'><p>Skill  name</p></article></html>")
        (self.files / "raw.html").write_text("<html>whatever</html>")
        self.table.write_text(
            HEAD
            + f"| `a.md` | <https://example.com/a.md> | bytes | {ZERO} |\n"
            + f"| `page.html` | <https://example.com/page> | text | {ZERO} |\n"
            + "| `raw.html` | <https://example.com/raw> | none | — |\n")
        # Store the live hashes through the script's own table output.
        printed = cli(self.files, "--offline", "--print-table", "--table", self.table)
        self.assertEqual(printed.returncode, 0, printed.stderr)
        self.table.write_text("Intro\n\n" + printed.stdout)

    def tearDown(self):
        self.tmp.cleanup()

    def run_json(self):
        done = cli(self.files, "--offline", "--table", self.table)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_round_trip_is_unchanged(self):
        out = self.run_json()
        self.assertTrue(out["all_unchanged"])
        self.assertEqual(out["unchanged"], ["a.md", "page.html"])
        self.assertEqual([s["status"] for s in out["sources"]], ["unchanged", "unchanged", "fetched"])

    def test_changed_bytes(self):
        (self.files / "a.md").write_text("# Article\n\nNew rule.\n")
        out = self.run_json()
        self.assertFalse(out["all_unchanged"])
        self.assertEqual(out["changed"], ["a.md"])

    def test_text_mode_ignores_markup_but_not_text_or_ids(self):
        (self.files / "page.html").write_text(
            "<html><script>var n=2</script><div class='x'><article id='h_1'>\n<p class='y'>Skill name</p>"
            "</article></div></html>")
        self.assertTrue(self.run_json()["all_unchanged"])
        (self.files / "page.html").write_text("<article id='h_1'><p>Skill title</p></article>")
        self.assertEqual(self.run_json()["changed"], ["page.html"])
        (self.files / "page.html").write_text("<article id='h_2'><p>Skill name</p></article>")
        self.assertEqual(self.run_json()["changed"], ["page.html"])

    def test_missing_or_empty_file_is_unreachable_never_unchanged(self):
        (self.files / "a.md").unlink()
        (self.files / "page.html").write_text("  \n")
        out = self.run_json()
        self.assertFalse(out["all_unchanged"])
        self.assertEqual(out["unreachable"], ["a.md", "page.html"])
        self.assertTrue(all(s["error"] for s in out["sources"] if s["status"] == "unreachable"))
        # An unreadable row keeps its stored hash in the printed table.
        printed = cli(self.files, "--offline", "--print-table", "--table", self.table)
        self.assertEqual("Intro\n\n" + printed.stdout, self.table.read_text())

    def test_bad_input_exits_2(self):
        for text in ("no table here\n",
                     HEAD,
                     HEAD + "| `a.md` | <http://example.com/a.md> | bytes | " + ZERO + " |\n",
                     HEAD + "| `../a.md` | <https://example.com/a.md> | bytes | " + ZERO + " |\n",
                     HEAD + "| `a.md` | <https://example.com/a.md> | bytes | abc |\n",
                     HEAD + "| `a.md` | <https://example.com/a.md> | none | " + ZERO + " |\n",
                     HEAD + "| `a.md` | <https://example.com/a.md> | md5 | " + ZERO + " |\n"):
            self.table.write_text(text)
            done = cli(self.files, "--offline", "--table", self.table)
            self.assertEqual(done.returncode, 2, text)
            self.assertIn("source_hashes:", done.stderr)
        self.assertEqual(cli().returncode, 2)
        self.assertEqual(cli(self.files, "--bogus").returncode, 2)

    def test_shipped_table_parses_and_names_the_article_first(self):
        done = cli(self.dir / "empty", "--offline")
        self.assertEqual(done.returncode, 0, done.stderr)
        out = json.loads(done.stdout)
        self.assertFalse(out["all_unchanged"])
        self.assertEqual(out["sources"][0]["file"], "best-practices.md")
        self.assertEqual(len(out["unreachable"]), len(out["sources"]))
        for name in ("best-practices.html", "claude-code-skills.md"):  # names refresh.md relies on
            self.assertIn(name, [s["file"] for s in out["sources"]])


if __name__ == "__main__":
    unittest.main()
