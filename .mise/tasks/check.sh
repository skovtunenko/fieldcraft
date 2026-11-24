#!/usr/bin/env bash
#MISE description="Check the frontmatter of each skill"

set -euo pipefail

# The skills CLI and kasetto read name and description; each skill also carries a quoted metadata.version.
status=0
count=0
for file in skills/*/SKILL.md; do
  [ -e "$file" ] || break
  count=$((count + 1))
  awk -v file="$file" -v dir="$(basename "$(dirname "$file")")" '
    NR == 1 { if ($0 != "---") exit; next }
    $0 == "---" { closed = 1; exit }
    /^[^ \t]/ { desc = 0; meta = 0 }
    /^name:/ { name = $2; gsub(/"/, "", name) }
    /^description:/ { v = $0; sub(/^description:[ \t]*/, "", v); if (v != "" && v !~ /^[>|][-+]?$/) has_desc = 1; else desc = 1 }
    desc && /^[ \t]+[^ \t]/ { has_desc = 1 }
    /^metadata:/ { meta = 1 }
    meta && /^[ \t]+version:[ \t]*"[^"]+"[ \t]*$/ { version = 1 }
    END {
      if (!closed) { print file ": no YAML frontmatter"; exit 1 }
      if (name != dir) { print file ": name \"" name "\" must match the folder \"" dir "\""; bad = 1 }
      if (!has_desc) { print file ": description is missing or empty"; bad = 1 }
      if (!version) { print file ": metadata.version is missing or not a quoted string"; bad = 1 }
      exit bad
    }
  ' "$file" || status=1
done

if [ "$count" -eq 0 ]; then
  echo "No skills/*/SKILL.md found" >&2
  exit 1
fi
[ "$status" -eq 0 ] && echo "$count skills passed"
exit "$status"
