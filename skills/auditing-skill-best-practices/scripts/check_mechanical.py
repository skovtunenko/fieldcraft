#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Decide the mechanical rules of both rule catalogues (BP and OS) for one skill.

Usage:
    python3 check_mechanical.py <skill-dir>

<skill-dir> is a directory that contains SKILL.md. The script reads files only
and writes nothing. It prints one JSON object to stdout:

    {"target": "<skill-dir>",
     "rules": {"BP-04": {"status": "pass" | "fail" | "n/a",   # BP-NN and OS-NN IDs
                         "findings": [{"file": "SKILL.md", "line": 2,
                                       "message": "...", "fix": "..."}],
                         "not_evaluated": [{"file": "...", "reason": "..."}]},
               ...},
     "unreadable": [{"file": "...", "reason": "..."}],
     "not_applicable": {"BP-33": "no evaluation material (BP-32)", ...}}

"not_applicable" maps judgment rules to the reason they are n/a for this
skill, decided from what the skill ships: no evaluation or test folder, no
bundled files, no injected command, no `allowed-tools`. A reader with facts
the script lacks (an evaluation location the user names) may still judge them.

"line" is null when a finding concerns a whole file. "not_evaluated" appears
only on rules whose input could not be fully read (a non-UTF-8 text file, an
unreadable file, a folder that cannot be listed). A rule with a confirmed
failure stays "fail"; otherwise it reports n/a. Binary files are skipped silently. Exit status: 0 after any
audit (failed rules are data, not errors); 2 on a usage error, with the reason
on stderr.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

NAME_MAX = 64  # article: `name` at most 64 characters
DESCRIPTION_MAX = 1024  # article: `description` at most 1024 characters
BODY_LIMIT = 500  # article: keep the SKILL.md body under 500 lines
TOC_THRESHOLD = 100  # article: reference files longer than 100 lines need a TOC
TOC_WINDOW = 30  # a TOC heading counts only near the top of the file
TOC_MIN_LINKS = 3  # fewer anchor links than this is not a table of contents
LISTING_MAX = 1536  # Claude Code docs: description + when_to_use are cut at 1,536 characters in the listing
COMPATIBILITY_MAX = 500  # Agent Skills specification: compatibility is 1 to 500 characters
QUOTE_MAX = 40  # characters of an offending line quoted in a message: enough to find it, short enough for one line
BINARY_SNIFF_BYTES = 8192  # a NUL in the first 8 KiB marks a binary file; text never holds NUL, and 8 KiB is cheap to read

SKIP_DIRS = {"__pycache__", "node_modules"}
# Judgment rules that apply to evaluation material; BP-32 alone reports its absence (catalogue Terms).
EVALUATION_RULES = ("BP-03", "BP-33", "BP-34", "BP-35", "BP-36", "BP-37", "BP-38", "BP-54")
DEV_DIR = re.compile(r"^(?:eval|test)(?:s|uations?)?$")  # evaluation and test folders: development files, not skill content
TEST_FILE = re.compile(r"^test_.*|.*[._]test\.[a-z]+$")  # unit tests sit beside code; Claude never reads them
TAG = re.compile(r"</?[A-Za-z][\w:.-]*(?:\s[^<>]*)?/?>")  # an element tag; `<=`, `>=`, `a < b` are not tags
RESERVED = re.compile(r"anthropic|claude", re.IGNORECASE)
NAME_CHARS = re.compile(r"^[a-z0-9-]+$")
DRIVE_PATH = re.compile(r"(?<![\w\\])[A-Za-z]:\\{1,2}[\w.$-]+(?:\\{1,2}[\w.$-]+)*")
BACKSLASHES = re.compile(r"\\+")
# A backslash path: word segments joined by one or two backslashes, not preceded by a
# backslash (so regex escapes such as \d\d are skipped).
BACKSLASH_PATH = re.compile(r"(?<![\\\w.$%-])[\w.$-]+(?:\\{1,2}[\w.$-]+)+")
FILE_SEGMENT = re.compile(r"^[\w-]{2,}[\w.-]*\.[A-Za-z][A-Za-z0-9]{0,4}$")  # name.ext: 2+ char name, ext starts with a letter
COMMON_DIRS = {"scripts", "references", "reference", "assets", "templates", "examples",
               "docs", "src", "lib", "bin", "data", "tools", "config"}  # skill folders a path may start with
