#!/usr/bin/env bash

set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SOURCE_DIR="$SCRIPT_DIR/intercepted-commands"
COMMANDS=(python python3 pip pip3 poetry)

usage() {
  echo "Usage: $0 check | install ABSOLUTE_TARGET" >&2
  exit 2
}

check_signature() {
  local command_path content interceptor_dir

  command_path=$(command -v python 2>/dev/null || true)
  [[ -n $command_path && -x $command_path ]] || return 1
  interceptor_dir=$(cd "$(dirname "$command_path")" && pwd)

  for command_name in "${COMMANDS[@]}"; do
    command_path=$(command -v "$command_name" 2>/dev/null || true)
    [[ -n $command_path && -x $command_path ]] || return 1
    [[ $(cd "$(dirname "$command_path")" && pwd) == "$interceptor_dir" ]] || return 1
  done

  command_path=$(command -v python)
  content=$(<"$command_path")
  [[ $content == *"resolve_uv_python"* && $content == *"exec uv run"* ]] || return 1

  for command_name in pip pip3 poetry; do
    command_path=$(command -v "$command_name")
    content=$(<"$command_path")
    if [[ $content != *"disabled. Use uv instead"* || $content != *"exit 1"* ]]; then
      [[ $command_name == pip3 && $content == *'/pip"'* ]] || return 1
    fi
  done
}

check_environment() {
  local output pip_status module_status

  command -v uv >/dev/null 2>&1 || {
    echo "not initialized: uv is unavailable" >&2
    return 1
  }

  check_signature || {
    echo "not initialized: active commands are not uv-only interceptors" >&2
    return 1
  }

  output=$(python -c 'print("uv-only-interceptor-ok")') || return 1
  [[ $output == "uv-only-interceptor-ok" ]] || return 1

  output=$(bash -c 'python -c '\''print("uv-only-interceptor-ok")'\''') || return 1
  [[ $output == "uv-only-interceptor-ok" ]] || return 1

  pip --version >/dev/null 2>&1
  pip_status=$?
  python -m pip --version >/dev/null 2>&1
  module_status=$?
  [[ $pip_status -eq 1 && $module_status -eq 1 ]] || return 1

  echo "already initialized: $(dirname "$(command -v python)")"
}

install_interceptors() {
  local target=$1 source destination

  [[ $target == /* ]] || {
    echo "Error: install target must be absolute." >&2
    return 2
  }
  [[ $target != / && $target != "${HOME:-}" ]] || {
    echo "Error: refusing a broad install target: $target" >&2
    return 2
  }

  for command_name in "${COMMANDS[@]}"; do
    source="$SOURCE_DIR/$command_name"
    destination="$target/$command_name"

    if [[ -e $destination ]]; then
      if cmp -s "$source" "$destination"; then
        continue
      fi
      echo "Error: refusing to overwrite conflicting interceptor: $destination" >&2
      return 2
    fi
  done

  mkdir -p "$target" || return

  for command_name in "${COMMANDS[@]}"; do
    source="$SOURCE_DIR/$command_name"
    destination="$target/$command_name"
    [[ -e $destination ]] && continue
    install -m 755 "$source" "$destination" || return
  done

  echo "installed: $target"
  case ":$PATH:" in
    *":$target:"*)
      echo "active in PATH"
      ;;
    *)
      echo "activation required: prepend $target to PATH"
      ;;
  esac
}

case ${1:-} in
  check)
    [[ $# -eq 1 ]] || usage
    check_environment
    ;;
  install)
    [[ $# -eq 2 ]] || usage
    install_interceptors "$2"
    ;;
  *)
    usage
    ;;
esac
