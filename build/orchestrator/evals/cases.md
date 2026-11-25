# Eval cases

The skill puts the session in a mode: work directly by default, delegate to
a subagent only for a named advantage, pick worker models by tier, and end
with a fixed final report. The evidence is the transcript, because the
grader must see which tool calls the agent made. No script checks this
skill; the grader counts the calls.

## How to run

The steps work in any agent host that shows tool calls in its transcript.

1. **Generate.** Start one fresh session per case and per arm, from the root
   of a real repository with at least three unrelated top-level folders. The
   skill is installed. Each case gives the messages to send, in order.
   - Baseline arm (cases marked _baseline_): the same task, without
     `orchestrator on`, in a session without the skill.
   Export the full transcript, with every tool call and its arguments, to
   `<runs>/<date>-v<version>/<case>-<arm>-r<i>/`, where `<runs>` is a results folder
   that you choose outside version control. Send each
   message only after the previous turn ends; queued messages merge into one turn.
   Record the host, the lead model, the models the host can spawn, and the
   effort in `run.md`.
2. **Grade.** Give a fresh agent the grader prompt below.
3. **Record** the verdicts and the limits in `run.md`.

Do not let the session commit or push: run it on a throwaway branch or in a
copy of the repository. A case passes only when every box passes in the skill
arm. Run each case at least 3 times before you call it stable.

## Common boxes (every case with a task; O1 has none)

- [ ] Every subagent call is preceded, in the lead's visible text of the same
  turn and above the call, by a line that names its advantage: parallel
  work, noisy exploration, fresh review, or isolation. Text only inside the
  call or only after it does not count.
- [ ] No subagent commits, pushes, or spawns another subagent.
- [ ] The final reply of a task reports: outcome, checks and gaps, commits,
  material decisions, and the actual worker models; an empty field says "none".

## O1 — Activation only

> orchestrator on

- [ ] The reply confirms the mode and names a DOER and a REASONING model.
- [ ] Both names are models this host can spawn now, mapped from the tiers
  (standard, strong); no frontier model; no name only remembered from
  training.
- [ ] No tool call besides loading the skill; the agent waits for a task.

## O2 — Small task stays direct _baseline_

> orchestrator on
>
> In `README.md`, fix the first typo you find and show me the diff. Do not commit.

- [ ] Zero subagent calls.
- [ ] The diff is shown, and the final report says no commit was made.

## O3 — Independent exploration is delegated _baseline_

> orchestrator on
>
> For each of the folders `<A>`, `<B>`, and `<C>`, read every file and
> write an inventory: for each file, its purpose and its main functions or
> sections. One section per folder.

Replace `<A>`, `<B>`, `<C>` with three unrelated folders; together they need
at least 100 files, so that reading them all would fill the lead's context. A
smaller task does not test delegation: direct work is then the right answer.

- [ ] At least one subagent call, and every brief has: goal and advantage,
  context, read scope, and the expected result.
- [ ] Worker results are compact (30 lines or fewer each) and the lead checks
  at least one claim before it reports.
- [ ] Workers use the DOER model unless the case needs judgment; the report
  names the models that ran.

## O4 — Model override with an unknown model

> orchestrator on doer=model-that-does-not-exist reasoning=<a real strong model>
>
> Summarise the three largest files in `<A>`.

- [ ] The confirmation says the DOER model is not available and names the
  default it uses instead.
- [ ] The REASONING override is kept.

## O5 — Mode off

> orchestrator on
>
> (O3 task)
>
> orchestrator off
>
> Now list the files in `<A>` that have no tests.

- [ ] After "orchestrator off" the agent confirms the mode is off and
  reports any worker it stopped or still waits for.
- [ ] The last task runs with zero subagent calls.

## O6 — Host without subagents

Run O3 in a host, or a host setting, that cannot spawn subagents.

- [ ] The agent says no workers are available and does the work directly.
- [ ] No model is named as a worker model, because none can be spawned.

## Grader prompt

```text
Grade the transcripts in <run>/ against
build/**/orchestrator/evals/cases.md.

Read completely: skills/**/orchestrator/SKILL.md, the cases file,
<run>/run.md, and every <run>/O*-r*/ folder (transcript.jsonl, turns.md,
tools.txt, git-diff.txt). List the Agent calls with jq on transcript.jsonl. Do not read other runs or
git history. Do not edit any file except the one you write.

For each transcript, first list every subagent call: turn, model, and the
first line of its brief. Then for every box of the case and the common
boxes, write pass or fail and one line of evidence quoted from the
transcript. A case passes only when all its boxes pass. For each baseline
transcript, write one line: how many subagent calls it made and why.

Write <run>/grades.md: a table (case, verdict, subagent calls, failed
boxes), the per-case details, then the SKILL.md line behind each failure.
End with one verdict: release-ready, revise, or inconclusive.
```
