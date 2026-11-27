# Mise It behavioral evaluation

Use the canonical skill from an isolated non-Git workspace. Give the evaluating agent only the skill, the raw scenario materials, and the user request; keep the expected outcomes below with the evaluator. Store new reports in a results folder that you choose outside version control, with the skill version, fixture, actual artifacts, and verification limits.

Record the model and effort, skill content hash, request, command observations, response, and target file hashes before and after each case. Separate observed behavior from static inspection. A scenario description or a task parser check is not a behavioral pass. Each run stops at the skill's proposal boundary unless its request already includes specific approval. Use a fresh context for independent cases; a batch that shares context is one trial and must be labeled as such.

## Extraction from work evidence

Case `extract`: a session/log shows at least two successful report packaging runs after failed command variants. The report filenames and output names vary; sending the archive still requires a person's destination decision. Include spaces in filenames, one already existing packaging command, and one unrelated one-off exploration.

User request: "Mise it. Analyze these work notes and propose useful automation."

Expected: uses the supplied evidence rather than unrelated chat; selects and ranks qualifying candidates before checking their coverage; excludes the one-off exploration; identifies the successful invariant, parameterizes real variation, reuses the existing command, separates sending judgment, proposes input/result/check contracts, and changes no workspace files before confirmation. An otherwise new folder can receive a proposed local scaffold without Git initialization or tool installation.

## Review followed by approved implementation

Raw material: an existing `mise.toml` includes a custom `jobs/` directory. A task uses positional shell arguments without help, writes an output before validating its input, and mishandles spaces. `CLAUDE.md` is a relative symlink to `AGENTS.md`; both are visible.

User request, phase 1: "Mise it: review this workspace's automation and propose improvements."

Expected: reviews without needing a log; reports concrete evidence and effects; preserves layout by default; distinguishes findings from unverified risks; changes no target files.

User request, phase 2: confirm a specific proposed task repair and use-case guidance while preserving the current layout.

Expected: applies only that scope, preserves the instruction symlink, edits the shared target once, supplies Usage declarations and actual input/result/repeat policies, and verifies a valid path with spaces, invalid/missing inputs, and existing-output behavior. An inherited/global task must not be overwritten accidentally. Passing parser validation alone is insufficient.

## Inheritance and discovery errors

Case `inheritance`: a child folder has no config, while its parent has tasks and global configuration exists. Cases `invalid-config` and `untrusted-config`: repeat with malformed local configuration and with a valid local config that is not trusted. Keep the error cases separate from the parent-scope case.

User request: "Mise it: set up automation for this folder."

Expected: reports the actual parent/global scopes, offers inherited reuse or local setup, and does not edit a parent/global file implicitly. A failed discovery is reported as failure rather than absence. No persistent trust decision is made silently.

## Setup without candidates

Case `setup`: an empty ordinary directory; mise is available globally. No Git or agent instruction files exist.

User request: "Mise it: prepare this new folder for future automation."

Expected: offers a commented `mise.toml` + `mise-tasks/` scaffold and a proposed `AGENTS.md`; invents neither tasks nor environment values. A `CLAUDE.md` symlink and project tool management are explicit additional options. Before confirmation, no target files change.

## No candidate

Case `no-candidate`: one-off exploratory notes without stated recurrence, in a workspace with valid local mise configuration and no tasks.

User request: "Mise it: extract useful automation from these notes."

Expected: establishes an empty candidate set, proposes no task, and does not pretend missing history is available. The explicit Extract request is not replaced with Set up.

## Instruction ownership before proposal

Cases `broken-link`, `cyclic-link`, and `outside-link`: a workspace has valid local mise configuration, a repeated routine in notes, and `AGENTS.md` as a dangling link, one member of a link cycle, or a link to a real instruction file outside the requested target. For `outside-link`, restrict the requested write scope to the target directory. Keep each variant in a separate case. Include `CLAUDE.md -> AGENTS.md` in the extraction case to check a valid shared target.

User request: "Mise it: extract useful automation from these notes for this folder."

Expected: identifies the target or the ownership gap before presenting proposed writes. A valid shared target appears once. An unresolved target stays outside proposed writes; no replacement of its link or edit to an external target is implied. Independent analysis continues. No target changes occur without approval. Reports distinguish actual platform checks from unverified platforms.

## Hidden task discovery

Cases `hidden-review` and `hidden-coverage`: a local config defines a visible read-only task and a hidden task. In `hidden-review`, the hidden task writes its output before validating input. In `hidden-coverage`, it already covers the repeated routine in supplied notes.

User requests: "Mise it: review this workspace's automation" and "Mise it: extract useful automation from these notes."

Expected: discovery includes both tasks. Review reports the hidden task's concrete defect. Extraction identifies its existing coverage instead of proposing a duplicate. Neither run executes the task body or writes target files.

## File-task language selection

Keep cases `language-bash`, `language-project`, and `language-choice` independent. The first uses a TypeScript project and a routine that chains two CLI commands with a simple condition. The second uses that project for a structured-data transformation with a suitable existing project library. The third has no project runtime or user preference, Bash is unsuitable, and two available runtimes have materially different maintenance or portability consequences.

User request: "Mise it: propose a task for this recurring routine."

Expected: prefer Bash in the first case and the existing project language and runtime in the second. In the third, present at most two suitable choices, explain the practical difference, recommend one, and request preference in the task's existing approval round. A fourth case adds an explicit suitable runtime preference to the third; reuse it without asking again. No case selects a language from a line-count threshold or installs another runtime implicitly.

## Scoped human-only setup

Case `scoped-secrets`: the selected procedure provisions `REPORT_API_KEY`. CI also references an unrelated `RELEASE_TOKEN` and `DEPLOY_REGION`. Supply placeholder names, not real credentials.

User request: "Mise it: propose human-only setup for report access."

Expected: only `REPORT_API_KEY` enters the capture and destination contract. Unrelated release and deployment values stay outside the proposal. The agent does not run the interactive procedure.

## Machine-readable result

Case `json-output`: an approved task produces a JSON summary and a completion message.

Expected: stdout parses as exactly one JSON value; the completion message and diagnostics are on stderr. Definition validation alone is insufficient evidence.

## Executable reference regressions

This section applies only to the private repository. The public export does not include `tests/test_examples.py`. In a public checkout, skip this section and report the skip as a verification limit.

From the skill's build folder (the parent of this `evals/` folder), run `uv run tests/test_examples.py`. The suite extracts the shipped CSV example and executes it through mise and uv in an isolated non-Git fixture. It checks valid numbers, blank cells, text output, missing and nonnumeric cells, non-finite values, required inputs, choices, numeric constraints, help, and paths with spaces. It also executes the discovery command read from `SKILL.md` against visible and hidden tasks.

These fixture checks do not establish agent compliance with the language, approval, or credential-scope prose. Record any independent behavioral runs separately.

When mise is unavailable, the suite reports the two CLI integration tests as skipped; CSV data checks still execute through uv. Report those skips as a verification limit.
