# Human-only procedures

Documentation checked on 2026-10-27 against [task configuration](https://mise.jdx.dev/tasks/task-configuration.html); `interactive`, `raw`, and `secrets` were accepted by mise 2026.10.19.

A human-only procedure walks a person through steps the agent cannot take: a third-party dashboard, credentials or CI secrets, an approval, a one-off cutover. The script tells the person exactly what to open, click, and copy, captures the values, and writes each one where it belongs.

## Task or scratch script

A one-off cutover is a scratch script, removed when the job is done. It becomes a mise task only when it passes the candidate threshold in `SKILL.md`, typically a setup path that new machines or new people repeat. Keep the deterministic parts as ordinary tasks; the human part is its own task with `interactive = true` (`#MISE interactive=true` in a file task), so it keeps the terminal for its whole run. Its description and agent guidance say that a person runs it and an agent does not.

## Scope before writing

Inspect the configuration and documentation relevant to the selected procedure: env-file keys, README, compose files, framework config, and CI workflows. Capture or provision only the credentials and variables that procedure needs; unrelated `secrets.*` and `vars.*` references stay outside its scope. Read existing secret values only when the procedure needs them. For a migration, name the current state, the target state, and the irreversible actions between them.

Write each stage as the path a stranger could follow: "Dashboard → Developers → API keys → Reveal test key → copy". Where the current UI or command is unknown, check its documentation or ask the user; leave no guessed step.

Done when every stage is named in dependency order and every captured value has a source (where the person gets it), a destination (`.env`, a CI secret, both, or nowhere), and a sensitivity (secret or public).

## Stage contract

- One focused task per stage, with progress shown as `Stage n/N`.
- Open a URL before asking for the value it shows: `wslview` on WSL, `xdg-open` on Linux, `open` on macOS; print the URL when none works.
- Read secrets with hidden input (`read -rs`); a secret value never reaches stdout, logs, or the summary. Output of an `interactive` task is not redacted by mise.
- Upsert persisted values: replace an existing `KEY=` line instead of appending, and create a new env file with mode `0600`. On a rerun, offer the saved value as the default, so an interrupted run resumes.
- Ask a y/N confirmation immediately before every irreversible action.
- End-of-input during a prompt fails the task instead of looping.
- When an optional tool such as `gh` is missing, record the step as skipped and continue.
- Close with a summary: keys written (names only), secrets set, and skipped steps with what the person must still do.

## Verify

Run `bash -n`, ShellCheck when available, and set the executable bit. The procedure blocks on a person, so the agent does not run it end to end. Trace it statically instead: every value from the scope is captured and lands at its destination, and every CI secret name matches a `secrets.*` reference. Report it as **inspected**, with that trace, and give the person the exact `mise run <task>` command.
