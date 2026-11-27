# Fieldcraft

[![check](https://github.com/skovtunenko/fieldcraft/actions/workflows/check.yml/badge.svg)](https://github.com/skovtunenko/fieldcraft/actions/workflows/check.yml)
[![release](https://img.shields.io/github/v/release/skovtunenko/fieldcraft?sort=date)](https://github.com/skovtunenko/fieldcraft/releases/latest)
[![license](https://img.shields.io/github/license/skovtunenko/fieldcraft)](https://github.com/skovtunenko/fieldcraft/blob/main/LICENSE)

Agent skills for daily engineering work and for how an agent talks to you.
Each skill is one folder with a `SKILL.md` in the Agent Skills format, which
Claude Code and Codex read. Each skill ships with its eval cases.

## Skills

| Skill | What it does | Starts when |
| --- | --- | --- |
| [`ambition-lens`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/ambition-lens/SKILL.md) | finds where the current task could aim higher and ranks at most three bigger versions | you call it by name |
| [`auditing-skill-best-practices`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/auditing-skill-best-practices/SKILL.md) | audits one skill against Anthropic's skill-authoring rules: a script checks the mechanical rules, the agent judges the rest, and you get a report and an optional review page | you call it by name |
| [`blunt-tone`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/blunt-tone/SKILL.md) | rewrites prose so it is cheaper to read, without a change in meaning | you call it by name |
| [`go-contract-mode`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/go-contract-mode/SKILL.md) | designs the contract of a Go feature with you and writes it into the project as code that compiles, with stubs in place of behavior | you say "go contract mode" |
| [`interview-helper-builder`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/interview-helper-builder/SKILL.md) | builds one offline HTML page for an interview with one candidate, from the role, the CV, and earlier feedback: questions, signals to rate, a timer, and a scorecard | you call it by name |
| [`mise-it`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/mise-it/SKILL.md) | turns repeated steps into documented [mise](https://mise.jdx.dev/) tasks that a person and an agent both run | you say "mise it" |
| [`orchestrator`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/orchestrator/SKILL.md) | a session mode: the agent works directly and delegates to subagents only for a named advantage | you say "orchestrator on" |
| [`reply-contract`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/reply-contract/SKILL.md) | ends each reply with a numbered list of what the agent needs from you and a fixed status line | every reply |
| [`ste-docs`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/ste-docs/SKILL.md) | writes design docs, RFCs, ADRs, and specs in ASD-STE100 Simplified Technical English | you ask for such a document |
| [`uv-only`](https://github.com/skovtunenko/fieldcraft/blob/main/skills/uv-only/SKILL.md) | runs all Python work through [uv](https://docs.astral.sh/uv/): scripts, tools, dependencies, CI | a task touches Python |

`uv-only` also starts on the Russian and Ukrainian phrases "только uv" and
"лише uv".

## Install

Pick one: the [skills CLI](https://skills.sh/) or
[kasetto](https://kasetto.dev/). Both install into the current project.

```bash
# skills CLI: pick the skills from a list
npx skills add skovtunenko/fieldcraft

# skills CLI: one skill
npx skills add skovtunenko/fieldcraft --skill uv-only

# kasetto: --project, because its default scope is global
kst add https://github.com/skovtunenko/fieldcraft --skill uv-only --project
```

By hand: copy `skills/<name>` into the skills folder of your agent.

## Evals

`build/<name>/evals/` holds the eval cases of each skill: prompts, the boxes
that a pass needs, and grader prompts. Some skills also have a checker
script. Run a checker from its `evals/` folder:

```bash
cd build/reply-contract/evals
uv run check_reply.py --self-test
```

Each `cases.md` starts with how to run its cases. Keep run results outside
the repository.

## Repository layout

```text
skills/<name>/        the skill: SKILL.md, agents/, references/, assets/
build/<name>/evals/   eval cases, grader prompts, checker scripts
.mise/tasks/          the check task
```

This repository receives releases from a private source repository. A
release has a calendar version, `vYYYY.MM.DD.N`. Each skill has its own
version in `metadata.version` of its `SKILL.md`.

## Development

The task needs [mise](https://mise.jdx.dev/).

```bash
mise run check   # check the frontmatter of each skill
```

## Feedback

Use [Issues](https://github.com/skovtunenko/fieldcraft/issues) to report a
problem or to suggest a skill.

## License

MIT, see [`LICENSE`](https://github.com/skovtunenko/fieldcraft/blob/main/LICENSE).
