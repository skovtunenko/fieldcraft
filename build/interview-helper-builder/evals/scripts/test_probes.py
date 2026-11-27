#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Follow-up probe pairs: accepted shapes and rejected pairings."""
import unittest

from test_background import spec
from generate_interview_helper import validate_spec


def probe_spec(*followups):
    value = spec()
    value["sections"][0]["questions"][0]["followups"] = list(followups)
    return value


def signals():
    q = spec()["sections"][0]["questions"][0]
    return q["positives"][0], q["negatives"][0]


class ProbeTests(unittest.TestCase):
    def test_strings_and_probe_objects_are_valid(self):
        pos, neg = signals()
        validate_spec(probe_spec("Plain follow-up?"))
        validate_spec(probe_spec(
            {"text": "Both?", "listenFor": pos, "warnIf": neg},
            {"text": "Positive only?", "listenFor": spec()["sections"][0]["questions"][0]["positives"][1]},
            "Plain follow-up?",
        ))

    def test_invalid_probes_fail(self):
        pos, neg = signals()
        cases = {
            "must be text or an object": [1],
            "non-empty text": [{"text": " ", "listenFor": pos}],
            "needs listenFor or warnIf": [{"text": "No pair?"}],
            "unknown fields": [{"text": "Typo?", "listenfor": pos}],
            "listenFor is not one of its positives": [{"text": "Wrong pool?", "listenFor": neg}],
            "warnIf is not one of its negatives": [{"text": "Wrong pool?", "warnIf": pos}],
            "pairs one signal with two follow-ups": [{"text": "A?", "listenFor": pos}, {"text": "B?", "listenFor": pos}],
            "follow-ups that share one state key": ["Same?", {"text": "Same?", "warnIf": neg}],
        }
        for message, followups in cases.items():
            with self.subTest(message=message), self.assertRaisesRegex(SystemExit, message):
                validate_spec(probe_spec(*followups))


class InstructionTests(unittest.TestCase):
    def test_analysis_instructions(self):
        value = spec()
        value["analysisInstructions"] = ["Score against the L1-L5 ladder."]
        validate_spec(value)
        for bad in ("one string", [""], ["two\nlines"], [3]):
            value["analysisInstructions"] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(SystemExit, "analysisInstructions"):
                validate_spec(value)


if __name__ == "__main__":
    unittest.main()
