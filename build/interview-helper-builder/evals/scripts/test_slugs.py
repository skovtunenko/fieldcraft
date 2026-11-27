#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""State keys: the slug keeps ASCII keys, separates non-Latin text, matches the template JS."""
import json
import re
import subprocess
import unittest

from test_background import spec
from generate_interview_helper import slug, validate_spec

JS = "function simpleSlug(v){return String(v||'interview').toLowerCase().normalize('NFC').replace(/[^\\p{L}\\p{M}\\p{N}]+/gu,'-').replace(/^-|-$/g,'')||'interview'}"
OLD = lambda v: re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", str(v or "interview").lower())) or "interview"

ENGLISH = ["Owns the rollback decision", "Names a metric, e.g. p99 < 200ms", "Blames the team; no 'I' statements",
           "Why?", "Uses 3 retries & backoff", "  Leading and trailing  ", "A--B__C", "", "---"]
MIXED = ENGLISH + ["Почему так?", "Что бы вы изменили?", "ПОЧЕМУ ТАК", "café", "café", "日本語のテキスト", "中文 测试",
                   "🔥 only emoji 🔥", "🔥", "Ünïcödé 123", "ǅ", "İstanbul", "ΟΔΥΣΣΕΥΣ", "हिन्दी पाठ", "x²y", "٣٤٥"]


def with_signals(kind, texts):
    value = spec()
    q = value["sections"][0]["questions"][0]
    if kind == "followups":
        q["followups"] = texts
    else:
        q[kind] = texts + [f"Other {i}" for i in range(8 - len(texts))]
    return value


class SlugTests(unittest.TestCase):
    def test_ascii_keys_match_the_old_regex(self):
        for text in ENGLISH:
            self.assertEqual(slug(text), OLD(text), text)

    def test_non_latin_texts_get_distinct_slugs(self):
        self.assertNotEqual(slug("Почему так?"), slug("Что бы вы изменили?"))
        self.assertNotIn(slug("日本語のテキスト"), ("interview", ""))

    def test_collisions_are_rejected_per_question(self):
        cases = {"followups": ["Why?", "Why!"], "positives": ["Clear owner", "clear  owner!"],
                 "negatives": ["Blames others", "Blames others?"]}
        for kind, texts in cases.items():
            value = with_signals(kind, texts)
            if kind == "negatives":
                value["sections"][0]["questions"][0]["negatives"] = texts + [f"Other {i}" for i in range(4)]
            with self.subTest(kind=kind), self.assertRaises(SystemExit) as ctx:
                validate_spec(value)
            msg = str(ctx.exception)
            self.assertIn("q1", msg)
            self.assertIn(texts[0], msg)
            self.assertIn(texts[1], msg)
        validate_spec(with_signals("followups", ["Почему так?", "Что бы вы изменили?"]))

    def test_js_and_python_agree(self):
        script = JS + ";console.log(JSON.stringify(" + json.dumps(MIXED) + ".map(simpleSlug)))"
        out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout
        for text, js in zip(MIXED, json.loads(out)):
            self.assertEqual(slug(text), js, repr(text))


if __name__ == "__main__":
    unittest.main()
