# Mise task contracts

Documentation checked on 2026-10-26. Inspect the installed `mise --version` and relevant `--help`; recheck official sources for features beyond that build. These are focused contracts, not a complete mise manual.

## Discovery details

`mise -C "$workspace" tasks info "$task_name" --json` shows one task's source, aliases, and definition.

Use `mise -C "$workspace" tasks ls --hidden --json` for discovery. Hidden tasks still run and can cover a candidate or need repair; include them in coverage and review. [Task visibility](https://mise.jdx.dev/tasks/task-configuration.html#hide)

`config ls` lists effective configuration in precedence order. `--tracked-configs` instead includes configurations remembered from other projects; it is unsuitable for deciding whether this workspace uses mise. Classify each path as global, parent, or local rather than treating any nonempty result as local setup. An executable lookup failure, untrusted config, and invalid config are separate outcomes. [Config listing](https://mise.jdx.dev/cli/config/ls.html), [configuration loading](https://mise.jdx.dev/configuration.html)

Inspect the sources behind task names and aliases: a name may be inherited or overridden, and a task may wrap an existing script. `task_config.includes` replaces the default task-directory list for that config root; replacing or appending includes can change discovery and name precedence. Retain all needed entries and check the resulting catalog. [Task discovery](https://mise.jdx.dev/tasks/task-discovery.html)

A catalog, help, or validation operation can evaluate dynamically sourced metadata. Report an untrusted config; a blanket `--yes` or a persistent trust change is not a resolution. [Task arguments](https://mise.jdx.dev/tasks/task-arguments.html), [Usage choices](https://usage.jdx.dev/spec/reference/arg)

## File tasks

Executable file tasks use their own interpreter, selected by the shebang, with `#MISE` metadata and `#USAGE` interface declarations; usage-arguments.md shows Bash and Python forms. Headers contain TOML task properties, with the documented file-task exceptions: `run`, `run_windows`, `file`, and `usage` are not file headers. Give scripts executable permission on macOS/Linux. [File tasks](https://mise.jdx.dev/tasks/file-tasks.html)

## Contract to establish or review

| Area | Evidence required |
| --- | --- |
| Use case | The user situation solved and the stable process being retained; commands already available to reuse. |
| Inputs | Required/optional parameters, defaults, semantic types and checks, environment names, and secret source. |
| Execution | Working directory, required tools, prerequisite ordering, platform assumptions, noninteractive behavior. |
| Result | Output artifacts/locations or state changes, stdout/stderr, exit status, success condition. |
| Lifecycle | Existing-output policy, repeat behavior, interruption cleanup, relevant concurrency/conflict behavior. |

A task's default working directory is the defining config root. `dir` can override it; `#MISE dir="{{cwd}}"` requests the invocation directory. `MISE_ORIGINAL_CWD` records the caller's directory. Specify which base relative paths use; do not depend accidentally on where the agent's shell started. [Working directory](https://mise.jdx.dev/tasks/file-tasks.html)

`[env]` sets workspace environment. Current directives include `_.file = ".env"` for a dotenv file and `_.path` for PATH entries, relative to the config root. Preserve existing environment sourcing, and put secret names/retrieval instructions rather than secret values in docs or committed configuration. [Environment variables](https://mise.jdx.dev/environments/)

Independent entries in `depends` may run in parallel. Array order is not sequential execution. Express real dependency edges or ordered `run` steps where ordering matters. Use caching (`sources`/`outputs`) only when all relevant inputs and success outputs are known; otherwise it can skip necessary work. [Dependencies](https://mise.jdx.dev/tasks/architecture.html), [caching](https://mise.jdx.dev/tasks/caching.html)

## Review checks

Each item of the review scan list in `SKILL.md`, and how to find it:

| Check | How to find it |
| --- | --- |
| Side effect before validation | Find the first write, `rm`, `mv`, or network call; every input it depends on must be checked above it. |
| Positional arguments without `#USAGE` | `$1`…`$9` or `$@` in a file task without `#USAGE`, or a TOML task without `usage`. |
| Unquoted expansions | `$var` or `$(…)` outside double quotes in word positions; ShellCheck SC2086 when available. |
| Bash without strict mode | No `set -euo pipefail` and no stated reason. |
| `depends` read as an ordered sequence | A task relying on the array order of `depends`, as described above. |
| Incomplete `sources`/`outputs` | An input file, environment value, or tool that changes the result but is missing from `sources`. |
| `confirm` used as a safety guard | A destructive task whose only guard is `confirm`, as described below. |
| Interactive input without a flag | `read`, `select`, or a prompt with no argument or environment alternative. |
| Secrets in config | Literal tokens or passwords in `mise.toml`, `[env]`, or scripts. |
| Undefined rerun or existing-output behavior | An output path written without an existence check or an explicit replace/reuse policy. |
| Hidden dependence on the caller's directory | Relative paths that assume the shell's directory instead of the config root, `dir`, or `MISE_ORIGINAL_CWD`. |
| Unusable from `--help` alone | `mise run <task> --help` lacks a description, a semantic type for an input, or, with more than two inputs, an example. |
| Loose scripts | Executable or `*.sh`/`*.py` files outside the task root that the README, instructions, or other scripts tell a person to run directly. |
| Two tasks for one situation | Tasks whose descriptions or commands overlap; propose one task with a flag for the real difference. |

## Script reliability

- Validate tool availability, input constraints, output destinations, and necessary authority before side effects. Preserve spaces and metacharacters through quoted variables and arrays; pass data as arguments rather than constructing executable source from it.
- Keep failures visible. For Bash, `set -euo pipefail` is a useful baseline, with explicit handling for commands whose nonzero result is expected. It does not replace result validation or transaction design.
- Define reruns: reuse, replace explicitly, create a distinct artifact, or fail on conflict. Apply temporary staging and publish only a verified result when partial output would be misleading. Clean temporary resources on exit/interruption.
- Prefer bounded noninteractive runs. Missing values should fail with a next action; human-only steps should be identified as interactive. Progress should leave readable logs, and completion should distinguish success, skips, and incomplete work.
- Check platform-sensitive utilities, interpreter features, paths, and quoting on each target platform. WSL2 uses its Linux environment. A shebang does not establish cross-platform correctness.

Apply checks appropriate to the actual effect. A read-only format conversion does not need a migration framework; a deleting task needs a bounded selection and a safe way to verify it. Follow project/runtime authorization for risky execution. A task's `confirm` setting is not an agent authorization boundary: dependencies run before confirmation, and `--yes` can bypass the prompt. [Task configuration](https://mise.jdx.dev/tasks/task-configuration.html)

## Verify without overstating evidence

For a Bash file task, the usual definition/syntax/help checks are:

```sh
bash -n mise-tasks/task-name
mise tasks validate task-name
mise run task-name --help
```

Use ShellCheck when available and appropriate. Validate the generated name in the target workspace, including inherited tasks and aliases. `mise tasks validate` checks definitions such as usage specs, dependencies, files, and directories; warnings do not fail it. It does not establish that the business result is correct. [Task validation](https://mise.jdx.dev/cli/tasks/validate.html)

Exercise representative valid and invalid input, paths with spaces, expected output, reruns/conflicts, and important failure behavior in a disposable fixture. Isolate its mise cache/data/state under scratch with process-local `MISE_CACHE_DIR`, `MISE_DATA_DIR`, and `MISE_STATE_DIR`; even process-scoped trusted paths can cause trust records to be written to the state directory. Preserve the real configuration scope being tested. [Mise directories](https://mise.jdx.dev/directories.html)

For a dangerous task, a checked dry-run or static trace may be the available evidence; report that limit.

## Agent guidance format

Keep task syntax authoritative in its Usage metadata. Add compact guidance explaining **when to choose the task**, for example:

```markdown
## Workspace automation

For a reviewable transfer of the completed report, use `mise run package-report <input> --output <archive>`. It validates the inputs and produces the archive; it does not send it. An existing destination is refused.

Use `mise tasks` to discover other tasks and `mise run <task> --help` for current arguments.
```

Adapt this to the real task and existing instructions; do not insert an invented task or repeat the full parameter catalog. If the use-case guide is genuinely large, keep a clear pointer in the instruction file and disclose details in a dedicated doc. `mise generate task-docs` generates argument reference documentation; regenerate it instead of maintaining a second parameter spec by hand. It does not replace the situation guidance. [Task docs](https://mise.jdx.dev/cli/generate/task-docs.html)
