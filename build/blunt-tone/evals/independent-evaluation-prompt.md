# Independent evaluation prompt

Paste the text below into a new Codex task from the repository root.

```text
Evaluate `skills/**/blunt-tone` independently. Its version is the
`metadata.version` value in its `SKILL.md`; below, `<version>` is that value.

Read completely:
- `AGENTS.md`, if the repository has one
- `skills/**/blunt-tone/SKILL.md`
- `skills/**/blunt-tone/agents/openai.yaml`
- `build/**/blunt-tone/evals/cases.md`

Do not read earlier blunt-tone run results, git history, the active
OpenSpec change, or earlier conclusions until grading is complete. Do not edit the
skill.

Verify I0 mechanically. Run every generation case in `evals/cases.md`. Use isolated
generator contexts where possible. A generator receives only the canonical skill and
the case Prompt; never give it the rubric, prior outputs, or expected answer. Invoke
`$blunt-tone` explicitly exactly as the case requires.

Grade in separate contexts. A grader receives the case Prompt, generated output,
canonical skill, and that case's rubric. Grade Preservation before Style. A case passes
only when every rubric box passes. Do not repair an output before grading it.

Write one report to `<runs>/<today>-v<version>-independent.md`, where `<runs>` is
the results folder that I name, containing:
- model and environment;
- how generator/grader independence was enforced;
- prompt, raw output, checked rubric, and verdict for every case;
- a summary table and total passed cases/rubric boxes;
- exact instruction gaps for failures, without editing the skill.

After the report is written, you may read prior runs only to compare regressions. End
with one of these verdicts: `release-ready`, `revise`, or `evaluation-inconclusive`,
followed by the smallest evidence-backed next action. Do not archive the OpenSpec change.
```
