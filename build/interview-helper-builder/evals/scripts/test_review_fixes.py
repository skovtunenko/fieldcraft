#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Regressions for the candidate, language, timebox, and score-label review fixes."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_background import APPROVAL, SCRIPTS, spec
from generate_interview_helper import approved_plan_errors, validate_spec
from review_plan import approval_errors
from validate_interview_helper import validate_embedded_spec
from check_spec import check


class ScoreMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.labels = []
        self.selects = []

    def handle_starttag(self, tag, attrs):
        if tag == "label":
            self.labels.append(dict(attrs).get("for"))
        elif tag == "select":
            self.selects.append(dict(attrs))


class ReviewFixTests(unittest.TestCase):
    def generate(self, folder, value, approved=None):
        folder = Path(folder)
        source, approval, output = (folder / name for name in ("spec.json", "approved.json", "helper.html"))
        source.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        approval.write_text(json.dumps({**(value if approved is None else approved), "approval": APPROVAL}, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPTS / "generate_interview_helper.py"),
                                 "--spec", str(source), "--approved", str(approval), "--output", str(output)],
                                text=True, capture_output=True)
        return result, output

    def test_approval_rejects_candidate_and_role_changes_and_missing_identity(self):
        approved = spec()
        self.assertEqual(approved_plan_errors(approved, approved), [])
        for field in ("candidate", "role"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as folder:
                value = {**approved, field: "Different"}
                result, output = self.generate(folder, value, approved)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(field, result.stderr)
                self.assertFalse(output.exists())
            missing = copy.deepcopy(approved)
            del missing[field]
            self.assertTrue(approved_plan_errors(approved, missing))

    def test_original_name_passes_generator_and_html_validator_on_english_page(self):
        value = {**spec(), "candidate": "Иван Иванов", "language": "en"}
        self.assertEqual(check(value)[0], [])
        with tempfile.TemporaryDirectory() as folder:
            result, output = self.generate(folder, value)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Иван Иванов", output.read_text(encoding="utf-8"))
            checked = subprocess.run([sys.executable, str(SCRIPTS / "validate_interview_helper.py"), str(output)],
                                     text=True, capture_output=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        for field in ("ask", "title"):
            changed = copy.deepcopy(value)
            changed["sections"][0]["questions"][0][field] = "Непереведённый текст"
            with self.subTest(field=field), tempfile.TemporaryDirectory() as folder:
                result, output = self.generate(folder, changed)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Cyrillic", result.stderr)
                self.assertFalse(output.exists())
                self.assertTrue(validate_embedded_spec("const CONFIG=" + json.dumps(changed, ensure_ascii=False) + ";"))
                self.assertTrue(check(changed)[0])

    def test_draft_and_final_reject_the_same_invalid_timeboxes(self):
        for minutes in ("20m garbage", "0m", "-5m", "later", "", "1e2m", "9" * 400 + "m"):
            value = spec()
            value["sections"][0]["minutes"] = minutes
            with self.subTest(minutes=minutes):
                self.assertTrue(approval_errors(value))
                self.assertTrue(check(value)[0])
                with self.assertRaisesRegex(SystemExit, "timebox"):
                    validate_spec(value)
        for minutes in ("20m", "20", "20.0m", " 20 m "):
            value = spec()
            value["sections"][0]["minutes"] = minutes
            with self.subTest(minutes=minutes):
                self.assertEqual(approval_errors(value), [])
                self.assertEqual(check(value)[0], [])
                validate_spec(value)
        value = spec()
        reserve = copy.deepcopy(value["sections"][0])
        reserve.update(id="reserve", minutes="if time")
        reserve["questions"][0].update(id="q2", index="2.1")
        value["sections"].append(reserve)
        self.assertEqual(approval_errors(value), [])
        validate_spec(value)

    def test_score_labels_are_unique_and_preserve_storage_keys_after_backup(self):
        value = spec()
        value["scoreDimensions"] = [{"key": "ownership", "label": "Ownership"},
                                    {"key": 'depth<&"', "label": "Runtime depth"}]
        with tempfile.TemporaryDirectory() as folder:
            result, output = self.generate(folder, value)
            self.assertEqual(result.returncode, 0, result.stderr)
            script = r"""
const fs=require('fs'),vm=require('vm');
const html=fs.readFileSync(process.argv[1],'utf8');
const js=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
const nodes={scoreGrid:{innerHTML:''},embeddedState:{textContent:''}};
const clone={querySelector:s=>nodes[s.slice(1)]||null,get outerHTML(){return '<main>'+nodes.scoreGrid.innerHTML+'</main><script type="application/json" id="embeddedState">'+nodes.embeddedState.textContent+'</script>'}};
const ctx={document:{addEventListener(){},querySelector:s=>nodes[s.slice(1)]||null,
  documentElement:{cloneNode:()=>clone}},setTimeout(){},clearTimeout(){}};
vm.createContext(ctx);vm.runInContext(js,ctx);
const first=vm.runInContext("renderScores();state.scores.ownership='Strong';$('#scoreGrid').innerHTML",ctx);
vm.runInContext('buildSavedHtml()',ctx);
const saved=JSON.parse(nodes.embeddedState.textContent);
if(saved.state.scores.ownership!=='Strong')throw new Error('backup lost score');
if(nodes.scoreGrid.innerHTML!=='')throw new Error('backup must clear derived score markup');
const reloaded=vm.runInContext("renderScores();$('#scoreGrid').innerHTML",ctx);
if(first!==reloaded)throw new Error('restored score markup changed');
console.log(first);
"""
            rendered = subprocess.run(["node", "-e", script, str(output)], text=True, capture_output=True)
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            markup = ScoreMarkup()
            markup.feed(rendered.stdout)
            self.assertEqual(len(markup.selects), 2)
            identifiers = [select.get("id") for select in markup.selects]
            self.assertTrue(all(identifiers))
            self.assertEqual(len(set(identifiers)), 2)
            self.assertEqual(markup.labels, identifiers)
            self.assertEqual([select["data-score"] for select in markup.selects], [row["key"] for row in value["scoreDimensions"]])


if __name__ == "__main__":
    unittest.main()