MD_LINK = re.compile(r"\]\(\s*(?:<([^>\n]*)>|([^)\s]+))")  # inline link: <path with spaces> or a bare path
REF_DEF = re.compile(r"^ {0,3}\[(?!\^)[^\]]+\]:\s*(?:<([^>\n]*)>|(\S+))")  # reference-style link definition
TOC_HEADING = re.compile(r"^#{1,3}\s+(?:table of )?contents\b", re.IGNORECASE)
TOC_LINE = re.compile(r"^\s*(?:table of )?contents\b", re.IGNORECASE)  # plain-text files have no "#" headings
ANCHOR_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s.*\]\(#")
HEADING = re.compile(r"^#{1,6}\s")
FENCE = re.compile(r"^\s*(```|~~~)")
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")  # CommonMark fence: closed only by the same character, at least as long
CODE_SPAN = re.compile(r"(`+).+?\1")
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
# Claude Code frontmatter fields as of the OS catalogue's snapshot (OS-04).
KNOWN_KEYS = {"name", "description", "when_to_use", "argument-hint", "arguments", "disable-model-invocation",
              "user-invocable", "allowed-tools", "disallowed-tools", "model", "effort", "context", "agent",
              "background", "hooks", "paths", "shell", "metadata", "license", "compatibility"}
# A YAML block-mapping entry: a quoted key, or a plain key that starts with no indicator character, then ":" and a
# space or the line end. The first ": " ends the key, as in YAML.
KEY_LINE = re.compile(r"""^(?P<key>"(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s"'#`@%,\[\]{}&*!|>?:-][^\n]*?)[ \t]*:(?:[ \t]+|$)(?P<rest>.*)$""")
DOUBLE_QUOTED = re.compile(r'^"(?:[^"\\]|\\.)*"')
SINGLE_QUOTED = re.compile(r"^'(?:[^']|'')*'")
# Plain scalars a YAML parser types as something other than a string: the union of YAML 1.1 (PyYAML, used by
# the packaging validator) and the YAML 1.2 core schema (JavaScript parsers).
NON_STRING = [
    ("null", re.compile(r"^(?:~|null|Null|NULL)$")),
    ("boolean", re.compile(r"^(?:yes|Yes|YES|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)$")),
    ("number", re.compile(r"^[-+]?(?:0b[01_]+|0o?[0-7_]+|0x[0-9a-fA-F_]+|(?:0|[1-9][0-9_]*)(?::[0-5]?[0-9])*)$")),
    ("number", re.compile(r"^(?:[-+]?(?:[0-9][0-9_]*)?\.[0-9_]*(?:[eE][-+]?[0-9]+)?|[-+]?[0-9][0-9_]*(?:\.[0-9_]*)?[eE][-+]?[0-9]+"
                          r"|[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$")),
    ("date", re.compile(r"^(?:[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:[Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}"
                        r"(?:\.[0-9]*)?(?:[ \t]*(?:Z|[-+][0-9]{1,2}(?::[0-9]{2})?))?)$")),
]


class UsageError(Exception):
    pass


def read_text(path: Path) -> str | None:
    """Return file text, or None for binary or unreadable files."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def load(path: Path) -> tuple[str | None, str | None]:
    """Return (text, problem). Binary files give (None, None); unreadable or non-UTF-8 text gives a problem."""
    try:
        data = path.read_bytes()
    except OSError as error:
        return None, f"cannot read: {error.strerror or error}"
    if b"\0" in data[:BINARY_SNIFF_BYTES]:
        return None, None  # binary (image, archive): not text, nothing to check
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError as error:
        return None, f"not UTF-8 text (byte {error.start}); its content was not checked"


def bundled_files(root: Path, problems: dict[str, str]) -> list[str]:
    """Relative POSIX paths of every shipped file except SKILL.md; unwalkable folders go to problems."""
    found: list[str] = []

    def walk_error(error: OSError) -> None:
        rel = Path(error.filename).relative_to(root).as_posix() + "/"
        problems[rel] = f"cannot list folder: {error.strerror or error}"

    seen = {os.path.realpath(root)}  # symlinked folders are followed once; a link back up is a cycle
    for current, dirs, names in os.walk(root, onerror=walk_error, followlinks=True):
        keep = []
        for d in sorted(dirs):
            real = os.path.realpath(os.path.join(current, d))
            if d.startswith(".") or d in SKIP_DIRS or DEV_DIR.match(d) or real in seen:
                continue
            seen.add(real)
            keep.append(d)
        dirs[:] = keep
        for name in sorted(names):
            if name.startswith(".") or TEST_FILE.match(name):
                continue
            rel = Path(current, name).relative_to(root).as_posix()
            if rel != "SKILL.md":
                found.append(rel)
    return found


def chomp(text: str, indicator: str, trailing_blank: int) -> str:
    """Apply YAML block chomping: clip keeps one final newline, '-' strips it, '+' keeps every one."""
    if not text:
        return ""
    if "-" in indicator:
        return text
    if "+" in indicator:
        return text + "\n" * (1 + trailing_blank)
    return text + "\n"


def scalar(raw: str, block: list[str]) -> object:
    """Resolve one top-level YAML scalar (plain, quoted, folded, or literal)."""
    content = list(block)
    trailing_blank = 0
    while content and not content[-1].strip():
        content.pop()
        trailing_blank += 1
    if raw[:1] in (">", "|"):
        indicator = raw[1:].split("#", 1)[0].strip()
        indent = min((len(l) - len(l.lstrip()) for l in content if l.strip()), default=0)
        lines = [l[indent:] for l in content]
        if raw[0] == "|":
            return chomp("\n".join(lines), indicator, trailing_blank)
        # Folding: a break between two text lines becomes a space; each empty line becomes one newline.
        # shortcut: more-indented lines fold like the rest (YAML keeps their breaks); upgrade if a description uses them.
        out, empties = "", 0
        for line in lines:
            if not line.strip():
                empties += 1
                continue
            if out:
                out += " " if empties == 0 else "\n" * empties
            out += line
            empties = 0
        return chomp(out, indicator, trailing_blank)
    if not raw and any(re.match(r"^\s+[\w-]+:(\s|$)", l) for l in content):
        return {}  # nested mapping, not a string
    joined = " ".join([raw.strip()] + [l.strip() for l in content if l.strip()]).strip()
    double = re.fullmatch(r'"((?:[^"\\]|\\.)*)"\s*(?:#.*)?', joined)
    if double:
        try:
            return json.loads(f'"{double.group(1)}"')
        except json.JSONDecodeError:
            return double.group(1)
    single = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", joined)
    if single:
        return single.group(1).replace("''", "'")
    return re.sub(r"\s+#.*$", "", joined)


def parse_skill(text: str) -> tuple[dict, dict, int | None]:
    """Return (fields, field line numbers, index of closing '---' or None)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, {}, None
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, {}, None
    fields: dict = {}
    where: dict = {}
    i = 1
    while i < end:
        match = re.match(r"""^("[A-Za-z0-9_-]+"|'[A-Za-z0-9_-]+'|[A-Za-z0-9_-]+):\s*(.*)$""", lines[i])
        if not match:
            i += 1
            continue
        key = match.group(1).strip("\"'")  # a quoted key names the same field
        j = i + 1
        while j < end and (lines[j][:1] in (" ", "\t") or not lines[j].strip()):
            j += 1
        fields[key] = scalar(match.group(2).rstrip(), lines[i + 1 : j])
        where[key] = i + 1
        i = j
    return fields, where, end


def plain_type(text: str) -> str:
    """'string', or the non-string type a YAML parser gives this plain scalar."""
    if text == ".":
        return "string"  # a lone dot matches the float pattern's shape but is a string in both schemas
    return next((kind for kind, pattern in NON_STRING if pattern.match(text)), "string")


def strip_comment(text: str) -> str:
    return re.sub(r"(?:^|\s)#.*$", "", text).strip()


def scan_frontmatter(lines: list[str], end: int) -> tuple[list[tuple[int, str]], list[dict]]:
    """Find YAML errors every parser rejects, and the top-level entries, in lines[1:end].

    Returns (errors as (line, message), entries as {key, line, rest, block: [(line, text)]}).
    shortcut: flow values ([...], {...}), tags, anchors, and aliases are not parsed; upgrade if skills use them.
    """
    errors: list[tuple[int, str]] = []
    entries: list[dict] = []
    lines = list(lines)
    content = [k for k in range(1, end) if lines[k].strip() and not lines[k].lstrip().startswith("#")]
    base = len(lines[content[0]]) - len(lines[content[0]].lstrip(" ")) if content else 0
    for k in content if base else []:  # a mapping indented as a whole is valid YAML: read it dedented
        if lines[k].startswith(" " * base):
            lines[k] = lines[k][base:]
        else:
            errors.append((k + 1, "line is less indented than the first entry"))
    i = 1
    while i < end:
        line = lines[i]
        number = i + 1
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] == "\t":
            errors.append((number, "line is indented with a tab; YAML allows only spaces"))
            continue
        if line[0] == " ":
            errors.append((number, "indented line with no key above it"))
            continue
        match = KEY_LINE.match(line)
        if not match:
            errors.append((number, f"`{line.strip()[:QUOTE_MAX]}` is not a `key: value` entry"))
            continue
        key = match.group("key")
        if key[0] in "\"'":
            key = key[1:-1]
        rest = match.group("rest")
        value = strip_comment(rest)
        block: list[tuple[int, str]] = []
        if value[:1] in ("\"", "'"):
            quoted = DOUBLE_QUOTED if value[0] == '"' else SINGLE_QUOTED
            joined = rest.strip()
            while not quoted.match(joined) and i < end:  # a quoted value may continue on any later line
                block.append((i + 1, lines[i]))
                joined += " " + lines[i].strip()
                i += 1
            closed = quoted.match(joined)
            if not closed:
                errors.append((number, f"the quoted value of `{key}` is not closed"))
            elif strip_comment(joined[closed.end():]):
                errors.append((number, f"`{key}` has text after its closing quote"))
        while i < end and (not lines[i].strip() or lines[i][0] in " \t"
                           or (not value and re.match(r"^-(?:\s|$)", lines[i]))):  # indentless list under an empty key
            if lines[i][:1] == "\t":
                errors.append((i + 1, "line is indented with a tab; YAML allows only spaces"))
            block.append((i + 1, lines[i]))
            i += 1
        k = 0
        while not value and k < len(block):  # nested values (such as metadata.version): an opened quote must close
            at, text = block[k]
            k += 1
            nested = KEY_LINE.match(text.strip())
            inner = strip_comment(nested.group("rest")) if nested else ""
            if inner[:1] not in ("\"", "'"):
                continue
            quoted = DOUBLE_QUOTED if inner[0] == '"' else SINGLE_QUOTED
            joined = nested.group("rest").strip()
            while not quoted.match(joined) and k < len(block):
                joined += " " + block[k][1].strip()
                k += 1
            if not quoted.match(joined):
                errors.append((at, f"the quoted value of `{key}.{nested.group('key')}` is not closed"))
        entries.append({"key": key, "line": number, "rest": rest, "block": block})
        if not value or value[0] in "\"'|>[{!&*":
            continue
        if value[0] in "`@%," or re.match(r"^[-?](?:\s|$)", value):
            errors.append((number, f"the plain value of `{key}` starts with the reserved character `{value[0]}`"))
            continue
        for at, text in [(number, value)] + [(n, strip_comment(t)) for n, t in block]:
            if ": " in text or text.endswith(":"):
                errors.append((at, f"the plain value of `{key}` contains `:` followed by a space or the line end"))
                break
    if not entries and not errors:
        errors.append((1, "the frontmatter block is empty, so it parses to null, not a mapping"))
    seen: dict[str, int] = {}
    for entry in entries:
        if entry["key"] in seen:
            errors.append((entry["line"], f"duplicate key `{entry['key']}` (first on line {seen[entry['key']]})"))
        seen.setdefault(entry["key"], entry["line"])
    return sorted(errors), entries


