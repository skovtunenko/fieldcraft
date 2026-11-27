# Command map — beyond the common cases

Read this when the task involves a toolchain the SKILL.md common commands do not cover:
migrating off another package manager, task runners, workspaces, lockfile workflows, or
wiring uv into Docker and CI.

Commands are stated by capability, not against a uv version. uv is assumed present in the
environment and is never pinned. If a flag below is not recognized by the installed uv,
read `uv <command> --help` on that machine and use the equivalent — never fall back to a
non-uv tool.

## Migrating off another package manager

The goal of a migration is a `pyproject.toml` with `[project.dependencies]` (plus
`[dependency-groups]` for dev/test/lint sets) and a committed `uv.lock`. Migrate the
declaration, not the installed environment — reinstalling into a stale venv reproduces the
old resolution.

| Coming from            | Read from                                        | Rewrite to                                                                                                            |
| ---------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `pip` + requirements   | `requirements.txt`, `requirements-dev.txt`       | `uv init --bare` if no `pyproject.toml`, then `uv add -r requirements.txt` and `uv add --group dev -r requirements-dev.txt` |
| `poetry`               | `[tool.poetry.dependencies]`, `poetry.lock`      | `[project.dependencies]`; Poetry's `^`/`~` carets become PEP 440 ranges (`^1.2` → `>=1.2,<2`); dev groups → `[dependency-groups]` |
| `pipenv`               | `Pipfile`, `Pipfile.lock`                        | `[project.dependencies]` + `[dependency-groups] dev`                                                                    |
| `pdm`                  | `[tool.pdm.dev-dependencies]`                    | `[dependency-groups]`; PDM's `[project]` table usually carries over as-is                                              |
| `conda` / `environment.yml` | conda deps                                  | pip-installable deps → `[project.dependencies]`; non-Python/native packages are **not** in uv's scope — report them as a boundary |
| `pipx`                 | globally installed CLIs                          | `uv tool install <pkg>` for persistent installs, `uvx <pkg>` for one-off runs                                          |
| `pyenv` / `asdf`       | `.python-version`                                | `uv python install <version>` + `uv python pin <version>` (uv reads and writes `.python-version`)                       |
| `virtualenv` / `venv`  | `.venv`                                          | delete and let `uv sync` create it, or `uv venv` explicitly                                                             |

After migrating: `uv lock`, then `uv sync`, then run the project's test command through
`uv run` to prove the resolution actually works. Delete the superseded lockfile and manager
config in the same change — leaving `poetry.lock` next to `uv.lock` guarantees someone (or
some agent) uses the wrong one.

Local and non-registry dependencies go in `[tool.uv.sources]` (path, git, url, workspace
members) rather than being installed imperatively.

## Task runners and test matrices

| Tool          | uv-only form                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------ |
| `tox`         | `uvx tox --with tox-uv`, or replace the matrix with `uv run --python 3.X --isolated pytest` per version |
| `nox`         | `uvx nox`, sessions using `uv` as the backend (`nox.options.default_venv_backend = "uv"`)         |
| `make`        | every recipe body is `uv run …`; add a `sync:` target running `uv sync --frozen`                    |
| `just`        | same as make; recipes call `uv run …`                                                             |
| `pre-commit`  | `entry: uv run <tool>` with `language: system`, so the hook uses the project's locked tool version |
| `invoke`/`nox`-likes | `uv run invoke <task>`                                                                     |

For a Python version matrix, `uv run --python 3.12` / `--python 3.13` replaces both pyenv
switching and tox environment management. `--isolated` gives a throwaway environment when a
test must not see the project's own venv.

## Workspaces and monorepos

- Declare members under `[tool.uv.workspace]` in the root `pyproject.toml`; cross-member
  dependencies use `{ workspace = true }` in `[tool.uv.sources]`.
- One `uv.lock` at the workspace root. Do not create per-member lockfiles.
- `uv sync --all-packages` installs every member; `uv run --package <name> <cmd>` runs inside
  one member.
- `uv workspace list` / `uv workspace metadata` inspect the layout when the structure is
  unclear.

## Lockfile workflows

| Intent                                | Command                                                     |
| ------------------------------------- | ----------------------------------------------------------- |
| Refresh the lock after editing deps   | `uv lock`                                                    |
| Lock a standalone script (not a project) | `uv lock --script path.py` (writes `path.py.lock`)         |
| Assert the lock is current (CI gate)  | `uv lock --check`                                            |
| Upgrade everything                    | `uv lock --upgrade`                                          |
| Upgrade one package                    | `uv lock --upgrade-package httpx`                            |
| Install exactly the lock, no drift    | `uv sync --frozen` (or `--locked` to fail if the lock is stale) |
| Runtime-only install                  | `uv sync --frozen --no-dev`                                  |
| Produce `requirements.txt` for a consumer that needs one | `uv export --format requirements.txt --no-hashes -o requirements.txt` |
| SBOM                                  | `uv export --format cyclonedx1.5`                            |

An exported `requirements.txt` is a build artifact, not a source of truth. If one is
generated, say so in the file header and keep `uv.lock` authoritative.

## Docker

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
# Dependencies first, without the project — keeps the layer cacheable.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "app.py"]
```

Points that matter more than the exact base image:

- Copy the uv binary in (or use the official uv base image). Never `pip install uv`.
- `--frozen` in an image build: the lock is an input, resolution is not a build step.
- Split dependency install from project install so code changes don't invalidate the
  dependency layer.
- Entrypoint goes through `uv run`. If a bare interpreter entrypoint is required by a
  platform contract, that is a blocker to state, not a default to accept.
- `UV_COMPILE_BYTECODE=1` and `UV_LINK_MODE=copy` are the usual container-friendly settings;
  `UV_PROJECT_ENVIRONMENT=/usr/local` installs into the system prefix when a venv in the
  image is unwanted.

## CI

Shape, in order: install uv → restore uv's cache → `uv sync --frozen` → `uv run <task>`.

- Use uv's official setup action (or its standalone installer script in non-GitHub CI).
  Pin it the way the rest of the workflow pins actions; do not pair it with a
  `setup-python` + `pip install` step.
- `uv python install` covers the interpreter, so a separate Python setup step is usually
  redundant. Keep one only if the runner image requires it.
- Add `uv lock --check` as its own step so a stale lockfile fails loudly instead of being
  silently re-resolved.
- Cache uv's cache directory (`~/.cache/uv`), keyed on `uv.lock`.

## Publishing

`uv build` produces sdist and wheel; `uv publish` uploads. No `python -m build`, no
`twine`, no `setup.py sdist`.

For a pure Python package, declare uv's own build backend instead of setuptools/hatchling:

```toml
[build-system]
requires = ["uv_build>=0.9.28,<0.10.0"]
build-backend = "uv_build"
```
