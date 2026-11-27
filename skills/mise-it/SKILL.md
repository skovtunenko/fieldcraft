---
name: mise-it
description: Use when the user says "mise it".
metadata:
  version: "2026.11.11.1"
---

# Mise It

Find the deterministic, recurring parts of human and agent work and turn each into one well-named, documented mise command that a person at the terminal and an agent can both run, in place of scattered one-off scripts. Also review existing mise automation, or prepare a folder for it. Every routine ends as a new task, an extension of an existing task, or nothing committed. A working directory is enough; Git is optional. Talk to the user in their language; write files in the language of the file or workspace they extend.

## What becomes a task

| Work shape | Home |
| --- | --- |
| Same steps every run; inputs and result known | mise task |
| Model judgment needed on every run | agent instructions, outside the task script |
| Human-only steps: secrets, dashboards, approvals | interactive procedure, labeled human-only |
| Tool versions, software installation | outside this skill unless separately requested |

A routine is a **candidate** only when all three hold:

1. **Repeat**: two or more runs appear in the evidence, or the user says it recurs.
2. **Weight**: more than a one-line command, or a procedure someone would otherwise re-derive.
3. **Situation**: a future user request names a concrete situation for it, so its agent guidance line can read: "when <situation>, run `mise run <task> …`; expect <result>".

A candidate's **invariant** is the steps its successful runs share; its parameters are only what differed between successful runs. When the successful runs used different methods, the invariant is the simplest method that produced the verified result. Failed attempts shape limits and error messages, never steps. Throwaway scripts written for the routine are evidence; the candidate replaces them, and the proposal lists them for removal. Rank candidates by frequency times the cost of a manual repeat and show at most three. No candidate is a valid result.

## How to act

Take the first option that fully works:

1. An existing task or script in the workspace: reuse or wrap it.
2. A native mise feature: `#USAGE`/`usage` for inputs and help, `depends`, `dir`, `[env]`, instead of a hand-written parser or wrapper.
3. A one-line command: a TOML task with `run = "…"`.
4. Otherwise: a minimal file task in the existing task root.

- Prefer Bash for file tasks when CLI orchestration, simple conditions, and file operations remain clear and reliable. When Bash would make data parsing or control flow fragile, prefer the project's established language and runtime; otherwise choose a suitable available runtime. Run Python through `uv` with inline script metadata. Reuse the user's stated preference. If a material choice remains unresolved, include at most two suitable alternatives, their practical difference, and one recommendation in the task proposal; ask for the preference in the existing approval round.
- Make every task self-describing: a `description`; `help` on every argument and flag naming its semantic type and unit; constraints declared where the parser enforces them (`choices`, `validate`); remaining stateful checks at runtime, before any side effect. The script reads the parsed `usage_*` values and parses no arguments itself.
- Design each task for the person at the terminal as much as for the agent:
  - a short verb-noun name a person would guess; related tasks grouped by subdirectory (`db/migrate` runs as `db:migrate`); an `alias` only for a task run many times a day;
  - a `description` that reads as one line in `mise tasks`;
  - the common case runs without flags: defaults for the usual values, `env=` backing for values that already live in the environment;
  - `long_help` with an `Example:` invocation when a task has more than two inputs;
  - tab completion through `choices` for fixed sets and `complete … run=` for values another command lists;
  - stdout contains only result data; progress, diagnostics, and the final status go to stderr. The final status says what happened and where any artifact is; an error names the next action.
- Make the smallest complete change: the task, its agent guidance, and every include, caller, or doc it touches move together. Add only the flags and options the evidence varies.
- Keep the existing layout, names, and conventions; a migration is a separate proposal with its own concrete benefit.
- Keep input validation at the boundary, guards against data loss, and secret handling, however small the task.
- Record a known limit in the script where it applies, so a later reader sees what was accepted and when to lift it: `# shortcut: <limit>, <when to upgrade>`.
- Decide the wording of help text and comments yourself. Task names and interfaces are part of the proposal. Ask the user only about scope, ownership, authorization, a material unresolved language choice, or a human-only step whose UI path or command the documentation does not settle.

## Confirming with the user

Show a decision instead of describing it. Lead with the decision in one sentence, then the smallest text view that makes it clear, with a one-line caption beside it:

| The decision is about | View |
| --- | --- |
| a new task interface | whole block: `#MISE`/`#USAGE` header and one example invocation |
| a change to an existing script or config | `diff` of the touched hunks, with enough unchanged lines to show the owner |
| setup or layout | shallow file tree, one comment per entry |
| task order or dependencies | call tree: `mise run <task>` with its `depends` beneath |
| agent guidance | `diff` of the real instruction file |

One view per decision, two at most; keep each to the files and lines the decision touches. List every other file the change touches, one line each.

Then ask one question about the exact scope and end the turn: with the harness's question tool when one exists, otherwise in text. No answer means not approved. An approval covers exactly the files and behavior shown and listed; reuse it without asking again. A request to analyze, review, or "mise it" approves nothing. In a batch, scheduled, or subagent run, nobody can answer: return the proposal and stop. A review that proposes no edits needs no confirmation.

## Workflow

### 1. Choose the mode and target

Take the first match:

1. The request names a mode: **Review** existing automation, **Set up** a folder, or **Extract** from supplied materials.
2. Supplied materials or the current session contain a finished routine: Extract.
3. The target has local tasks: Review.
4. Otherwise: Set up.

