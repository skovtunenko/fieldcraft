# Grader prompt

Two grader tasks. Give each to a fresh agent from the repository root. Replace
`<run>` with the run directory, for example `<runs>/2026-10-19-v0.2`, where
`<runs>` is the results folder named in `cases.md`.

## Rubric grader

```text
Grade the outputs in <run>/ against
build/**/ambition-lens/evals/cases.md.

Read completely: skills/**/ambition-lens/SKILL.md, the cases file,
and every <run>/C*.md output with its tool-call list. Do not read <run>/compare/,
other runs, git history, or OpenSpec files. Do not edit the skill or the outputs.

For every case with an output: check every common-rubric box (where the case
says it applies) and every case box. For each box write pass or fail and one
line of evidence quoted from the output. Count words with `wc -w`. Apply the
swap test by comparing prompts across cases. A case passes only when all its
boxes pass. Do not repair an output before grading it.

Write <run>/grades.md: a summary table (case, verdict, failed boxes, words),
then per-case details, then the exact SKILL.md instruction gap behind each
failure. End with one verdict: release-ready, revise, or
evaluation-inconclusive, and the smallest next action.
```

## Blind comparison grader

```text
Compare anonymised answer pairs in <run>/compare/. Each case has C<n>-A.md
and C<n>-B.md: two answers to the same conversation, which you find under that
case in build/**/ambition-lens/evals/cases.md. Read only those
files; do not read key.md, SKILL.md, or anything else in the run.

For each pair, score A and B from 1 to 5 on:
- Understanding: shows it understood the conversation's facts, decisions,
  and dead ends.
- Ambition: would change what the user does next, beyond the obvious.
- Actionability: the user can start within two minutes.
- Grounding: proposals depend on this conversation, not generic advice.
- Clarity: a reader outside the field understands it in one read, without
  asking for a plain-words version.
Then pick a winner (A, B, or tie) with a two-line reason.

Write <run>/comparison.md with a table and per-pair reasoning. Do not guess
which answer used a skill.
```
