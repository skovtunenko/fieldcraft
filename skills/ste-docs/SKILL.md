---
name: ste-docs
description: Writes design docs, RFCs, ADRs and specs in ASD-STE100 Simplified Technical English with given-new flow. Use when writing or editing such a document; not for chat replies.
metadata:
  version: "2026.11.20.1"
  kind: rule
---

# STE docs

Write documents in ASD-STE100 with given-new flow: topic sentence first, every term defined before use, every logical link written as a word.

This applies to the document only; chat replies keep their own style. Leave code, identifiers and keywords the template requires (MUST, WHEN/THEN) as they are.

Core STE rules (Issue 9):

- Sentences: 20 words or fewer in procedures, 25 or fewer in descriptions.
- One topic per paragraph, 6 sentences or fewer.
- Active voice, simple tenses, one instruction per sentence.
- -ing words only inside technical nouns; noun clusters of 3 words or fewer.
- One word, one meaning; keep articles, subjects and verbs.

The STE dictionary is not in your context: call the result "STE style", not "STE-compliant".
