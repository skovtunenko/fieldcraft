#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Roundtrip and rejection checks for the shipped preparation reviewer."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "skills").is_dir())
SKILL = next(ROOT.glob("skills/**/interview-helper-builder/SKILL.md")).parent
sys.path.insert(0, str(SKILL / "scripts"))
from review_plan import apply_feedback, approval_errors, draft_items, fingerprint, ignore_temporary, main, read_feedback, round_changes  # noqa: E402
from generate_interview_helper import approved_plan_errors, validate_spec  # noqa: E402


def draft():
    return {"candidate": "Demo Candidate", "role": "Architect", "durationMinutes": 30,
            "analysisContext": ["Preserve this context"], "outOfScope": ["Trivia"],
            "deepestProbes": ["Runtime ownership"], "scoreDimensions": [{"key": "depth", "label": "Depth"}],
            "sections": [
                {"id": "s1", "title": "Runtime", "minutes": "10m", "meta": "Keep meta", "coach": "Keep cue",
                 "requirementIds": ["R1"], "questions": [
                     {"id": "q1", "index": "1.1", "title": "A real system", "ask": "Walk through your system.",
                      "purpose": "Ownership", "origin": "prepared", "estimatedMinutes": 4, "custom": {"keep": True}},
                     {"id": "q2", "index": "1.2", "title": "Recovery", "ask": "What failed?", "origin": "new"}]},
                {"id": "s2", "title": "Judgment", "minutes": "20m", "meta": "Trade-offs", "coach": "Probe alternatives",
                 "questions": [{"id": "q3", "index": "2.1", "title": "Alternative", "ask": "What did you reject?"}]}]}


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.spec = draft()
        self.feedback = {"format": "interview-review-v1", "base": fingerprint(self.spec), "approved": False}

    def test_draft_accepts_missing_enrichment_but_final_rejects_it(self):
        draft_items(self.spec)
        self.assertEqual(approval_errors(self.spec), [])
        with self.assertRaises(SystemExit):
            validate_spec(self.spec)
        self.assertEqual(fingerprint(self.spec), fingerprint(json.loads(json.dumps(self.spec, sort_keys=True))))

    def test_requirements_list_is_validated(self):
        draft_items({**self.spec, "requirements": [{"id": "R1", "text": "Owns runtime"}]})
        for bad in ([{"id": "R1"}], [{"id": "R1", "text": " "}], [{"id": "R1", "text": "A"}, {"id": "R1", "text": "B"}],
                    [{"id": "R1", "text": "A", "extra": 1}], {"R1": "A"}):
            with self.assertRaises(ValueError):
                draft_items({**self.spec, "requirements": bad})

    def test_edits_moves_exclusions_and_comments_preserve_other_data(self):
        original = copy.deepcopy(self.spec)
        self.feedback.update(edits=[{"kind": "question", "id": "q1", "field": "ask", "value": "Explain your own runtime."}],
                             layout=[{"id": "s2", "questions": ["q1", "q3"]}, {"id": "s1", "questions": ["q2"]}],
                             excluded=["q2"], comments=[{"kind": "question", "id": "q1", "text": "Добавить пример </script>"}])
        updated, report = apply_feedback(self.spec, self.feedback)
        self.assertEqual([s["id"] for s in updated["sections"]], ["s2"])
        q = updated["sections"][0]["questions"][0]
        self.assertEqual(q["id"], "q1")
        self.assertEqual(q["index"], "1.1")
        self.assertEqual(q["ask"], "Explain your own runtime.")
        self.assertEqual(q["custom"], {"keep": True})
        self.assertEqual(updated["analysisContext"], original["analysisContext"])
        self.assertEqual(report["comments"], self.feedback["comments"])
        self.assertNotIn("comments", updated)
        self.assertEqual(self.spec, original)
        self.assertTrue(report["approvalErrors"])

    def test_bad_payloads_are_rejected_without_mutating_input(self):
        cases = [
            {"base": "stale"}, {"approved": "yes"}, {"unexpected": True},
            {"edits": [{"kind": "question", "id": "q1", "field": "id", "value": "q9"}]},
            {"edits": [{"kind": "question", "id": "missing", "field": "ask", "value": "X"}]},
            {"layout": [{"id": "s1", "questions": ["q1", "q1", "q2"]}, {"id": "s2", "questions": ["q3"]}]},
            {"layout": [{"id": "s1", "questions": ["q1", "q2"]}]},
            {"excluded": ["missing"]}, {"excluded": ["q1", "q1"]},
            {"comments": [{"kind": "question", "id": "q9", "text": "Fix"}]},
            {"edits": [{"kind": [], "id": "q1", "field": "ask", "value": "X"}]},
        ]
        for fields in cases:
            with self.subTest(fields=fields):
                before = copy.deepcopy(self.spec)
                with self.assertRaises(ValueError):
                    apply_feedback(self.spec, {**self.feedback, **fields})
                self.assertEqual(self.spec, before)

    def test_approval_is_explicit_and_checked(self):
        _, report = apply_feedback(self.spec, {**self.feedback, "approved": True})
        self.assertTrue(report["approved"])
        for fields in [
            {"comments": [{"kind": "section", "id": "s1", "text": "Add a question"}]},
            {"edits": [{"kind": "section", "id": "s1", "field": "minutes", "value": "5m"}]},
            {"excluded": ["q1", "q2", "q3"]},
            {"edits": [{"kind": "question", "id": "q1", "field": "ask", "value": ""}]},
        ]:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                apply_feedback(self.spec, {**self.feedback, **fields, "approved": True})

    def test_section_removal_keeps_rescued_questions(self):
        feedback = {**self.feedback, "excludedSections": ["s1"],
                    "layout": [{"id": "s1", "questions": ["q2"]}, {"id": "s2", "questions": ["q1", "q3"]}]}
        updated, report = apply_feedback(self.spec, feedback)
        self.assertEqual([s["id"] for s in updated["sections"]], ["s2"])
        self.assertEqual([q["id"] for q in updated["sections"][0]["questions"]], ["q1", "q3"])
        self.assertEqual(report["excludedSections"], ["s1"])
        addition = {"id": "review-section-1", "title": "New", "minutes": ""}
        for fields in ({"excludedSections": ["missing"]}, {"excludedSections": ["s1", "s1"]}, {"excludedSections": "s1"},
                       {"addedSections": [addition], "excludedSections": [addition["id"]]}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                apply_feedback(self.spec, {**self.feedback, **fields})

    def test_timing_requests_set_minutes_and_reach_the_report(self):
        timing = [{"kind": "question", "id": "q1", "minutes": 15}, {"kind": "section", "id": "s2", "minutes": 20}]
        updated, report = apply_feedback(self.spec, {**self.feedback, "timing": timing})
        self.assertEqual(updated["sections"][0]["questions"][0]["estimatedMinutes"], 15)
        self.assertEqual(updated["sections"][1]["minutes"], "20m")
        self.assertEqual(report["timing"], timing)
        for bad in ([{"kind": "question", "id": "q9", "minutes": 5}], [{"kind": "question", "id": "q1", "minutes": 0}],
                    [{"kind": "question", "id": "q1", "minutes": 2.5}], [{"kind": "section", "id": "s1", "minutes": True}],
                    [timing[0], timing[0]], [{"kind": "question", "id": "q1"}], {"q1": 5}):
            with self.subTest(timing=bad), self.assertRaises(ValueError):
                apply_feedback(self.spec, {**self.feedback, "timing": bad})

    def test_approved_plan_drift_is_listed_and_enrichment_is_not(self):
        approved = draft()
        spec = copy.deepcopy(approved)
        spec["sections"][0]["questions"][1]["purpose"] = "Filled during enrichment"
        for q in (q for s in spec["sections"] for q in s["questions"]):
            q.update(followups=["Why?"], positives=["p"] * 8, negatives=["n"] * 6, cue="Timebox it", index="9.9")
        self.assertEqual(approved_plan_errors(spec, approved), [])
        s1, s2 = spec["sections"]
        s1["questions"][0].update(ask="Reworded", estimatedMinutes=6)
        s2["questions"].append(s1["questions"].pop(1))
        s1["minutes"] = "15m"
        self.assertEqual(approved_plan_errors(spec, approved), [
            "section s1: minutes changed", "question q1: ask changed",
            "question q1: estimatedMinutes changed", "question q2: moved s1 -> s2"])
        spec = copy.deepcopy(approved)
        spec["sections"].reverse()
        spec["sections"][0]["questions"] = [{"id": "q9", "title": "New", "ask": "?"}]
        self.assertEqual(approved_plan_errors(spec, approved), [
            "question q3: missing", "question q9: not in the approved plan",
            "section order changed: approved ['s1', 's2'], spec ['s2', 's1']"])
        self.assertEqual(approved_plan_errors(spec, {"sections": "x"}),
                         ["approved plan is malformed: it needs sections with IDs and question lists"])

    def test_identity_and_types_checked_at_render_boundary(self):
        for mutate in [lambda s: s["sections"][0]["questions"].append({"id": "q3"}),
                       lambda s: s["sections"][0].update(title=[]),
                       lambda s: s.update(durationMinutes=True),
                       lambda s: s["sections"][0]["questions"][0].update(estimatedMinutes="4"),
                       lambda s: s.update(candidateFacts=[{"text": "A claim", "source": ""}]),
                       lambda s: s.update(candidateInsights=["An unsourced guess"])]:
            s = draft()
            mutate(s)
            with self.assertRaises(ValueError):
                draft_items(s)

    def test_added_sections_keep_identity_scope_and_questions(self):
        addition = {"id": "review-section-1", "title": "Incident ownership", "minutes": ""}
        feedback = {**self.feedback, "addedSections": [addition], "comments": [
            {"kind": "section", "id": addition["id"], "text": "Нужен пример восстановления"}]}
        updated, report = apply_feedback(self.spec, feedback)
        self.assertEqual(updated["sections"][-1], {**addition, "index": "3", "requirementIds": [], "questions": []})
        self.assertEqual(report["comments"], feedback["comments"])
        self.assertTrue(report["approvalErrors"])
        again, _ = apply_feedback(updated, {**self.feedback, "base": fingerprint(updated)})
        self.assertEqual(again["sections"][-1]["id"], addition["id"])
        feedback["layout"] = [{"id": addition["id"], "questions": ["q1"]},
                              {"id": "s2", "questions": ["q3"]}, {"id": "s1", "questions": ["q2"]}]
        updated, _ = apply_feedback(self.spec, feedback)
        self.assertEqual(updated["sections"][0]["questions"][0]["id"], "q1")
        for fields in ({"addedSections": [addition, addition]},
                       {"addedSections": [{**addition, "id": "s1"}]},
                       {"addedSections": [{**addition, "title": " "}]},
                       {"addedSections": [{**addition, "minutes": 5}]},
                       {"addedSections": [{**addition, "questions": []}]},
                       {"approved": True},
                       {"layout": [{"id": "s1", "questions": ["q1", "q2"]}, {"id": "s2", "questions": ["q3"]}]}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                apply_feedback(self.spec, {**feedback, **fields})

    def test_added_questions_are_placed_by_layout_and_reported(self):
        ask = {"id": "review-question-1", "text": "Ask about on-call ownership"}
        layout = [{"id": "s1", "questions": ["q1", "q2"]}, {"id": "s2", "questions": [ask["id"], "q3"]}]
        updated, report = apply_feedback(self.spec, {**self.feedback, "addedQuestions": [ask], "layout": layout})
        self.assertEqual(updated["sections"][1]["questions"][0], {"id": ask["id"], "origin": "new", "title": "", "ask": "", "index": "2.1"})
        self.assertEqual(report["addedQuestions"], [ask])
        self.assertIn("Each included question needs a title and wording.", report["approvalErrors"])
        emptied = [{"id": "s1", "questions": []}, {"id": "s2", "questions": ["q1", "q2", "q3"]}]
        dropped, _ = apply_feedback(self.spec, {**self.feedback, "layout": emptied})
        self.assertEqual([s["id"] for s in dropped["sections"]], ["s2"], "a draft section emptied by moves is dropped")
        for fields in ({"layout": None},
                       {"addedQuestions": [ask, ask]},
                       {"addedQuestions": [{**ask, "id": "q1"}]},
                       {"addedQuestions": [{**ask, "text": 5}]},
                       {"addedQuestions": [{**ask, "section": "s2"}]},
                       {"approved": True},
                       {"layout": [{"id": "s1", "questions": ["q1", "q2"]}, {"id": "s2", "questions": ["q3"]}]}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                feedback = {**self.feedback, "addedQuestions": [ask], "layout": layout, **fields}
                apply_feedback(self.spec, {k: v for k, v in feedback.items() if v is not None})

    def test_shipped_template_and_browser_delta_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec, html = root / "draft.json", root / "review.html"
            spec.write_text(json.dumps(self.spec), encoding="utf-8")
            cmd = [sys.executable, str(SKILL / "scripts/review_plan.py")]
            subprocess.run(cmd + ["render", "--spec", str(spec), "--output", str(html)], check=True, capture_output=True)
            first = html.read_bytes()
            subprocess.run(cmd + ["render", "--spec", str(spec), "--output", str(html)], check=True, capture_output=True)
            self.assertEqual(first, html.read_bytes())
            result = subprocess.run(["node", str(Path(__file__).with_suffix(".cjs")), str(html)], check=True, capture_output=True, text=True)
            subprocess.run(["node", str(Path(__file__).with_name("test_section_drag.cjs")), str(html)], check=True, capture_output=True)
            subprocess.run(["node", str(Path(__file__).with_name("test_main_section_drag.cjs")), str(html)], check=True, capture_output=True)
            subprocess.run(["node", str(Path(__file__).with_name("test_question_drag.cjs")), str(html)], check=True, capture_output=True)
            subprocess.run(["node", str(Path(__file__).with_name("test_change_list.cjs")), str(html)], check=True, capture_output=True)
            subprocess.run(["node", str(Path(__file__).with_name("test_field_edits.cjs")), str(html)], check=True, capture_output=True)
            returned = json.loads(result.stdout)
            feedback = returned["feedback"]
            added, _ = apply_feedback(self.spec, returned["addedFeedback"])
            self.assertEqual(added["sections"][-1]["id"], "review-section-1")
            self.assertEqual(added["sections"][-1]["questions"][0]["id"], "q1")
            asked, ask_report = apply_feedback(self.spec, returned["askFeedback"])
            self.assertEqual([q["id"] for q in asked["sections"][1]["questions"]], ["q3", "review-question-1"])
            self.assertEqual(ask_report["addedQuestions"][0]["text"], "On-call ownership </interview_review>")
            updated, report = apply_feedback(self.spec, feedback)
            self.assertEqual([s["id"] for s in updated["sections"]], ["s2", "s1"])
            self.assertEqual([q["id"] for q in updated["sections"][0]["questions"]], ["q1", "q3"])
            self.assertEqual(updated["sections"][0]["questions"][0]["ask"], 'Walk through your system.')
            self.assertEqual(report["comments"][1]["text"], "Нужен пример")
            self.assertFalse(report["approved"])
            self.assertEqual(updated["sections"][1]["questions"][0]["id"], "q2")
            fb, out, report_path = root / "review-prompt.txt", root / "updated.json", root / "report.json"
            fb.write_text(returned["prompt"], encoding="utf-8")
            self.assertEqual(read_feedback(fb), feedback)
            subprocess.run(cmd + ["apply", "--spec", str(spec), "--feedback", str(fb), "--output", str(out), "--report", str(report_path)], check=True, capture_output=True)
            self.assertEqual(json.loads(out.read_text()), updated)
            feedback["base"] = "stale"
            fb.write_text(json.dumps(feedback), encoding="utf-8")
            before = out.read_bytes()
            bad = subprocess.run(cmd + ["apply", "--spec", str(spec), "--feedback", str(fb), "--output", str(out), "--report", str(report_path)], capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertTrue(bad.stderr.startswith(b"Error: This review was made for a different version"))
            self.assertEqual(out.read_bytes(), before)

    def test_ambiguous_or_malformed_prompt_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prompt.txt"
            block = '<interview_review>' + json.dumps(self.feedback) + '</interview_review>'
            for text in ('Review this plan', block + block, '<interview_review>invalid</interview_review>'):
                path.write_text(text, encoding="utf-8")
                with self.subTest(text=text), self.assertRaises(ValueError):
                    read_feedback(path)

    def test_hostile_draft_is_embedded_as_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.spec["sections"][0]["questions"][0]["ask"] = '</script><script>alert("x")</script>'
            spec, html = root / "draft.json", root / "review.html"
            spec.write_text(json.dumps(self.spec), encoding="utf-8")
            subprocess.run([sys.executable, str(SKILL / "scripts/review_plan.py"), "render", "--spec", str(spec), "--output", str(html)], check=True, capture_output=True)
            page = html.read_text()
            block = page.split('id="reviewData">', 1)[1].split('</script>', 1)[0]
            self.assertNotIn('<script>', block)
            self.assertEqual(json.loads(block)["spec"], self.spec)

    def test_final_display_order_keeps_original_section_identity(self):
        self.feedback.update(approved=True, layout=[{"id": "s2", "questions": ["q3"]}, {"id": "s1", "questions": ["q2", "q1"]}])
        updated, _ = apply_feedback(self.spec, self.feedback)
        for section in updated["sections"]:
            for q in section["questions"]:
                q.setdefault("purpose", "Probe a concrete example")
                q.update(followups=[], positives=[f"Explains observation {i}" for i in range(8)],
                         negatives=[f"Cannot explain observation {i}" for i in range(6)])
        validate_spec(updated)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec, html = root / "final.json", root / "live.html"
            spec.write_text(json.dumps(updated), encoding="utf-8")
            approved = root / "approved.json"
            approved.write_text(json.dumps({**updated, "approval": {"by": "Interviewer", "at": "2026-10-28T11:55:00+01:00", "quote": "Approved."}}), encoding="utf-8")
            subprocess.run([sys.executable, str(SKILL / "scripts/generate_interview_helper.py"), "--spec", str(spec), "--approved", str(approved), "--output", str(html)], check=True, capture_output=True)
            code = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[1],'utf8'),nodes=new Map();
const ctx={document:{addEventListener(){},querySelector(s){if(!nodes.has(s))nodes.set(s,{classList:{toggle(){}},setAttribute(){}});return nodes.get(s);}}};
vm.createContext(ctx);vm.runInContext([...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n'),ctx);
vm.runInContext('renderStatic();renderSections();',ctx);
assert.match(nodes.get('#sectionsRoot').innerHTML,/id="section-s2"[\s\S]*?class="section-number">1<\/div>/);
assert.match(nodes.get('#navList').innerHTML,/data-nav="s2"[\s\S]*?1\. Judgment/);
'''
            subprocess.run(["node", "-e", code, str(html)], check=True, capture_output=True)


    def test_round_changes_compare_by_id(self):
        previous, current = self.spec, copy.deepcopy(self.spec)
        current["sections"][0]["title"] = "Runtime systems"
        current["sections"][0]["minutes"] = "10"
        current["sections"][0]["questions"][0]["ask"] = "Walk through one system."
        current["sections"][0]["questions"][0]["index"] = "9.9"
        current["sections"].append({"id": "s3", "title": "New", "minutes": "if time", "questions": []})
        current["sections"][0]["questions"].append(current["sections"][1]["questions"].pop())
        current["sections"][0]["questions"] = [q for q in current["sections"][0]["questions"] if q["id"] != "q2"]
        marks = round_changes(previous, current)
        self.assertEqual(marks["sections"]["s1"], ["edited"])
        self.assertNotIn("s2", marks["sections"])
        self.assertEqual(marks["sections"]["s3"], ["added"])
        self.assertEqual(marks["questions"]["q1"], ["edited"])
        self.assertEqual(marks["questions"]["q3"], ["moved"])
        self.assertEqual(marks["removed"], [{"kind": "question", "title": "Recovery"}])
        time_only = copy.deepcopy(self.spec)
        time_only["sections"][0]["minutes"] = "15m"
        time_only["sections"][0]["questions"][0]["estimatedMinutes"] = 8
        self.assertEqual(round_changes(previous, time_only)["sections"]["s1"], ["time"])
        self.assertEqual(round_changes(previous, time_only)["questions"]["q1"], ["time"])

    def test_round_moves_keep_section_and_question_ids_separate(self):
        previous = draft()
        previous["sections"][0]["questions"][0]["id"] = "s1"
        current = copy.deepcopy(previous)
        current["sections"].reverse()
        marks = round_changes(previous, current)
        self.assertEqual(marks["sections"], {"s1": ["moved"]})
        self.assertEqual(marks["questions"], {}, "moving a section must not mark a same-ID question")

        previous["sections"][0]["questions"][0]["id"] = "s2"
        current = copy.deepcopy(previous)
        current["sections"][0]["questions"].reverse()
        marks = round_changes(previous, current)
        self.assertEqual(marks["sections"], {}, "moving a question must not mark a same-ID section")
        self.assertEqual(marks["questions"], {"s2": ["moved"]})

        current = copy.deepcopy(previous)
        current["sections"][1]["questions"].append(current["sections"][0]["questions"].pop(0))
        marks = round_changes(previous, current)
        self.assertEqual(marks["sections"], {})
        self.assertEqual(marks["questions"], {"s2": ["moved"]}, "real parent changes still need a mark")

    def test_previous_draft_never_blocks_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec, html, cmd = root / "draft.json", root / "review.html", [sys.executable, str(SKILL / "scripts/review_plan.py")]
            spec.write_text(json.dumps(self.spec), encoding="utf-8")
            missing = subprocess.run(cmd + ["render", "--spec", str(spec), "--previous", str(root / "gone.json"), "--output", str(html)], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 0)
            self.assertIn("Previous draft not found", missing.stderr)
            self.assertNotIn("changes", json.loads(html.read_text().split('id="reviewData">', 1)[1].split("</script>", 1)[0]))
            prev = root / "prev.json"
            prev.write_text("{not json", encoding="utf-8")
            broken = subprocess.run(cmd + ["render", "--spec", str(spec), "--previous", str(prev), "--output", str(html)], capture_output=True, text=True)
            self.assertEqual(broken.returncode, 0)
            self.assertIn("cannot be compared", broken.stderr)
            prev.write_text(json.dumps(self.spec), encoding="utf-8")
            same = subprocess.run(cmd + ["render", "--spec", str(spec), "--previous", str(prev), "--output", str(html)], capture_output=True, text=True)
            self.assertEqual(same.returncode, 0)
            self.assertIn("identical", same.stderr)
            earlier = copy.deepcopy(self.spec)
            earlier["sections"][0]["title"] = "Old title"
            prev.write_text(json.dumps(earlier), encoding="utf-8")
            ok = subprocess.run(cmd + ["render", "--spec", str(spec), "--previous", str(prev), "--output", str(html)], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0)
            data = json.loads(html.read_text().split('id="reviewData">', 1)[1].split("</script>", 1)[0])
            self.assertEqual(data["changes"]["sections"]["s1"], ["edited"])
            self.assertIn("Edited", html.read_text())


class TemporaryFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name).resolve()
        self.git("init", "-q")
        self.output = self.repo / "artifacts [custom]"
        self.command = ["uv", "run", "--script", str(SKILL / "scripts/review_plan.py")]

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True).stdout

    def ignored(self, path):
        return subprocess.run(["git", "-C", str(self.repo), "check-ignore", "-q", "--", str(path)],
                              capture_output=True).returncode == 0

    def run_cli(self, *args):
        # Deliberately run outside output-dir.
        return subprocess.run(self.command + list(map(str, args)), cwd=self.repo, check=True,
                              capture_output=True, text=True)

    def test_registration_precedes_files_and_is_exact_preserving_and_idempotent(self):
        self.output.mkdir()
        ignore = self.output / ".gitignore"
        original = b"# User rules\r\nuser-cache/"  # Preserve CRLF and a missing final newline.
        ignore.write_bytes(original)
        names = ["draft.json", "draft-v4.json", "nested [x]/!#draft*?\\.json ", "юзер [a]?.txt", ":(glob)draft.json"]
        paths = [self.output / name for name in names]
        self.run_cli("ignore", "--output-dir", self.output, "--", *paths)
        first = ignore.read_bytes()
        self.assertTrue(first.startswith(original + b"\n"))
        self.assertTrue(all(not path.exists() and self.ignored(path) for path in paths))
        self.run_cli("ignore", "--output-dir", self.output, "--", *paths)
        self.assertEqual(ignore.read_bytes(), first)
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        visible = ["interview-helper.html", "interview-spec.json", "approved-plan.json", "CV.pdf",
                   "feedback.txt", "evidence.json", "requirements.json", "preparation-state.json",
                   "unrelated.html", "draft-v5.json", "nested [x]/!#draftZZ\\.json ", "other/draft.json"]
        for name in visible:
            path = self.output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            self.assertFalse(self.ignored(path), name)
        self.assertFalse(self.ignored(ignore))
        self.assertTrue(self.ignored(self.output / "user-cache/file"))
        status = self.git("status", "--porcelain", "--untracked-files=all").decode()
        self.assertIn("interview-helper.html", status)
        self.assertIn(".gitignore", status)

    def test_new_output_roundtrip_registers_all_outputs_before_each_write(self):
        base = self.output / "nested" / "draft.json"
        self.run_cli("ignore", "--output-dir", self.output, "--", base)
        self.assertTrue((self.output / ".gitignore").exists())
        self.assertFalse(base.exists())
        base.parent.mkdir()
        base.write_text(json.dumps(draft()), encoding="utf-8")
        original = base.read_bytes()
        review = self.output / "review.html"
        feedback = self.output / "review-prompt.txt"
        report = self.output / "nested/report.json"

        def invoke(arguments, outputs):
            write = Path.write_text

            def checked_write(path, *args, **kwargs):
                if path in outputs:
                    self.assertTrue(all(self.ignored(p) for p in outputs), "All outputs must be ignored before the first write")
                return write(path, *args, **kwargs)

            with patch.object(sys, "argv", ["review_plan.py", *map(str, arguments)]), patch.object(Path, "write_text", checked_write):
                main()

        invoke(["render", "--output-dir", self.output, "--spec", base, "--output", review], [review])
        self.run_cli("ignore", "--output-dir", self.output, "--", feedback)
        payload = {"format": "interview-review-v1", "base": fingerprint(draft()), "approved": False,
                   "edits": [{"kind": "question", "id": "q1", "field": "ask", "value": "Describe recovery."}]}
        feedback.write_text(json.dumps(payload), encoding="utf-8")
        invoke(["apply", "--output-dir", self.output, "--spec", base, "--feedback", feedback,
                "--output", base, "--report", report], [base, report])
        self.assertNotEqual(base.read_bytes(), original)
        invoke(["render", "--output-dir", self.output, "--spec", base, "--previous", review,
                "--output", review], [review])
        result = json.loads(base.read_text())
        self.assertEqual(result["sections"][0]["questions"][0]["ask"], "Describe recovery.")
        self.assertEqual(result["sections"][0]["questions"][0]["id"], "q1")
        page = json.loads(review.read_text().split('id="reviewData">', 1)[1].split("</script>", 1)[0])
        self.assertEqual(page["changes"]["questions"], {"q1": ["edited"]})
        self.assertTrue(all(self.ignored(p) for p in (base, review, feedback, report)))
        before = (self.output / ".gitignore").read_bytes()
        contents = {path: path.read_bytes() for path in (base, review, report)}
        stale = subprocess.run(self.command + ["apply", "--spec", str(base), "--feedback", str(feedback),
                                              "--output", str(base), "--report", str(report)],
                               cwd=self.repo, capture_output=True, text=True)
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("different version", stale.stderr)
        self.assertEqual((self.output / ".gitignore").read_bytes(), before)
        self.assertEqual({path: path.read_bytes() for path in contents}, contents)
        payload.update(base=fingerprint(result), edits=[{"kind": "section", "id": "s1", "field": "title", "value": "New title"}])
        feedback.write_text(json.dumps(payload), encoding="utf-8")
        invoke(["apply", "--output-dir", self.output, "--spec", base, "--feedback", feedback,
                "--output", base, "--report", report], [base, report])
        invoke(["render", "--output-dir", self.output, "--spec", base, "--previous", review,
                "--output", review], [review])
        page = json.loads(review.read_text().split('id="reviewData">', 1)[1].split("</script>", 1)[0])
        self.assertEqual(page["changes"]["sections"], {"s1": ["edited"]})
        self.assertEqual(page["changes"]["questions"], {}, "Compare to the immediately preceding round")
        self.assertEqual((self.output / ".gitignore").read_bytes(), before)
        files = {path.relative_to(self.output).as_posix() for path in self.output.rglob("*") if path.is_file()}
        self.assertEqual(files, {".gitignore", "nested/draft.json", "review.html", "review-prompt.txt", "nested/report.json"})

    def test_in_place_apply_still_rejects_feedback_and_report_collisions(self):
        self.output.mkdir()
        base, feedback, report = (self.output / name for name in ("draft.json", "feedback.txt", "report.json"))
        base.write_text(json.dumps(draft()), encoding="utf-8")
        feedback.write_text(json.dumps({"format": "interview-review-v1", "base": fingerprint(draft()), "approved": False}), encoding="utf-8")
        report.write_text("original report", encoding="utf-8")
        original = {path: path.read_bytes() for path in (base, feedback, report)}
        for fb, out, rep in ((base, base, report), (feedback, base, base), (feedback, feedback, report),
                             (feedback, report, report), (feedback, base, feedback)):
            result = subprocess.run(self.command + ["apply", "--spec", str(base), "--feedback", str(fb),
                                                   "--output", str(out), "--report", str(rep)],
                                    cwd=self.repo, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("separate files", result.stderr)
            self.assertEqual({path: path.read_bytes() for path in original}, original)

    def test_tracked_temporary_warns_without_changing_index(self):
        self.output.mkdir()
        path = self.output / "draft[1].json"
        path.write_text("original", encoding="utf-8")
        self.git("add", "--", str(path))
        before = self.git("ls-files", "--stage", "-z")
        result = self.run_cli("ignore", "--output-dir", self.output, "--", path)
        self.assertIn("already tracked", result.stderr)
        self.assertEqual(self.git("ls-files", "--stage", "-z"), before)
        self.assertEqual(path.read_text(), "original")

    def test_non_repository_needs_no_gitignore(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "output"
            ignore_temporary(output, [output / "draft.json"])
            self.assertFalse((output / ".gitignore").exists())
            self.assertFalse((output / "draft.json").exists())

    def test_unsafe_paths_and_nested_overrides_stop_before_output(self):
        for path in (self.repo / "outside.json", self.output / ".gitignore", self.output / "bad\nname"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                ignore_temporary(self.output, [path])
        self.assertFalse((self.output / ".gitignore").exists())
        nested = self.output / "nested"
        nested.mkdir(parents=True)
        (nested / ".gitignore").write_text("!draft.json\n", encoding="utf-8")
        base = self.output / "base.json"
        base.write_text(json.dumps(draft()), encoding="utf-8")
        output = nested / "draft.json"
        result = subprocess.run(self.command + ["render", "--output-dir", str(self.output), "--spec", str(base),
                                               "--output", str(output)], cwd=self.repo, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not ignore", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
