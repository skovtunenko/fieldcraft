#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Requirement links and approval boundaries for the live coverage renderer."""
import copy
import unittest

from test_background import spec
from generate_interview_helper import approved_plan_errors, validate_spec


def mapped_spec():
    value = spec()
    value["requirements"] = [{"id": "R1", "text": "Ownership"}, {"id": "R2", "text": "Runtime"}]
    value["sections"][0]["requirementIds"] = ["R1"]
    value["sections"][0]["questions"][0]["requirementIds"] = ["R1"]
    return value


class RequirementTests(unittest.TestCase):
    def test_legacy_and_explicit_maps_are_valid(self):
        validate_spec(spec())
        validate_spec(mapped_spec())
        legacy = mapped_spec()
        del legacy["sections"][0]["questions"][0]["requirementIds"]
        validate_spec(legacy)

    def test_invalid_catalogue_fails(self):
        for rows in (None, {}, [{"id": "R1"}], [{"id": " ", "text": "x"}],
                     [{"id": "R1", "text": "x"}, {"id": "R1", "text": "y"}]):
            with self.subTest(rows=rows), self.assertRaisesRegex(SystemExit, "requirement"):
                validate_spec({**mapped_spec(), "requirements": rows})

    def test_unknown_duplicate_and_out_of_section_links_fail(self):
        for target in ("section", "question"):
            for links in ("R1", [1], ["missing"], ["R1", "R1"]):
                value = mapped_spec()
                item = value["sections"][0]
                if target == "question":
                    item = item["questions"][0]
                item["requirementIds"] = links
                with self.subTest(target=target, links=links), self.assertRaisesRegex(SystemExit, "requirementIds"):
                    validate_spec(value)
        value = mapped_spec()
        value["sections"][0]["questions"][0]["requirementIds"] = ["R2"]
        with self.assertRaisesRegex(SystemExit, "must belong to its section"):
            validate_spec(value)

    def test_approved_matrix_and_links_cannot_drift(self):
        approved = mapped_spec()
        self.assertEqual(approved_plan_errors(approved, approved), [])
        mutations = [lambda v: v["requirements"][0].update(text="Changed"),
                     lambda v: v["sections"][0].update(requirementIds=["R1", "R2"]),
                     lambda v: v["sections"][0]["questions"][0].update(requirementIds=[])]
        for mutate in mutations:
            value = copy.deepcopy(approved)
            mutate(value)
            self.assertTrue(approved_plan_errors(value, approved))
        draft = copy.deepcopy(approved)
        del draft["sections"][0]["questions"][0]["requirementIds"]
        self.assertEqual(approved_plan_errors(approved, draft), [])


if __name__ == "__main__":
    unittest.main()
