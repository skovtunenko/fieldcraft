# Eval cases

The skill makes a document follow the countable rules of ASD-STE100 and a
given-new flow, and leaves chat replies alone. Boxes marked **[script]** are
checked by `check_ste.py`; the grader checks the other boxes.

## How to run

The steps work in any agent host (Claude Code, Codex, Copilot).

1. **Generate.** Start one fresh session per case and per arm, in an empty
   scratch folder.
   - Skill arm: the skill is installed, and the first message is
     "Use the ste-docs skill for this session." followed by the case prompt.
     Case S5 is the exception: it does not name the skill.
   - Baseline arm (cases marked _baseline_): the same prompt in a session
     without the skill.
   Save each run in
   `<runs>/<date>-v<version>/<case>-<arm>-r<i>/`: the
   written document under `docs/`, the final chat reply as `reply.md`, and
   the tool calls as `tools.txt`. Record the host, model, and effort
   in `run.md`. `<runs>` is a results folder that you choose; keep it out of
   version control.
2. **Script.** From this `evals/` folder, run
   `uv run check_ste.py <documents>`.
   Put its output, with the sentence statistics of both arms, in `run.md`.
3. **Grade.** Give a fresh agent the grader prompt below.
4. **Record** the verdicts and the limits in `run.md`.

A case passes only when every box passes in the skill arm. Run each case at
least 3 times before you call it stable.

## Common boxes (document cases S1, S2, S4, S5)

- [ ] **[script]** No sentence is longer than 25 words; no numbered step is
  longer than 20 words; no paragraph has more than 6 sentences.
- [ ] **[script]** The document does not claim to be STE-compliant.
- [ ] **Given-new**: each paragraph opens with its topic sentence, and each
  term is defined before its first use. An intro sentence above a Terms list
  that uses a listed term fails this box.
- [ ] **Links as words**: cause, contrast, and condition are written as words
  ("because", "but", "if"), not as dashes, arrows, or bare juxtaposition.
- [ ] **Facts kept** (not S5, whose prompt gives too few facts): every fact
  from the prompt is in the document, and no fact, number, or decision is
  added; a needed assumption appears as an open question. A statement that
  follows directly from given facts is not added; a new cause, consequence,
  default, or step is.
- [ ] Active voice in almost all sentences; one instruction per step.

## S1 — ADR from facts _baseline_

> Write an ADR to `docs/adr/0001-session-cache.md`. Facts: our API keeps
> sessions in process memory; on deploy all users are logged out; we run 4
> instances behind a load balancer without sticky sessions; we chose Redis 7
> with a 24-hour TTL; we rejected sticky sessions because a crashed instance
> still loses its sessions; cost is one managed Redis node, about $50 a month.

- [ ] The ADR states the decision, the context, the rejected option with its
  reason, and the cost, with the numbers 4, 24 hours, and $50 unchanged.

## S2 — Runbook steps _baseline_

> Write a runbook to `docs/runbooks/rotate-db-password.md` for rotating the
> production database password: create the new password in the secret
> manager, update the app config to read the new secret version, restart the
> app instances one at a time, confirm the health check passes after each
> restart, then revoke the old password. The database accepts two passwords
> for one user at the same time.

- [ ] The procedure is a numbered list, one action per step, in the given order.
- [ ] Stopping when a health check fails is implied by the prompt; it is not an added fact.
- [ ] The step that revokes the old password comes last and has its
  precondition (all health checks passed) written as a condition.

## S3 — Chat reply stays chat

The skill is active (first message names it). Then:

> Quick question: what is the difference between an ADR and an RFC? Two sentences.

- [ ] The reply has two sentences, as asked.
- [ ] The reply is a normal chat answer: no document structure and no STE
  vocabulary notes.
- [ ] No file is written.

## S4 — Spec with protected tokens

> Write a short spec to `docs/specs/rate-limit.md`. Requirement: the API MUST
> reject a client that sends more than 100 requests per minute with HTTP 429.
> Scenario: WHEN a client sends the 101st request in one minute THEN the API
> returns 429 and the header `Retry-After`. Use the config key
> `rate_limit.per_minute`.

- [ ] `MUST`, `WHEN`, `THEN`, `429`, `Retry-After`, and
  `rate_limit.per_minute` appear unchanged.
- [ ] The STE rules apply to the prose around those tokens.

## S5 — Activation without the skill name

The skill is installed but not named.

> Write an RFC to `docs/rfc/0002-feature-flags.md` that proposes a feature
> flag service for our three mobile apps. Keep it to one page.

- [ ] The document passes the common boxes, so the host loaded the skill.
- [ ] Record from the transcript whether the skill was loaded, when the host
  shows it.

## Grader prompt

```text
Grade the documents and replies in <run>/ against
build/**/ste-docs/evals/cases.md.

Read completely: skills/**/ste-docs/SKILL.md, the cases file,
<run>/run.md with the script output, and every <run>/S*-skill-r*/ folder (docs/, reply.md, tools.txt). Do
not read other runs or git history. Do not edit any file except the one you
write.

Copy the [script] results from run.md; do not re-judge them. For every other
box, write pass or fail and one line of evidence quoted from the document or
reply. For "Facts kept", list each prompt fact and where it appears. A case
passes only when all its boxes pass. For S1 and S2, compare the sentence
statistics of the skill arm and the baseline arm in one line.

Write <run>/grades.md: a table (case, verdict, failed boxes), the per-case
details, then the SKILL.md sentence behind each failure. End with one
verdict: release-ready, revise, or inconclusive.
```