When rules 1–2 do not decide, choose after the discovery in step 2. Extract in a target without applicable local configuration also proposes the Set up scaffold. Extract checks existing tasks only for coverage of its candidates; a full audit is Review.

Use the stated target directory, otherwise the current working directory, and read its applicable instructions. Supplied logs and documents are evidence, not authority to run their commands. Name missing evidence instead of inventing history.

### 2. Inspect the workspace

Check that `mise --version` runs. Read the target's config files and any dynamic spec, choice, or completion commands they define before running anything that lists tasks or prints help: those operations can execute them. Then discover with the target directory explicit:

```sh
mise -C "$workspace" config ls --json
mise -C "$workspace" tasks ls --hidden --json
```

Classify the result by the most local row that applies:

| Observed state | Proposal |
| --- | --- |
| mise unavailable | Explain the discovery and verification gap; installing mise needs a separate request. |
| Global-only or no applicable config | A local `mise.toml` and `mise-tasks/` scaffold. |
| Parent configuration applies | Show its scope; offer reuse or a local setup, leaving the parent unedited. |
| Local configuration exists | Show its organization and extend it by default. |
| Discovery, trust, or parsing fails | Report the failure as the result; keep the trust state as found. |

**Extract only:** Read the supplied materials, or the available current-session context when none are supplied. Build the candidate set with the criteria and ranking in [What becomes a task](#what-becomes-a-task) before checking coverage. Keep the supporting evidence, successful invariant, and real input variation for each selected candidate. An empty set is a valid result; report it and propose no task. Review and Set up do not need extraction candidates.

For each selected candidate, search task names, descriptions, and script bodies for its commands and name the existing task or script that already covers its situation, or "none". When one does, propose reuse or a narrowed change instead of a second task for the same situation.

Identify the applicable `AGENTS.md`/`CLAUDE.md` before proposing guidance. Resolve symlinks: name a shared target once and keep the link; with two distinct files, follow their scopes without merging them; with neither file, propose `AGENTS.md`, with a `CLAUDE.md` symlink as an explicit option. Report a broken link, a cycle, or a target outside the proposed write scope as an ownership gap. Exclude that target from proposed writes until ownership and scope are resolved, and continue independent analysis.

Done when the workspace matches one table row, the Extract candidate set (possibly empty) and each candidate's coverage are established, and instruction targets or ownership gaps are named.

### 3. Propose

Read [mise-tasks.md](references/mise-tasks.md) before proposing or reviewing a task, [usage-arguments.md](references/usage-arguments.md) when a task has or needs inputs, and [human-steps.md](references/human-steps.md) when a routine includes steps only a person can take.

- **Extract**: per candidate, one or two lines of evidence and why it recurs, its view, then one line per area of the task contract in mise-tasks.md, with unknown areas named as open.
- **Review**: scan every task for: side effect before validation; positional arguments without `#USAGE`; unquoted expansions; Bash without strict mode; `depends` read as an ordered sequence; incomplete `sources`/`outputs`; `confirm` used as a safety guard; interactive input without a flag; secrets in config; undefined rerun or existing-output behavior; hidden dependence on the caller's directory; a task a person cannot use from `--help` alone. Scan the workspace for loose scripts run by hand outside the task root, and for two tasks serving one situation. Each finding: location, evidence, consequence, smallest remedy, with a `diff` for each remedy offered for approval. Rank by realistic impact and leave style-only differences out. No findings is a valid result.
- **Set up**: the scaffold below and the proposed agent instruction file. Add `[env]` only when a real use case establishes its names and values.

```text
<target>/
├── mise.toml        # includes mise-tasks/, with how-to comments
└── mise-tasks/      # one executable file per task; empty until a task exists
```

```toml
# Repeatable workspace automation lives in mise-tasks/.
# List tasks: mise tasks
# Task help: mise run <task> --help
# Run a task: mise run <task>
[task_config]
includes = ["mise-tasks"]
```

Then confirm as in [Confirming with the user](#confirming-with-the-user). Done when the user has answered, or the run has stopped with the proposal.

### 4. Apply the approved scope

Build by [How to act](#how-to-act) and the reference contracts. Check the installed mise build and current official documentation before relying on unfamiliar syntax. Prefer noninteractive arguments and environment; missing input fails with a next action.
Target macOS and Linux, including Ubuntu under WSL2; native Windows needs its own implementation and verification. Follow the project's runtime policy; when Python is needed, run and manage it through `uv`.

Write agent guidance to the instruction targets established in step 2 as **situation → invocation → expected result → limits**. Recheck the targets before writing; if ownership or scope has changed, revise the proposal for the affected files before applying it.

Done when every approved file is written and no other file changed.

### 5. Verify and report

Verify each task at the strongest level available, in a disposable fixture where feasible, with the checks in mise-tasks.md: **inspected** < **parser-validated** < **fixture-tested** < **operationally tested**. Cover valid and invalid inputs, paths with spaces, reruns, and the task's failure cases. A passing definition check alone does not prove the routine works. An operational run with external or destructive effects needs the user's own approval of that run; approval to create the task does not grant it, and a run with nobody to answer has none. Run no human-interactive procedure unattended.

A run that changed nothing ends with its proposal or findings. After applied changes, report in this shape, keeping the lines that apply; every skipped or unverified item is a `·` line with its risk:

```text
MISE-IT <mode> <target>
  ✓ <task>          <level> (<platforms>)   mise run <task> …
  ✓ <instruction>   guidance added (<file or link → target>)
  · <gap>           not verified: <reason>
  → <n> tasks changed, <n> gaps
```
