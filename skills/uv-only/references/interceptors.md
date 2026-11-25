# PATH interceptors

Read this when the user wants bare Python commands mechanically routed through uv.

## How they work

The bundled [intercepted-commands](../scripts/intercepted-commands/) directory contains
small executables named `python`, `python3`, `pip`, `pip3`, and `poetry`. Put that directory
first in `PATH`:

- `python` and `python3` dispatch through `uv run`;
- `python -m pip`, `python -m venv`, and `python -m py_compile` stop with a uv-native
  replacement;
- `pip`, `pip3`, and `poetry` stop with a uv-native replacement.

Command resolution supplies the enforcement. There is no shell parser and no harness hook.
The same interceptors therefore work in Claude, Codex, other agents, and ordinary shells.

## Activate

Resolve the interceptor directory to an absolute path, then prepend it for the intended
shell or agent environment:

```bash
export PATH="/absolute/path/to/uv-only/scripts/intercepted-commands:$PATH"
```

For project-scoped activation with direnv:

```bash
PATH_add /absolute/path/to/uv-only/scripts/intercepted-commands
```

Do not persist the `PATH` setting without the user's request. Activation is successful only
when `command -v python`, `command -v pip`, and `command -v poetry` resolve inside the
bundled directory.

Let uv use its default cache. If a restricted environment cannot write there, set
`UV_CACHE_DIR=<workspace>/.uv-cache` for that execution and keep `.uv-cache/` ignored.

## Initialize

On `initialize uv-only`:

1. Run `scripts/initialize-interceptors.sh check`. If it passes, report
   `already initialized` and stop. If uv fails because its default cache is not writable,
   retry with an execution-local workspace cache.
2. If it fails, ask for `project` or `user` scope before writing:
   - project target: `<workspace>/.uv-only`;
   - user target: `${XDG_DATA_HOME:-$HOME/.local/share}/agent-shims`.
3. Run `scripts/initialize-interceptors.sh install <absolute-target>`. It copies only
   missing files, accepts identical files, and refuses conflicting files.
   For project scope, install the command files directly in `.uv-only/`; do not create an
   extra `intercepted-commands/` child.
4. Put the target first in `PATH` through the environment's native configuration. Preserve
   existing configuration and request permission before changing it. For project scope,
   keep `.uv-only/` uncommitted unless the user asks to share it.
5. Start or reload the affected shell or harness, then run
   `scripts/initialize-interceptors.sh check` again. Do not declare success before it
   passes.

The script never edits shell or harness configuration. This keeps the install portable and
makes persistence an explicit, reviewable action.

## Boundary

An explicit path such as `/usr/bin/python3` bypasses `PATH`; generated files can also name
an absolute interpreter. The skill contract still forbids those forms. Do not present the
interceptors as proof that every future execution is uv-routed.