def value_type(rest: str, block: list[tuple[int, str]]) -> str:
    """Type of one mapping value: 'string', 'flow', 'unknown', or a non-string type name."""
    value = strip_comment(rest)
    deeper = [t for _, t in block if t.strip() and not t.strip().startswith("#")]
    if not value:
        return ("list" if deeper[0].lstrip().startswith("-") else "nested map") if deeper else "null"
    if value[0] in "\"'|>":
        return "string"
    if value[0] in "[{":
        return "flow"
    if value[0] in "!&*":
        return "unknown"
    return plain_type(" ".join([value] + [strip_comment(t) for t in deeper]))


def metadata_problems(entry: dict) -> list[tuple[int, str]] | None:
    """Problems of a `metadata` entry as (line, message); None when it is flow style and cannot be decided."""
    value = strip_comment(entry["rest"])
    if value[:1] == "{":
        return None
    if value:
        return [(entry["line"], "`metadata` holds a single value, not a map of string keys to string values")]
    children = [(n, t) for n, t in entry["block"] if t.strip() and not t.strip().startswith("#")]
    if not children:
        return [(entry["line"], "`metadata` is empty (null), not a map")]
    indent = len(children[0][1]) - len(children[0][1].lstrip(" "))
    problems: list[tuple[int, str]] = []
    k = 0
    while k < len(children):
        number, text = children[k]
        k += 1
        nested = []
        while k < len(children) and len(children[k][1]) - len(children[k][1].lstrip(" ")) > indent:
            nested.append(children[k])
            k += 1
        if re.match(r"^-(?:\s|$)", text.strip()):
            return [(number, "`metadata` is a list, not a map")]
        match = KEY_LINE.match(text[indent:])
        if not match:
            problems.append((number, f"`{text.strip()[:QUOTE_MAX]}` is not a `key: value` entry"))
            continue
        key = match.group("key")
        if key[0] not in "\"'" and plain_type(key) != "string":
            problems.append((number, f"`metadata` key `{key}` is a {plain_type(key)}, not a string"))
        kind = value_type(match.group("rest"), nested)
        if kind == "flow":
            kind = "list" if strip_comment(match.group("rest")).startswith("[") else "nested map"
        if kind not in ("string", "unknown"):
            problems.append((number, f"`metadata.{key}` is a {kind}, not a string"))
    return problems


