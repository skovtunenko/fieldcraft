---
name: uv-only
description: >-
  Route all Python execution, CLI tools, environments, versions, and dependency
  work through uv/uvx, including commands, generated artifacts, docs, CI,
  Docker, and delegated instructions. Use whenever a task touches Python,
  migrates from another Python toolchain, or explicitly requires uv-only,
  no-system-Python, "только uv", or "через uv"; also use when the user asks to
  initialize, install, activate, or verify the uv-only interceptors.
metadata:
  version: "2026.11.07.1"
---

# uv Only

## Contract

Resolve every Python interpreter and package through uv:

- `uv run` for project code, scripts, and project tools;
- `uvx` for one-off tools;
- uv subcommands for dependencies, environments, and Python versions.

Apply the same rule to executed commands, generated files, documentation, task runners,
CI, Docker, code that launches subprocesses, and delegated instructions. `uv run python`
is valid because uv resolves that interpreter.

Use the installed uv's `--help` when a capability is uncertain. If `uv` or `uvx` is absent,
report the blocker. Treat host-embedded or OS-mandated interpreters as explicit scope
exceptions and name the boundary.

## Sandbox cache

Before Python work in a sandbox, inspect `uv cache dir`, existing uv configuration,
`UV_CACHE_DIR`, and the host's writable roots. Reuse a writable cache. If the cache is
outside those roots, set execution-local `UV_CACHE_DIR=<workspace-root>/.uv-cache`
before the first run. Use the same fallback after a cache permission error. Keep
`.uv-cache/` ignored by Git.

When the user requests a permanent fix or prevention of repeated cache failures,
persist the cache within the authorized project scope. A relative `cache-dir` resolves
from the current directory, so it creates a `.uv-cache` in every folder uv runs from.
Prefer an absolute `UV_CACHE_DIR` in an existing project task environment, for example
a mise `[env]` entry `UV_CACHE_DIR = "{{config_root}}/.uv-cache"`. Without one, use an
existing `uv.toml`, or `[tool.uv]` in an existing `pyproject.toml`; if neither contains
uv configuration, create `uv.toml` at the project root:

```toml
cache-dir = ".uv-cache"
```

That relative form covers only commands run from the project root; say so.
Preserve other settings. A new `uv.toml` takes precedence over `[tool.uv]`, so keep
existing uv settings in the file that uv reads. Environment variables override both
files; inspect a conflicting `UV_CACHE_DIR` before claiming the fix works. `uvx` and
`uv tool` ignore project configuration. Script commands discover configuration from
the script's directory, so a script outside the project can select a different cache.
Use an absolute execution-local `UV_CACHE_DIR` for these invocations, or persist it
in an already-authorized project task environment.

Verify the persistent fix with `uv cache dir` and the original command, without a
temporary cache override, from the command's actual working directory, and confirm that
a run from a subfolder creates no `.uv-cache` there. Report which
commands are covered. If only the temporary fallback works, say so and name the
remaining fix. Suggest a host-specific writable-root change only when project-local
configuration is unsuitable or the user wants a shared cache. Use the observed path
and active host; omit that request once the local fix works.

## Sandbox downloads

When a sandbox blocks uv's downloads (`Failed to fetch` for `pypi.org` or
`files.pythonhosted.org`), rerun inside the sandbox with both hosts allowed for that
command (Claude Code auto mode: `allowed_domains`) and end the reply with this note, in the
user's language, while the host's network allowlist lacks them:

```text
uv downloads blocked by the sandbox. Permanent fix: allow pypi.org and files.pythonhosted.org.
Claude Code, ~/.claude/settings.json: "sandbox": {"network": {"allowedDomains": ["pypi.org", "files.pythonhosted.org"]}}
Other hosts: add both hosts to the sandbox's network allowlist.
```

## Common commands

| Task | Command |
| --- | --- |
| Run a script | `uv run app.py` |
| Run a module | `uv run -m package.module` |
| Run inline code | `uv run python -c '...'` |
| Run a project tool | `uv run pytest`, `uv run ruff check .` |
| Run a one-off tool | `uvx ruff check .` |
| Add or remove a dependency | `uv add httpx`, `uv remove httpx` |
| Sync from project metadata | `uv sync` |
| Add a dependency for one run | `uv run --with rich script.py` |
| Create an environment | `uv venv` |
| Manage Python | `uv python install 3.13`, `uv python pin 3.13` |
| Start a project or script | `uv init`, `uv init --script tool.py` |

Use `uv add` and `uv sync` for managed projects. Reserve `uv pip` for unmanaged or
requirements-file compatibility workflows.

## Standalone scripts

Declare standalone dependencies inline with PEP 723:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///

import httpx
```

Use `uv init --script path.py` to scaffold and `uv add --script path.py httpx` to add
dependencies. Inside a uv project directory, run the script with `uv run --no-project
path.py` so it does not install the project's own dependencies.

## Self-check

Before execution or delivery, verify that uv resolves every Python command, tool, package,
environment, generated entrypoint, and delegated instruction. Report any boundary that uv
cannot satisfy.

## Enforcement

The bundled PATH interceptors make bare `python` run through uv and reject `pip` and
`poetry`. They are opt-in: do not change `PATH` automatically or claim they are active
without verifying command resolution. Read the interceptor reference when mechanical
enforcement is requested.

When the user says `initialize uv-only`, read the interceptor reference and follow its
initialization protocol. Check first; an already-working environment is a successful no-op.
Ask for project or user scope before installing or persisting `PATH`.

## References

- Read [references/command-map.md](references/command-map.md) when the task involves a
  toolchain not in the common commands — migrating a project off poetry/pipenv/pdm/conda,
  tox/nox, `pyproject.toml` layout, workspaces, monorepos, lockfile and export workflows, or
  wiring uv into Docker and CI in detail.
- Read [references/interceptors.md](references/interceptors.md) when the user requests
  mechanical enforcement, wants to activate the bundled interceptors, or asks why a
  command was redirected or rejected.
