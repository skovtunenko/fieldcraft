#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Background completeness and renderer regressions with synthetic professional context."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "skills").is_dir())
SKILL = next(ROOT.glob("skills/**/interview-helper-builder/SKILL.md")).parent
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
from generate_interview_helper import approval_errors, approved_plan_errors, validate_spec
from review_plan import apply_feedback, fingerprint
from validate_interview_helper import validate_embedded_spec


def spec():
    return {
        "candidate": "Test Candidate", "role": "Platform Engineer", "durationMinutes": 20,
        "analysisContext": [], "outOfScope": ["Motivation"],
        "scoreDimensions": [{"key": "ownership", "label": "Ownership"}],
        "sections": [{"id": "s1", "index": "1", "title": "Systems", "minutes": "20m", "meta": "", "coach": "",
                      "questions": [{"id": "q1", "index": "1.1", "title": "Ownership", "purpose": "Decisions",
                                     "ask": "Which failure did you resolve?", "estimatedMinutes": 10,
                                     "followups": [], "positives": [f"Positive {i}" for i in range(8)],
                                     "negatives": [f"Negative {i}" for i in range(6)]}]}]}


APPROVAL = {"by": "Interviewer", "at": "2026-10-28T11:55:00+01:00", "quote": "Plan approved, generate it."}


def cv_profile():
    return {"portrait": "According to cv.md, a platform engineer who claims ownership of a payment runtime.",
            "timeline": [{"from": "2020", "to": "2023", "org": "Example & Co", "role": "Engineer",
                          "scale": "CV: three services", "source": "cv.md"}],
            "standouts": [{"text": "Claims payment runtime ownership", "source": "cv.md"}],
            "inconsistencies": [], "probes": []}