def unfenced(text: str):
    """Yield (line number, line) outside fenced code blocks, with inline code spans removed."""
    fence = ""
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_OPEN.match(line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) and not match.group(2).strip():
                fence = ""
            continue
        if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
            fence = match.group(1)
            continue
        yield number, CODE_SPAN.sub("", line)


def inside_root(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def link_targets(line: str) -> list[str]:
    """Relative-or-URL targets of the inline links and link definitions on one line, without #fragment."""
    raw = [a or b for a, b in MD_LINK.findall(line) + REF_DEF.findall(line)]
    return [t for t in (r.split("#", 1)[0] for r in raw) if t]


def finding(file: str, line: int | None, message: str, fix: str) -> dict:
    return {"file": file, "line": line, "message": message, "fix": fix}


def verdict(findings: list[dict]) -> dict:
    return {"status": "fail" if findings else "pass", "findings": findings}


NA = {"status": "n/a", "findings": []}


def has_dev_folder(root: Path) -> bool:
    """True when the skill holds an evaluation or test folder at any depth."""
    for _, dirs, _ in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
        if any(DEV_DIR.match(d) for d in dirs):
            return True
    return False


def audit(root: Path) -> tuple[dict, list[dict], dict[str, str]]:
    skill_text = read_text(root / "SKILL.md")
    if skill_text is None:
        raise UsageError(f"cannot read {root / 'SKILL.md'} as UTF-8 text")
    fields, where, end = parse_skill(skill_text)
    problems: dict[str, str] = {}  # path -> why its content could not be checked
    files = bundled_files(root, problems)
    texts: dict[str, str | None] = {}
    for rel in files:
        texts[rel], problem = load(root / rel)
        if problem:
            problems[rel] = problem

    # L1: bundled files SKILL.md names directly, by link or by relative path.
    linked = {
        os.path.normpath(target).replace(os.sep, "/")
        for line in skill_text.splitlines() for target in link_targets(line)
        if not re.match(r"^[a-z]+:", target, re.IGNORECASE)
    }
    l1 = {rel for rel in files if rel in skill_text or rel in linked}
    # Reference files: anything in references/, plus Markdown outside assets/ (output templates)
    # and scripts/ (run, not read).
    refs = [rel for rel in files if rel.startswith("references/")
            or (rel.endswith(".md") and not rel.startswith(("assets/", "scripts/")))]

    rules: dict[str, dict] = {}
    name, desc = fields.get("name"), fields.get("description")
    name_line, desc_line = where.get("name", 1), where.get("description", 1)
    has_name = isinstance(name, str) and name != ""

    if end is None:
        rules["BP-04"] = verdict([finding("SKILL.md", 1, "SKILL.md has no YAML frontmatter block between '---' lines",
                                          "Start SKILL.md with '---', then name and description fields, then '---'.")])
    elif not has_name:
        rules["BP-04"] = verdict([finding("SKILL.md", name_line, "frontmatter has no non-empty string `name`",
                                          "Add `name: <lowercase-hyphenated-name>` to the frontmatter.")])
    elif len(name) > NAME_MAX:
        rules["BP-04"] = verdict([finding("SKILL.md", name_line, f"`name` is {len(name)} characters, over {NAME_MAX}",
                                          f"Shorten `name` to {NAME_MAX} characters or fewer.")])
    else:
        rules["BP-04"] = verdict([])

    if has_name:
        rules["BP-05"] = verdict([] if NAME_CHARS.fullmatch(name) else [finding(
            "SKILL.md", name_line, f"`name` `{name}` has characters other than a-z, 0-9, and '-'",
            "Rename using only a-z, 0-9, and hyphens, without 'anthropic' or 'claude', to a name that says what the skill does.")])
        rules["BP-06"] = verdict([] if not TAG.search(name) else [finding(
            "SKILL.md", name_line, f"`name` contains an XML tag: {TAG.search(name).group(0)}",
            "Remove the tag from `name`.")])
        hit = RESERVED.search(name)
        rules["BP-07"] = verdict([] if not hit else [finding(
            "SKILL.md", name_line, f"`name` contains the reserved word `{hit.group(0)}`",
            "Rename without 'anthropic' or 'claude'.")])
    else:
        for rule_id in ("BP-05", "BP-06", "BP-07"):
            rules[rule_id] = dict(NA)

    if not isinstance(desc, str) or not desc.strip():
        rules["BP-08"] = verdict([finding("SKILL.md", desc_line, "frontmatter has no non-empty string `description`",
                                          "Add a `description` saying what the skill does and when to use it.")])
        rules["BP-09"] = dict(NA)
        rules["BP-10"] = dict(NA)
    else:
        rules["BP-08"] = verdict([])
        rules["BP-09"] = verdict([] if len(desc) <= DESCRIPTION_MAX else [finding(
            "SKILL.md", desc_line, f"`description` is {len(desc)} characters, over {DESCRIPTION_MAX}",
            f"Cut {len(desc) - DESCRIPTION_MAX}+ characters; keep capabilities and triggers, move detail into the body.")])
        tag = TAG.search(desc)
        rules["BP-10"] = verdict([] if not tag else [finding(
            "SKILL.md", desc_line, f"`description` contains an XML tag: {tag.group(0)}",
            "Remove angle-bracket markup from `description`; write placeholders in plain words.")])

    body_lines = len(skill_text.splitlines()) - (end + 1 if end is not None else 0)
    rules["BP-17"] = verdict([] if body_lines < BODY_LIMIT else [finding(
        "SKILL.md", None, f"body is {body_lines} lines; the limit is under {BODY_LIMIT}",
        "Move detailed or rarely needed sections into reference files linked from SKILL.md.")])

    rules["BP-21"] = verdict([finding(
        rel, None, "reference file is not linked directly from SKILL.md",
        f"Link `{rel}` from SKILL.md with a line saying when to read it.")
        for rel in refs if rel not in l1]) if refs else dict(NA)

    long_refs = [rel for rel in refs if rel.endswith((".md", ".txt")) and texts[rel]
                 and len(texts[rel].splitlines()) > TOC_THRESHOLD]
    toc_findings = []
    for rel in long_refs:
        lines = texts[rel].splitlines()
        toc = TOC_LINE if rel.endswith(".txt") else TOC_HEADING
        has_toc = any(toc.match(l) for l in lines[:TOC_WINDOW])
        if not has_toc:
            headings, anchors, fenced = 0, 0, False
            for line in lines:
                if FENCE.match(line):
                    fenced = not fenced
                elif not fenced and HEADING.match(line):
                    headings += 1
                    if headings == 2:
                        break
                elif not fenced and ANCHOR_ITEM.match(line):
                    anchors += 1
            has_toc = anchors >= TOC_MIN_LINKS
        if not has_toc:
            toc_findings.append(finding(
                rel, 1, f"{len(lines)} lines with no table of contents at the top",
                "Add a 'Contents' list of in-page links to every section right after the title."))
    rules["BP-22"] = verdict(toc_findings) if long_refs else dict(NA)

    def mentioned(rel: str, text: str) -> bool:
        names = [Path(rel).name]
        if Path(rel).suffix in (".py", ".js", ".ts", ".mjs", ".cjs"):
            names.append(Path(rel).stem)  # modules are imported by stem
        dirs = [p.as_posix() + "/" for p in Path(rel).parents if len(p.parts) >= 2]  # e.g. assets/brand/
        return rel in text or any(d in text for d in dirs) or any(
            re.search(rf"(?<![\w.-]){re.escape(n)}(?![\w-])", text) for n in names)

    # Reachable: named in SKILL.md, or in a file that is itself reachable (scripts call fixtures, etc.).
    reachable: set[str] = set()
    frontier = [skill_text]
    while frontier:
        text = frontier.pop()
        for rel in files:
            if rel not in reachable and mentioned(rel, text):
                reachable.add(rel)
                frontier.append(texts[rel] or "")
    candidates = [rel for rel in files
                  if not rel.startswith("agents/") and not Path(rel).name.upper().startswith("LICENSE")]
    rules["BP-39"] = verdict([finding(
        rel, None, "nothing in SKILL.md, or in any file it leads to, mentions this file",
        f"Name `{rel}` in SKILL.md with the condition for using it, or delete it if unused.")
        for rel in candidates if rel not in reachable]) if candidates else dict(NA)

    top_dirs = {rel.split("/", 1)[0].lower() for rel in files if "/" in rel}

    def is_path(candidate: str) -> bool:
        segments = BACKSLASHES.split(candidate)
        if not re.search(r"[A-Za-z]{2}", segments[0]):
            return False  # regex fragments such as -\d.eE start without a word
        return segments[0].lower() in COMMON_DIRS | top_dirs or bool(FILE_SEGMENT.match(segments[-1]))

    path_findings = []
    for rel, text in [("SKILL.md", skill_text)] + list(texts.items()):
        for number, line in enumerate((text or "").splitlines(), start=1):
            hits = {m.group(0).rstrip(".") for m in DRIVE_PATH.finditer(line)}  # a sentence period is not part of the path
            hits |= {h for m in BACKSLASH_PATH.finditer(line) if is_path(h := m.group(0).rstrip("."))}
            for written in sorted(h for h in hits if not any(h != o and h in o for o in hits)):
                fixed = BACKSLASHES.sub("/", written)
                path_findings.append(finding(
                    rel, number, f"backslash path `{written}`",
                    f"Write it with forward slashes: `{fixed}`."))
    rules["BP-40"] = verdict(path_findings)

    # Other official sources (OS-NN): the mechanical rules of references/other-official-sources.md.
    if has_name:
        bad = [why for why, hit in (("starts with a hyphen", name.startswith("-")), ("ends with a hyphen", name.endswith("-")),
                                    ("contains `--`", "--" in name)) if hit]
        fixed = re.sub(r"-{2,}", "-", name).strip("-")
        rules["OS-01"] = verdict([finding("SKILL.md", name_line, f"`name` `{name}` {' and '.join(bad)}",
                                          f"Rename to `{fixed}` and rename the folder to match.")] if bad else [])
        folder = root.resolve().name
        if (root / ".claude-plugin" / "plugin.json").is_file():
            rules["OS-02"] = dict(NA)  # SKILL.md at a plugin root: the folder is the plugin, not a skill folder
        else:
            rules["OS-02"] = verdict([] if name == folder else [finding(
                "SKILL.md", name_line, f"`name` `{name}` differs from the folder name `{folder}`",
                "Rename the folder or the `name` so the two are identical.")])
    else:
        rules["OS-01"] = dict(NA)
        rules["OS-02"] = dict(NA)

    raw_lines = skill_text.splitlines()
    opening = next((n for n, l in enumerate(raw_lines) if l.lstrip("\ufeff").strip() == "---"), None)
    late_block = (end is None and opening is not None
                  and not "".join(raw_lines[:opening] + [raw_lines[opening]]).lstrip("\ufeff").strip("- \t")
                  and any(l.strip() == "---" for l in raw_lines[opening + 1:]))
    if late_block:
        where_ = "after a byte-order mark" if raw_lines[0].startswith("\ufeff") else f"on line {opening + 1}"
        rules["OS-03"] = verdict([finding("SKILL.md", opening + 1, f"the opening `---` is {where_}, not alone on line 1",
                                          "Delete everything before the opening `---` so it is the file's first line.")])
    elif end is None:
        rules["OS-03"] = dict(NA)  # no frontmatter block at all: BP-04 reports it
    entries: list[dict] = []
    if end is not None:
        errors, entries = scan_frontmatter(raw_lines, end)
        rules["OS-03"] = verdict([finding("SKILL.md", n, f"frontmatter YAML error: {m}",
                                          "Fix the line; quote any value that holds `: ` or starts with a reserved character.")
                                  for n, m in errors])
        rules["OS-04"] = verdict([finding("SKILL.md", e["line"], f"`{e['key']}` is not a recognised frontmatter field",
                                          "Correct the spelling, or move the data under `metadata`.")
                                  for e in entries if e["key"] not in KNOWN_KEYS])
    else:
        rules["OS-04"] = dict(NA)

    by_key = {e["key"]: e for e in entries}
    os06: list[dict] = []
    undecided = False
    if "metadata" in by_key:
        meta_problems = metadata_problems(by_key["metadata"])
        undecided = meta_problems is None
        os06 += [finding("SKILL.md", n, m, 'Quote each value (`version: "0.1"`) and flatten nested data.') for n, m in meta_problems or []]
    if "compatibility" in by_key:
        entry = by_key["compatibility"]
        kind = value_type(entry["rest"], entry["block"])
        compat = fields.get("compatibility")
        if kind not in ("string", "unknown"):
            os06.append(finding("SKILL.md", entry["line"], f"`compatibility` is a {kind}, not a string",
                                "Write `compatibility` as one quoted string."))
        elif isinstance(compat, str) and not 1 <= len(compat) <= COMPATIBILITY_MAX:
            os06.append(finding("SKILL.md", entry["line"], f"`compatibility` is {len(compat)} characters; allowed 1 to {COMPATIBILITY_MAX}",
                                f"Shorten `compatibility` to {COMPATIBILITY_MAX} characters or fewer."))
    if "metadata" not in by_key and "compatibility" not in by_key:
        rules["OS-06"] = dict(NA)
    else:
        rules["OS-06"] = verdict(os06)
        if undecided and not os06:
            rules["OS-06"]["status"] = "n/a"
            rules["OS-06"]["not_evaluated"] = [{"file": "SKILL.md", "reason": "flow-style `metadata` ({...}) is not parsed; judge it by reading"}]

    when = fields.get("when_to_use")
    if "when_to_use" not in fields:
        rules["OS-08"] = dict(NA)
    else:
        total = len(desc if isinstance(desc, str) else "") + len(when if isinstance(when, str) else "")
        rules["OS-08"] = verdict([] if total <= LISTING_MAX else [finding(
            "SKILL.md", where.get("when_to_use", 1), f"`description` plus `when_to_use` is {total} characters, over {LISTING_MAX}",
            f"Cut {total - LISTING_MAX}+ characters from `when_to_use`; put the key use case first in `description`.")])

    link_findings, links = [], 0
    real_root = root.resolve()  # a skill folder that is itself a symlink is fine; only links leaving it fail
    for rel, text in [("SKILL.md", skill_text)] + [(r, texts[r]) for r in refs if r.endswith(".md")]:
        for number, line in unfenced(text or ""):
            for target in link_targets(line):
                if URL_SCHEME.match(target):
                    continue
                links += 1
                resolved = os.path.normpath(os.path.join(os.path.dirname(rel), unquote(target)))
                if target.startswith("/") or resolved == ".." or resolved.startswith("../"):
                    link_findings.append(finding(rel, number, f"link `{target}` points outside the skill directory",
                                                 "Link a file inside the skill, or give the outside location as plain text."))
                elif not (root / resolved).exists():
                    link_findings.append(finding(rel, number, f"link `{target}` points to a missing file",
                                                 "Correct the path, add the file, or remove the link."))
                elif not inside_root((root / resolved).resolve(), real_root):
                    link_findings.append(finding(rel, number, f"link `{target}` resolves outside the skill directory through a symlink",
                                                 "Replace the symlink with the real file: an installed or uploaded skill carries only its own folder."))
    rules["OS-11"] = verdict(link_findings) if links else dict(NA)

    # Content the script could not check: the affected rules say so instead of passing silently.
    for path, reason in sorted(problems.items()):
        if path.endswith("/"):
            affected = ["BP-21", "BP-22", "BP-39", "BP-40", "OS-11"]  # an unlisted folder hides its files
        else:
            affected = ["BP-39", "BP-40"] + (["BP-22"] if path in refs and path.endswith((".md", ".txt")) else []) \
                + (["OS-11"] if path in refs and path.endswith(".md") else [])
        for rule_id in affected:
            rule = rules[rule_id]
            rule.setdefault("not_evaluated", []).append({"file": path, "reason": reason})
            if rule["status"] != "fail":
                rule["status"] = "n/a"  # no confirmed failure and partly unread: not evaluated

    # Judgment rules whose n/a clause the skill's composition alone decides. Each test errs towards "judge it".
    skipped: dict[str, str] = {}
    if not has_dev_folder(root):
        skipped.update(dict.fromkeys(EVALUATION_RULES, "no evaluation material (BP-32)"))
    if not files and not problems:
        skipped["BP-52"] = skipped["BP-54"] = "no bundled files"
    if "!`" not in skill_text and "```!" not in skill_text:
        skipped["OS-10"] = "the body has no injected command"
    if "allowed-tools" not in fields:
        skipped["OS-17"] = "`allowed-tools` is absent"

    return (dict(sorted(rules.items())), [{"file": k, "reason": v} for k, v in sorted(problems.items())],
            dict(sorted(skipped.items())))


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 2:
            raise UsageError("expected exactly one argument: the path to a skill directory")
        root = Path(argv[1])
        if not root.is_dir():
            raise UsageError(f"not a directory: {root}")
        if not (root / "SKILL.md").is_file():
            raise UsageError(f"no SKILL.md in {root}; pass the directory that holds the skill's SKILL.md")
        rules, unreadable, skipped = audit(root)
    except UsageError as error:
        print(f"check_mechanical: {error}\nusage: python3 check_mechanical.py <skill-dir>", file=sys.stderr)
        return 2
    print(json.dumps({"target": str(root), "rules": rules, "unreadable": unreadable, "not_applicable": skipped}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
