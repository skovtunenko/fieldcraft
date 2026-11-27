# Grader brief: interview-helper-builder behavioral run

You grade one finished run of one scenario. You judge what happened; you do
not fix the skill.

## Inputs

- `evals/cases.md`: the cases and their pass conditions. Grade every case
  whose Scenario column names this run's scenario or says `all` for S1–S3. Grade
  S4 only against C19 and the expected behavior in its task. Mechanical
  cases (`M*`) are not graded here.
- `evals/tasks/<S>.md`: the scenario. Its **Expected facts** section is the
  answer key; the interviewer script tells you which replies were scripted.
- `<run-dir>/transcript.md`: every agent message and every scripted reply, in
  order, including unscripted questions the orchestrator answered with the
  fallback reply.
- `<run-dir>/workspace/`: the files the run produced, chiefly
  `*-interview-spec.json` and `*-interview-helper.html`, plus the preparation
  drafts/review pages and returned feedback when the structure gate ran.
- `<run-dir>/skill/` and `<run-dir>/skill.manifest`: the skill copy the agent
  used and its checksum baseline.
- The skill copy's `SKILL.md` and `references/`: the text you cite for defects.

## Mechanical steps

For S4, run only the skill-copy integrity check below; absence of generated
interview JSON and HTML is expected in help-only runs. For the active-draft
variant, compare supplied draft and approved-plan bytes before and after.

Run these from the repository root before judging anything, and keep their
output for the Evidence column. `<skill>` is
the skill folder `skills/**/interview-helper-builder/`; `<development>` is
the eval folder `build/**/interview-helper-builder/evals/`.

```bash
uv run --script <development>/scripts/check_spec.py <run-dir>/workspace/<candidate>-interview-spec.json
bash <development>/scripts/prepare_run.sh --verify <run-dir>
uv run --script <skill>/scripts/validate_interview_helper.py <run-dir>/workspace/<candidate>-interview-helper.html
```

If the spec or HTML is missing, or sits outside `<run-dir>/workspace/`, record
that; do not search elsewhere for a substitute.

## Rules

- A `pass` needs cited evidence: a quote from the transcript (with its turn
  number) or a file name plus the JSON field or HTML element.
- Absence of evidence is a `fail`. If the transcript does not record what a
  case needs (for example when a file was written), the case fails and the
  Evidence cell says what was not recorded.
- `n.a.` only when the case's own condition cannot arise in this run, and the
  Evidence cell says why (for example, C12 on S1).
- Compare facts against the Expected facts section, not against your own
  reading of the fixtures.
- A case with several conditions passes only if every condition passes; name
  the failing condition.
- C11: paste the summary line of `check_spec.py` (`PASS: ...` or `FAIL: ...`)
  and every `FAIL:` line. Its `WARN:` lines feed C15; they do not decide C11.
- C13: paste the `--verify` result (`SKILL COPY UNCHANGED` or the changed
  paths) and the validator's `VALID:` line or its errors. Confirm from the
  transcript that the final reply names the HTML path and does not reproduce
  the spec.
- C9/C10: inspect the review's embedded `reviewData` and the draft at the time
  it was shown; review HTML and incomplete JSON before approval are expected.
  Distinguish them from the final enriched spec and live interview HTML.
- C15: sample the first question of the first timeboxed section, of the
  middle timeboxed section (lower middle when even), and of the last
  timeboxed section, counting only sections that test a requirement; skip
  `"if time"` sections and sections shown as `[-]`. For each sampled question,
  quote its signals and apply the Signals section of
  `references/interview-design.md`: at least one signal references a CV claim
  or requirement from this candidate; at least one graded pair of the same
  dimension; no signal joins two checks with "and"; each signal under about
  12 words. Name the question ID and quote each offending signal.
- Grade the agent's messages, not its intentions: a promise to do something
  later does not count as doing it.
- Do not propose fixes. For a defect, name the responsible sentence and stop.

## Output

Return exactly these three parts.

### 1. Results table

```markdown
| Case | Result | Evidence |
| --- | --- | --- |
| C1 | pass | Turn 1: "Candidate: Marek Halloway ... Employer: Quillmark Insurance" |
| C11 | fail | check_spec.py: "FAIL: 14 questions, 1 failures, 2 warnings"; "FAIL: q3: 7 positives, expected 8-12" |
```

One row per applicable case, in `cases.md` order. Result is one of `pass`,
`fail`, `n.a.`.

### 2. Defects

One line per failed condition:

```text
<case>: <what the skill text allowed or caused> - <file>: "<responsible sentence>"
```

Quote the SKILL.md or reference sentence that permitted or produced the
behavior. When no sentence covers the behavior, say "no sentence covers
<behavior>" and name the step or section where it would belong.

### 3. Unscripted questions

Every question the agent asked that the interviewer script does not answer,
verbatim, with its turn number, or `none`:

```text
Turn <n>: "<question>"
```