class BackgroundTests(unittest.TestCase):
    def test_context_requires_portrait_even_in_legacy_specs(self):
        for evidence in ({"candidateBackgroundRequired": True},
                         {"candidateCareer": [{"org": "Example role", "source": "CV"}]},
                         {"candidateFacts": [{"text": "Claims service ownership", "source": "CV"}]},
                         {"candidateInsights": [{"text": "Interpretation: possible depth", "source": "CV"}]},
                         {"candidateBackgroundRequired": False, "candidateFacts": [{"text": "Owns services", "source": "CV"}]}):
            for profile in (None, {}, {"portrait": " "}, {"standouts": [{"text": "Owns services", "source": "CV"}]}):
                with self.subTest(evidence=evidence, profile=profile):
                    value = {**spec(), **evidence, "candidateProfile": profile}
                    with self.assertRaisesRegex(SystemExit, "professional context requires candidateProfile"):
                        validate_spec(value)
                    self.assertIn("professional context requires", validate_embedded_spec("const CONFIG=" + json.dumps(value) + ";")[0])

    def test_flag_is_a_boolean(self):
        for flag in ("false", 0, None, []):
            with self.subTest(flag=flag), self.assertRaisesRegex(SystemExit, "must be a boolean"):
                validate_spec({**spec(), "candidateBackgroundRequired": flag})

    def test_background_survives_review_and_preserves_approved_plan(self):
        draft = {**spec(), "candidateBackgroundRequired": True, "candidateCareer": copy.deepcopy(cv_profile()["timeline"]),
                 "candidateFacts": [{"text": "Claims service ownership", "source": "CV"}]}
        approved = copy.deepcopy(draft)
        enriched = {**draft, "candidateProfile": cv_profile()}
        updated, _ = apply_feedback(enriched, {"format": "interview-review-v1", "base": fingerprint(enriched), "approved": False})
        self.assertTrue(updated["candidateBackgroundRequired"])
        self.assertEqual(updated["candidateCareer"], enriched["candidateCareer"])
        self.assertEqual(updated["candidateProfile"], enriched["candidateProfile"])
        self.assertEqual(updated["sections"], approved["sections"])
        self.assertEqual(approved_plan_errors(updated, approved), [])
        for field, value in (("id", "q2"), ("ask", "Changed?"), ("estimatedMinutes", 15)):
            changed = copy.deepcopy(updated)
            changed["sections"][0]["questions"][0][field] = value
            self.assertTrue(approved_plan_errors(changed, approved), field)
        changed = copy.deepcopy(updated)
        changed["sections"][0]["minutes"] = "25m"
        self.assertTrue(approved_plan_errors(changed, approved))
        two = copy.deepcopy(updated)
        two["sections"].append({**copy.deepcopy(two["sections"][0]), "id": "s2", "questions": []})
        self.assertTrue(approved_plan_errors({**two, "sections": list(reversed(two["sections"]))}, two))
        pair = copy.deepcopy(updated)
        pair["sections"][0]["questions"].append({**copy.deepcopy(pair["sections"][0]["questions"][0]), "id": "q2"})
        reordered = copy.deepcopy(pair)
        reordered["sections"][0]["questions"].reverse()
        self.assertTrue(approved_plan_errors(reordered, pair))

    def test_approved_copy_needs_an_approval_record(self):
        self.assertEqual(approval_errors({**spec(), "approval": APPROVAL}), [])
        for record in (None, "yes", {}, {**APPROVAL, "quote": " "}, {**APPROVAL, "by": 1}, {**APPROVAL, "at": "today"}):
            with self.subTest(record=record):
                self.assertTrue(approval_errors({**spec(), "approval": record}))
        self.assertEqual(approval_errors(spec()), ["no approval record"])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "spec.json").write_text(json.dumps(spec()), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPTS / "generate_interview_helper.py"), "--spec", str(tmp / "spec.json"),
                                     "--approved", str(tmp / "spec.json"), "--output", str(tmp / "out.html")],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no approval record", result.stderr)
            self.assertFalse((tmp / "out.html").exists())
            result = subprocess.run([sys.executable, str(SCRIPTS / "generate_interview_helper.py"), "--spec", str(tmp / "spec.json"),
                                     "--output", str(tmp / "out.html")], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--approved", result.stderr)
            self.assertFalse((tmp / "out.html").exists())

    def test_generated_data_and_executed_background_render(self):
        feedback = {"portrait": "Round 1 feedback (feedback.md) observed clear incident reasoning.",
                    "probes": [{"text": "Ownership remains untested", "source": "Round 1 feedback"}]}
        cases = {"cv": {"candidateBackgroundRequired": True, "candidateCareer": copy.deepcopy(cv_profile()["timeline"]), "candidateProfile": cv_profile()},
                 "feedback": {"candidateBackgroundRequired": True, "candidateCareer": [], "candidateProfile": feedback},
                 "none": {"candidateBackgroundRequired": False, "candidateCareer": []}}
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for name, context in cases.items():
                with self.subTest(name=name):
                    value = {**spec(), **context}
                    draft = tmp / "spec.json"
                    approved = tmp / "approved.json"
                    output = tmp / f"{name}.html"
                    draft.write_text(json.dumps(value), encoding="utf-8")
                    approved.write_text(json.dumps({**spec(), "approval": APPROVAL}), encoding="utf-8")
                    command = [sys.executable, str(SCRIPTS / "generate_interview_helper.py"), "--spec", str(draft),
                               "--approved", str(approved), "--output", str(output), "--generated-at", "2026-10-28T12:00:00+01:00"]
                    subprocess.run(command, check=True, capture_output=True)
                    first = output.read_text(encoding="utf-8")
                    subprocess.run(command, check=True, capture_output=True)
                    self.assertEqual(first, output.read_text(encoding="utf-8"))
                    subprocess.run([sys.executable, str(SCRIPTS / "validate_interview_helper.py"), str(output)], check=True, capture_output=True)
                    renderer = Path(__file__).with_name("test_background.cjs")
                    subprocess.run(["node", str(renderer), str(output), name], check=True)
                    if name == "cv":
                        broken = tmp / "broken.html"
                        broken.write_text(first.replace('function renderProfile(){', 'function renderProfile(){return;'), encoding="utf-8")
                        self.assertNotEqual(subprocess.run(["node", str(renderer), str(broken), name], capture_output=True).returncode, 0)
                        missing = dict(value)
                        del missing["candidateProfile"]
                        broken.write_text(first.replace(json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("&", "\\u0026"),
                                                        json.dumps(missing, ensure_ascii=False, separators=(",", ":"))), encoding="utf-8")
                        result = subprocess.run([sys.executable, str(SCRIPTS / "validate_interview_helper.py"), str(broken)], capture_output=True, text=True)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("professional context requires", result.stdout)

    def test_career_inventory_requires_full_identity_coverage(self):
        roles = [{"org": f"Employer {i}", "role": "Engineer", "from": str(2000+i), "to": str(2002+i),
                  "source": f"cv.md · role {i}"} for i in range(7)]
        value = {**spec(), "candidateBackgroundRequired": True, "candidateCareer": roles,
                 "candidateProfile": {"portrait": "According to cv.md, seven professional positions.", "timeline": copy.deepcopy(roles)}}
        validate_spec(value)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            draft, output = tmp/"spec.json", tmp/"seven.html"
            draft.write_text(json.dumps(value))
            (tmp/"approved.json").write_text(json.dumps({**value, "approval": APPROVAL}))
            command = [sys.executable, str(SCRIPTS/"generate_interview_helper.py"), "--spec", str(draft), "--approved", str(tmp/"approved.json"), "--output", str(output)]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertIn("Career coverage: 7/7 source entries covered", result.stdout)
            self.assertIn("Approved plan: checked", result.stdout)
            subprocess.run(["node", str(Path(__file__).with_name("test_background.cjs")), str(output), "seven"], check=True)
            broken = copy.deepcopy(value)
            broken["candidateProfile"]["timeline"] = roles[:2]
            draft.write_text(json.dumps(broken))
            output.unlink()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertIn("career coverage mismatch", result.stderr)
        for variant in (roles[:2], roles[:6]+[roles[0]]):
            broken = copy.deepcopy(value)
            broken["candidateProfile"]["timeline"] = copy.deepcopy(variant)
            with self.assertRaisesRegex(SystemExit, "career coverage"):
                validate_spec(broken)
            self.assertTrue(validate_embedded_spec("const CONFIG="+json.dumps(broken)+";"))
        for field in ("org", "role", "from", "to", "source"):
            broken = copy.deepcopy(value)
            broken["candidateProfile"]["timeline"][0][field] = "2001" if field in ("from", "to") else "Changed"
            with self.subTest(field=field), self.assertRaisesRegex(SystemExit, "career coverage mismatch"):
                validate_spec(broken)
        del value["candidateCareer"]
        with self.assertRaisesRegex(SystemExit, "candidateCareer inventory is required"):
            validate_spec(value)
        for invalid in (None, {}, "summary", [None]):
            with self.subTest(invalid=invalid), self.assertRaises(SystemExit):
                validate_spec({**value, "candidateCareer": invalid})

    def test_overflow_and_unknown_dates_stay_visible(self):
        roles = [{"org": f"Employer {i}", "role": "Engineer", "from": str(2000+i), "to": str(2001+i),
                  "source": "cv.md"} for i in range(13)]
        unknown = {"org": "Independent <lab>", "role": "Maintainer", "dateNote": "Around 1999; end date not supplied", "source": "cv.md"}
        value = {**spec(), "candidateBackgroundRequired": True, "candidateCareer": roles+[unknown],
                 "candidateProfile": {"portrait": "According to cv.md, thirteen positions and a lab.",
                                      "timeline": copy.deepcopy(roles[:12]),
                                      "additionalExperience": [{**roles[12], "reason": "Timeline limited to 12 entries"},
                                                               {**unknown, "reason": "Exact career dates unavailable"}]}}
        validate_spec(value)
        for mutation in ("to", "reason"):
            broken = copy.deepcopy(value)
            if mutation == "to":
                del broken["candidateProfile"]["timeline"][0]["to"]
            else:
                del broken["candidateProfile"]["additionalExperience"][0]["reason"]
            with self.subTest(mutation=mutation), self.assertRaises(SystemExit):
                validate_spec(broken)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            draft, output = tmp/"spec.json", tmp/"overflow.html"
            draft.write_text(json.dumps(value))
            (tmp/"approved.json").write_text(json.dumps({**value, "approval": APPROVAL}))
            subprocess.run([sys.executable, str(SCRIPTS/"generate_interview_helper.py"), "--spec", str(draft), "--approved", str(tmp/"approved.json"), "--output", str(output)], check=True, capture_output=True)
            subprocess.run(["node", str(Path(__file__).with_name("test_background.cjs")), str(output), "overflow"], check=True)


if __name__ == "__main__":
    unittest.main()
