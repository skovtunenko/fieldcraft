#!/usr/bin/env bash
# Build an isolated behavioral-eval run, or verify its skill copy is unchanged.
#   prepare_run.sh <scenario> <run-dir>   -> <run-dir>/{skill/,workspace/,skill.manifest}
#   prepare_run.sh --verify <run-dir>     -> exit 1 and list paths if skill/ changed
set -euo pipefail

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
while [ ! -d "$root/skills" ]; do
  [ "$root" = / ] && { echo "no skills/ folder above $0" >&2; exit 1; }
  root="$(dirname "$root")"
done
skill_root="$(cd "$(dirname "$(ls "$root"/skills/interview-helper-builder/SKILL.md "$root"/skills/*/interview-helper-builder/SKILL.md 2>/dev/null | head -1)")" && pwd)"

usage() {
  echo "usage: $0 <scenario> <run-dir> | --verify <run-dir>" >&2
  exit 2
}

# Sorted sha256 of every file under $1, paths relative to it.
# .cc-writes/ is the agent harness's own write log, not skill content.
manifest() {
  (cd "$1" && fd --hidden --no-ignore --follow -E .git -E .cc-writes --type f --print0 . | LC_ALL=C sort -z | xargs -0 shasum -a 256)
}

[[ $# -eq 2 ]] || usage

if [[ $1 == --verify ]]; then
  run_dir="$2"
  [[ -f "$run_dir/skill.manifest" && -d "$run_dir/skill" ]] || { echo "not a prepared run: $run_dir" >&2; exit 2; }
  current="$(manifest "$run_dir/skill")"
  # Emit "changed|added|removed <path>" by joining the two manifests on path.
  diffs="$(awk '
    { p = substr($0, 67) }  # shasum line: 64-hex hash, two spaces, path
    NR == FNR { old[p] = $1; next }
    { if (!(p in old)) print "added " p; else if (old[p] != $1) print "changed " p; delete old[p] }
    END { for (p in old) print "removed " p }
  ' "$run_dir/skill.manifest" <(printf '%s\n' "$current") | LC_ALL=C sort)"
  if [[ -n $diffs ]]; then
    echo "SKILL COPY MODIFIED"
    printf '%s\n' "$diffs"
    exit 1
  fi
  echo "SKILL COPY UNCHANGED"
  exit 0
fi

scenario="$1"
run_dir="$2"
fixture="$(dirname "${BASH_SOURCE[0]}")/../fixtures/$scenario"
[[ -d $fixture ]] || { echo "no fixture: $fixture" >&2; exit 2; }
if [[ -e $run_dir ]] && [[ -n "$(ls -A "$run_dir")" ]]; then
  echo "run dir not empty: $run_dir" >&2
  exit 2
fi

mkdir -p "$run_dir/skill" "$run_dir/workspace"
rsync -a --exclude '/evals/' --exclude '.cc-writes/' "$skill_root/" "$run_dir/skill/"
cp -R "$fixture/." "$run_dir/workspace/"
manifest "$run_dir/skill" > "$run_dir/skill.manifest"
echo "skill:     $(cd "$run_dir/skill" && pwd)"
echo "workspace: $(cd "$run_dir/workspace" && pwd)"
