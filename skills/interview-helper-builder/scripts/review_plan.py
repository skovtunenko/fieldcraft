#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Render an offline draft reviewer or apply its compact feedback."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from generate_interview_helper import section_minutes, serialize_for_script

FORMAT = "interview-review-v1"
FIELDS = {"section": {"title", "minutes", "meta", "coach"},
          "question": {"title", "ask", "purpose"}}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def draft_items(spec: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    require(isinstance(spec, dict), "draft must be an object")
    for field in ("candidate", "role"):
        require(field not in spec or isinstance(spec[field], str), f"{field} must be text")
    require("durationMinutes" not in spec or (type(spec["durationMinutes"]) is int and spec["durationMinutes"] > 0),
            "durationMinutes must be a positive integer when present")
    for field in ("deepestProbes", "outOfScope"):
        require(field not in spec or (isinstance(spec[field], list) and all(isinstance(x, str) for x in spec[field])),
                f"{field} must be an array of text")
    for field in ("candidateFacts", "candidateInsights"):
        entries = spec.get(field, [])
        require(isinstance(entries, list) and all(
            isinstance(x, dict) and set(x) == {"text", "source"}
            and all(isinstance(x[k], str) and x[k].strip() for k in ("text", "source")) for x in entries),
            f"{field} must contain text and source strings")
    requirements = spec.get("requirements", [])
    require(isinstance(requirements, list) and all(
        isinstance(x, dict) and set(x) == {"id", "text"}
        and all(isinstance(x[k], str) and x[k].strip() for k in ("id", "text")) for x in requirements)
        and len({x["id"] for x in requirements}) == len(requirements),
        "requirements must contain unique id and text strings")
    sections = spec.get("sections")
    require(isinstance(sections, list) and bool(sections), "draft needs sections")
    items: dict[str, dict[str, dict[str, Any]]] = {"section": {}, "question": {}}
    for section in sections:
        require(isinstance(section, dict), "section must be an object")
        require(isinstance(section.get("questions"), list), "section needs a questions array")
        for kind, obj in [("section", section)] + [("question", q) for q in section["questions"]]:
            require(isinstance(obj, dict), f"{kind} must be an object")
            key = obj.get("id")
            require(isinstance(key, str) and bool(key.strip()), f"{kind} needs a string ID")
            require(key not in items[kind], f"duplicate {kind} ID: {key}")
            for field in FIELDS[kind]:
                require(field not in obj or isinstance(obj[field], str), f"{kind} {key}: {field} must be text")
            if kind == "question" and "origin" in obj:
                require(obj["origin"] in ("prepared", "new"), f"question {key}: invalid origin")
            if kind == "question" and "estimatedMinutes" in obj:
                require(type(obj["estimatedMinutes"]) in (int, float) and obj["estimatedMinutes"] > 0,
                        f"question {key}: estimatedMinutes must be positive")
            if kind == "section" and "requirementIds" in obj:
                require(isinstance(obj["requirementIds"], list) and all(isinstance(x, str) for x in obj["requirementIds"]),
                        f"section {key}: requirementIds must be strings")
            items[kind][key] = obj
    return items


def fingerprint(spec: dict[str, Any]) -> str:
    raw = json.dumps(spec, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _minutes(value: Any) -> Any:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*m?\s*", value) if isinstance(value, str) else None
    return float(match[1]) if match else float(value) if type(value) in (int, float) else value


def _moved(old: list[str], new: list[str]) -> set[str]:
    """IDs outside the longest run kept in the old relative order, so one move marks one item."""
    common = [key for key in new if key in old]
    rank = {key: i for i, key in enumerate(key for key in old if key in common)}
    best: list[list[str]] = []
    for key in common:
        chain = max((c for c in best if rank[c[-1]] < rank[key]), key=len, default=[])
        best.append(chain + [key])
    return set(common) - set(max(best, key=len, default=[]))


def round_changes(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Mark what changed since the previous draft by stable ID; index renumbering alone is not a change."""
    old, new = draft_items(previous), draft_items(current)
    content = {"section": ("title", "meta", "requirementIds"), "question": ("title", "ask", "purpose")}
    timing = {"section": "minutes", "question": "estimatedMinutes"}
    parent = lambda spec: {q["id"]: s["id"] for s in spec["sections"] for q in s["questions"]}
    old_parent, new_parent = parent(previous), parent(current)
    moved = {"section": _moved([s["id"] for s in previous["sections"]], [s["id"] for s in current["sections"]]),
             "question": set()}
    for section in current["sections"]:
        before = next((s for s in previous["sections"] if s["id"] == section["id"]), None)
        if before:
            moved["question"] |= _moved([q["id"] for q in before["questions"]], [q["id"] for q in section["questions"]])
    marks: dict[str, dict[str, list[str]]] = {"section": {}, "question": {}}
    for kind in marks:
        for key, item in new[kind].items():
            before = old[kind].get(key)
            if before is None:
                tags = ["added"]
            else:
                tags = [tag for tag, hit in (
                    ("edited", any(before.get(f) != item.get(f) for f in content[kind])),
                    ("time", _minutes(before.get(timing[kind])) != _minutes(item.get(timing[kind]))),
                    ("moved", key in moved[kind] or (kind == "question" and old_parent[key] != new_parent[key]))) if hit]
            if tags:
                marks[kind][key] = tags
    gone = {s["id"] for s in previous["sections"]} - set(new["section"])
    removed = [{"kind": "section", "title": s.get("title", "")} for s in previous["sections"] if s["id"] in gone]
    removed += [{"kind": "question", "title": q.get("title", "")} for s in previous["sections"] if s["id"] not in gone
                for q in s["questions"] if q["id"] not in new["question"]]
    return {"sections": marks["section"], "questions": marks["question"], "removed": removed}


def approval_errors(spec: dict[str, Any]) -> list[str]:
    errors = []
    if not spec.get("candidate") or not spec.get("role"):
        errors.append("Candidate and role are required.")
    duration = spec.get("durationMinutes")
    if type(duration) is not int or duration <= 0:
        errors.append("Confirm a positive duration in minutes.")
    total = 0.0
    for section in spec["sections"]:
        if not section.get("title", "").strip() or not section["questions"]:
            errors.append("Each included section needs a title and a question.")
        try:
            total += section_minutes(section.get("minutes"))
        except ValueError as exc:
            errors.append(str(exc))
        for q in section["questions"]:
            if not all(q.get(k, "").strip() for k in ("title", "ask")):
                errors.append("Each included question needs a title and wording.")
    if type(duration) is int and abs(total - duration) > 0.01:
        errors.append(f"Timeboxes total {total:g}m; expected {duration}m.")
    if not spec["sections"]:
        errors.append("Keep at least one question.")
    return list(dict.fromkeys(errors))


def apply_feedback(spec: dict[str, Any], feedback: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    draft_items(spec)
    require(isinstance(feedback, dict), "feedback must be an object")
    require(not set(feedback) - {"format", "base", "approved", "edits", "layout", "excluded", "excludedSections", "timing", "comments", "addedSections", "addedQuestions"},
            "unsupported feedback fields")
    require(feedback.get("format") == FORMAT, "unsupported feedback format")
    require(feedback.get("base") == fingerprint(spec), "feedback belongs to a different draft revision")
    require(type(feedback.get("approved")) is bool, "feedback needs an explicit approved boolean")
    updated = copy.deepcopy(spec)
    items = draft_items(updated)
    additions = feedback.get("addedSections", [])
    require(isinstance(additions, list), "addedSections must be an array")
    added_ids = set()
    for addition in additions:
        require(isinstance(addition, dict) and set(addition) == {"id", "title", "minutes"}, "invalid added section")
        key = addition["id"]
        require(isinstance(key, str) and bool(key.strip()) and key not in items["section"], "duplicate or invalid added section ID")
        require(all(isinstance(addition[k], str) for k in ("title", "minutes")) and bool(addition["title"].strip()),
                "added section needs a title and text timebox")
        section = {**addition, "requirementIds": [], "questions": []}
        items["section"][key] = section
        updated["sections"].append(section)
        added_ids.add(key)
    require(not additions or not feedback["approved"], "new section requests require another review before approval")
    asks = feedback.get("addedQuestions", [])
    require(isinstance(asks, list), "addedQuestions must be an array")
    for ask in asks:
        require(isinstance(ask, dict) and set(ask) == {"id", "text"}, "invalid added question")
        key = ask["id"]
        require(isinstance(key, str) and bool(key.strip()) and key not in items["question"], "duplicate or invalid added question ID")
        require(isinstance(ask["text"], str), "added question text must be text")
        # Empty title and ask keep the plan unapprovable until the agent drafts the question from the request text.
        items["question"][key] = {"id": key, "origin": "new", "title": "", "ask": ""}
    require(not asks or feedback.get("layout") is not None, "added questions need a layout that places them")
    require(not asks or not feedback["approved"], "new question requests require another review before approval")
    edits = feedback.get("edits", [])
    require(isinstance(edits, list), "edits must be an array")
    seen = set()
    for edit in edits:
        require(isinstance(edit, dict) and set(edit) == {"kind", "id", "field", "value"}, "invalid field edit")
        kind, key, field, value = (edit[k] for k in ("kind", "id", "field", "value"))
        require(isinstance(kind, str) and kind in items and isinstance(key, str) and key in items[kind], "unknown edit target")
        require(isinstance(field, str) and field in FIELDS[kind] and isinstance(value, str), "unsupported field edit")
        signature = (kind, key, field)
        require(signature not in seen, "duplicate field edit")
        seen.add(signature)
        items[kind][key][field] = value

    timing = feedback.get("timing", [])
    require(isinstance(timing, list), "timing must be an array")
    timed = set()
    for entry in timing:
        require(isinstance(entry, dict) and set(entry) == {"kind", "id", "minutes"}, "invalid timing request")
        kind, key, minutes = entry["kind"], entry["id"], entry["minutes"]
        require(isinstance(kind, str) and kind in items and isinstance(key, str) and key in items[kind], "unknown timing target")
        require(type(minutes) is int and minutes > 0, "timing minutes must be a positive integer")
        require((kind, key) not in timed, "duplicate timing request")
        timed.add((kind, key))
        if kind == "question":
            items[kind][key]["estimatedMinutes"] = minutes
        else:
            items[kind][key]["minutes"] = f"{minutes}m"

    layout = feedback.get("layout")
    if layout is not None:
        require(isinstance(layout, list), "layout must be an array")
        section_ids, question_ids = [], []
        for row in layout:
            require(isinstance(row, dict) and set(row) == {"id", "questions"}, "invalid layout row")
            require(isinstance(row["id"], str) and row["id"] in items["section"], "unknown layout section")
            require(isinstance(row["questions"], list) and all(isinstance(q, str) and q in items["question"] for q in row["questions"]),
                    "unknown layout question")
            section_ids.append(row["id"])
            question_ids.extend(row["questions"])
        require(len(section_ids) == len(set(section_ids)) and set(section_ids) == set(items["section"]), "layout must contain every section exactly once")
        require(len(question_ids) == len(set(question_ids)) and set(question_ids) == set(items["question"]), "layout must contain every question exactly once")
        updated["sections"] = [items["section"][row["id"]] for row in layout]
        for row, section in zip(layout, updated["sections"]):
            section["questions"] = [items["question"][qid] for qid in row["questions"]]

    excluded = feedback.get("excluded", [])
    require(isinstance(excluded, list) and all(isinstance(q, str) and q in items["question"] for q in excluded), "unknown excluded question")
    require(len(excluded) == len(set(excluded)), "duplicate exclusion")
    excluded_sections = feedback.get("excludedSections", [])
    draft_sections = {s["id"] for s in spec["sections"]}
    require(isinstance(excluded_sections, list) and all(isinstance(s, str) and s in draft_sections for s in excluded_sections),
            "unknown or added excluded section")
    require(len(excluded_sections) == len(set(excluded_sections)), "duplicate section exclusion")
    comments = feedback.get("comments", [])
    require(isinstance(comments, list), "comments must be an array")
    for comment in comments:
        require(isinstance(comment, dict) and set(comment) == {"kind", "id", "text"}, "invalid comment")
        kind, key = comment["kind"], comment["id"]
        require(isinstance(kind, str) and kind in items and isinstance(key, str) and key in items[kind], "unknown comment target")
        require(isinstance(comment["text"], str) and bool(comment["text"].strip()), "empty comment")

    # Layout already ran, so a removed section drops only the questions it holds in the requested order.
    updated["sections"] = [s for s in updated["sections"] if s["id"] not in excluded_sections]
    for section in updated["sections"]:
        section["questions"] = [q for q in section["questions"] if q["id"] not in excluded]
    keep_empty = added_ids | {s["id"] for s in spec["sections"] if not s["questions"]}
    updated["sections"] = [s for s in updated["sections"] if s["questions"] or s["id"] in keep_empty]
    for si, section in enumerate(updated["sections"], 1):
        section["index"] = str(si)
        for qi, question in enumerate(section["questions"], 1):
            question["index"] = f"{si}.{qi}"
    errors = approval_errors(updated)
    require(not feedback["approved"] or (not comments and not errors), "approval requires resolved comments and a complete, time-balanced plan")
    report = {"approved": feedback["approved"], "comments": comments, "excluded": excluded,
              "excludedSections": excluded_sections, "timing": timing, "addedQuestions": asks, "approvalErrors": errors}
    return updated, report


def _parse(text: str, path: Path) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON (line {exc.lineno}, column {exc.colno})") from None


def read_json(path: Path) -> Any:
    return _parse(path.read_text(encoding="utf-8"), path)


def read_feedback(path: Path) -> Any:
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("{"):
        return _parse(text, path)
    blocks = re.findall(r"<interview_review>\s*([\s\S]*?)\s*</interview_review>", text)
    require(len(blocks) == 1, "feedback prompt needs exactly one interview_review block")
    return _parse(blocks[0], path)


# What the person running the review should do next, keyed by the internal check that failed.
ADVICE = {
    "feedback belongs to a different draft revision": "This review was made for a different version of the plan. "
        "Open the latest review page, carry your notes over, and copy the review prompt again.",
    "feedback prompt needs exactly one interview_review block": "The pasted text holds no review, or more than one. "
        "Press Copy review prompt on the review page and paste the whole text once.",
    "unsupported feedback format": "This review comes from an incompatible review page. "
        "Render the review page again and copy a new review prompt.",
    "approval requires resolved comments and a complete, time-balanced plan": "The plan cannot be approved yet: "
        "resolve every comment and make the timeboxes add up to the interview length.",
    "keep feedback and report separate from draft/output": "Use separate files for the pasted review prompt "
        "and the report. The output may update the draft in place.",
    "review HTML must not overwrite the draft": "The review page would overwrite the draft. Choose another --output path.",
    "review template needs one data marker": "The installed review template is damaged. Reinstall the skill.",
}


def explain(exc: Exception, stage: str) -> str:
    """Turn a failed check into a sentence that says what happened and what to do."""
    if isinstance(exc, FileNotFoundError):
        return f"File not found: {exc.filename}. Check the path and run the command again."
    if isinstance(exc, OSError):
        return f"Cannot use {exc.filename or 'a file'}: {exc.strerror or exc}. Check the path and its permissions."
    message = str(exc)
    if message in ADVICE:
        return ADVICE[message]
    if "is not valid JSON" in message:
        return f"{message}. Fix the file or create it again."
    if stage == "temporary":
        return f"Cannot prepare temporary files: {message}"
    if stage == "draft":
        return f"The draft cannot be used: {message}. Fix the draft JSON and run the command again."
    return (f"The review prompt cannot be applied: {message}. Copy the review prompt again from the latest "
            "review page; if it still fails, render the review page again.")


def previous_changes(path: Path, spec: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Change marks against the previous draft, or a warning; a bad previous draft never blocks the review."""
    skip = "The review page is built without change marks."
    try:
        text = path.read_text(encoding="utf-8")
        if text.lstrip().startswith("{"):
            previous = _parse(text, path)
        else:
            embedded = re.search(r'''<script\b[^>]*\bid=["']reviewData["'][^>]*>([\s\S]*?)</script\s*>''', text, re.I)
            require(embedded is not None, "previous review page has no embedded draft")
            previous = _parse(embedded[1], path)["spec"]
        if isinstance(previous, dict) and fingerprint(previous) == fingerprint(spec):
            return None, f"The previous draft {path} is identical to this draft, so nothing is marked as changed."
        return round_changes(previous, spec), None
    except FileNotFoundError:
        return None, f"Previous draft not found: {path}. {skip}"
    except (ValueError, TypeError, KeyError, OSError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else "its structure is not a draft"
        return None, f"The previous draft {path} cannot be compared ({reason}). {skip}"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def ignore_temporary(output_dir: Path, paths: list[Path]) -> None:
    """Register exact temporary paths before any caller writes them."""
    root = output_dir.resolve()
    relative = []
    for path in paths:
        try:
            name = path.resolve().relative_to(root).as_posix()
        except ValueError:
            raise ValueError(f"Temporary path {path} is outside output-dir {root}.") from None
        require(name != "." and not path.is_dir() and
                not {".git", ".gitignore"}.intersection(Path(name).parts),
                f"Not a temporary file path: {path}.")
        require(not any(c in name for c in "\n\r\0"), f"Temporary path contains a line break or NUL: {path!s}.")
        relative.append(name)
    root.mkdir(parents=True, exist_ok=True)
    repo = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                          capture_output=True, text=True)
    if repo.returncode:
        require("not a git repository" in repo.stderr.lower(), f"Cannot inspect Git repository: {repo.stderr.strip()}")
        return
    require(repo.stdout.strip() == "true", "output-dir must be a working directory, not Git metadata.")
    ignore = root / ".gitignore"
    require(not ignore.is_symlink(), f"Local .gitignore must not be a symlink: {ignore}.")
    existing = ignore.read_bytes() if ignore.exists() else b""
    lines = set(existing.splitlines())
    additions = []
    for name in relative:
        rule = ("/" + "".join("\\" + c if c in "\\*?[]#! " else c for c in name)).encode("utf-8")
        if rule not in lines:
            additions.append(rule)
            lines.add(rule)
    if additions:
        with ignore.open("ab") as stream:
            if existing and not existing.endswith(b"\n"):
                stream.write(b"\n")
            stream.write(b"\n".join(additions) + b"\n")
    for name in relative:
        tracked = subprocess.run(["git", "--literal-pathspecs", "-C", str(root), "ls-files", "--cached", "-z", "--", name],
                                 capture_output=True, check=True)
        if tracked.stdout:
            print(f"Warning: temporary file is already tracked by Git: {root / name}. "
                  "It remains in the index; report this to the interviewer.", file=sys.stderr)
        ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", "-q", "--", "./" + name],
                                 capture_output=True)
        require(ignored.returncode == 0, f"Git does not ignore {root / name}; check nested .gitignore overrides before writing it.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render", help="Inject a draft into the bundled offline reviewer")
    apply = sub.add_parser("apply", help="Apply exported feedback to its exact base draft")
    ignore = sub.add_parser("ignore", help="Register agent-written temporary files before creating them")
    ignore.add_argument("--output-dir", type=Path, required=True)
    ignore.add_argument("paths", type=Path, nargs="+")
    for command in (render, apply):
        command.add_argument("--spec", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--output-dir", type=Path, help="Artifact directory; defaults to the input draft's parent")
    render.add_argument("--previous", type=Path, help="Earlier draft or existing review HTML; may be the same as --output")
    apply.add_argument("--feedback", type=Path, required=True)
    apply.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    stage = "draft"
    try:
        if args.command == "ignore":
            stage = "temporary"
            ignore_temporary(args.output_dir, args.paths)
            return
        spec = read_json(args.spec)
        draft_items(spec)
        if args.command == "render":
            require(args.output.resolve() != args.spec.resolve(), "review HTML must not overwrite the draft")
            template = (Path(__file__).resolve().parents[1] / "assets" / "interview-review-template.html").read_text(encoding="utf-8")
            marker = "__REVIEW_DATA_JSON__"
            require(template.count(marker) == 1, "review template needs one data marker")
            data = {"base": fingerprint(spec), "spec": spec, "source": str(args.spec.resolve())}
            if args.previous:
                changes, warning = previous_changes(args.previous, spec)
                if changes:
                    data["changes"] = changes
                if warning:
                    print(f"Note: {warning}", file=sys.stderr)
            stage = "temporary"
            ignore_temporary(args.output_dir or args.spec.parent, [args.output])
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(template.replace(marker, serialize_for_script(data)), encoding="utf-8")
        else:
            base, feedback, output, report_path = (p.resolve() for p in (args.spec, args.feedback, args.output, args.report))
            require(len({base, feedback, report_path}) == 3 and output not in {feedback, report_path},
                    "keep feedback and report separate from draft/output")
            stage = "feedback"
            updated, report = apply_feedback(spec, read_feedback(args.feedback))
            stage = "temporary"
            ignore_temporary(args.output_dir or args.spec.parent, [args.output, args.report])
            write_json(args.output, updated)
            write_json(args.report, report)
        print(args.output)
    except (ValueError, TypeError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Error: {explain(exc, stage)}\n")


if __name__ == "__main__":
    main()
