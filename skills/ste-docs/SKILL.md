---
name: ste-docs
description: Writes design docs, RFCs, ADRs and specs in ASD-STE100 Simplified Technical English with given-new flow. Use when writing or editing such a document; not for chat replies.
metadata:
  version: "2026.11.25.1"
  kind: rule
---

# STE docs

Write documents in ASD-STE100 with given-new flow: topic sentence first, every term defined at or before its first use (never in a later section: a Terms list comes before any text that uses its terms), every logical link written as a word ("because", "but", "if"), also when you split a long sentence.

Keep every fact, number and decision from the source, and add none: no new consequence, benefit, default, step or failure handling. Write each one the reader needs as an open question, and do not state as decided what an open question leaves open.

This applies to the document only; chat replies keep their own style. Leave code, identifiers and keywords the template requires (MUST, WHEN/THEN) as they are.

Core STE rules (Issue 9):

- Sentences: 20 words or fewer in procedures, 25 or fewer in descriptions.
- One topic per paragraph, 6 sentences or fewer.
- Active voice, simple tenses, one instruction per sentence, one action per numbered step.
- Write the precondition of a step as a condition in that step ("Only after all health checks pass, …").
- -ing words only inside technical nouns; noun clusters of 3 words or fewer.
- One word, one meaning; keep articles, subjects and verbs.

The STE dictionary is not in your context: call the result "STE style", not "STE-compliant".
