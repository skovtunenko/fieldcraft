#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Generate a self-contained interview helper HTML from an approved JSON spec."""
from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

MIN_POSITIVES = 8
MIN_NEGATIVES = 6
LANGUAGE_TAG = re.compile(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*")
APPROVED_SECTION_FIELDS = ("title", "minutes")
APPROVED_QUESTION_FIELDS = ("title", "ask", "purpose", "estimatedMinutes")
PROFILE_LISTS = ("standouts", "inconsistencies", "probes")
MAX_PROFILE_ITEMS = 5
MAX_TIMELINE = 12
TIMELINE_DATE = re.compile(r"\d{4}(?:-(?:0[1-9]|1[0-2]))?")
QUESTION_REF = re.compile(r"→\s*(\S+)\s*$")  # same pattern as QREF in the template
CAREER_IDENTITY = ("org", "role", "from", "to", "source", "dateNote")

REQUIRED_TOP = [
    "candidate", "role", "durationMinutes", "analysisContext", "outOfScope", "sections", "scoreDimensions",
]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def section_minutes(value: Any) -> float:
    """A positive timebox, or zero for the explicit reserve label."""
    text = value.strip() if isinstance(value, str) else ""
    if text == "if time":
        return 0.0
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*m?", text)
    minutes = float(match[1]) if match else 0.0
    if not math.isfinite(minutes) or minutes <= 0:
        raise ValueError("Use a positive timebox (e.g. 10m) or 'if time'.")
    return minutes


def untranslated_cyrillic(spec: dict[str, Any]) -> bool:
    """Preserve the candidate's name; check the remaining English spec content."""
    content = {key: value for key, value in spec.items() if key != "candidate"}
    return spec.get("language", "en").split("-")[0] == "en" and bool(
        re.search(r"[\u0400-\u04FF]", json.dumps(content, ensure_ascii=False))
    )


def slug(value: Any) -> str:
    """Mirror of simpleSlug in the template: lowercase NFC, runs of non-letter/mark/digit become one hyphen."""
    text = unicodedata.normalize("NFC", str(value or "interview").lower())
    text = "".join(c if unicodedata.category(c)[0] in "LMN" else "-" for c in text)
    return re.sub(r"-+", "-", text).strip("-") or "interview"


def reject_slug_collisions(qid: str, kind: str, texts: list[str]) -> None:
    seen: dict[str, str] = {}
    for text in texts:
        if slug(text) in seen:
            fail(f"question {qid} has {kind} that share one state key: {seen[slug(text)]!r} and {text!r}")
        seen[slug(text)] = text


def validate_followups(qid: str, q: dict[str, Any]) -> None:
    """A follow-up is text or {text, listenFor?, warnIf?} naming this question's own signals."""
    if not isinstance(q["followups"], list):
        fail(f"question {qid} followups must be a list")
    pools = {"listenFor": [str(x) for x in q["positives"]], "warnIf": [str(x) for x in q["negatives"]]}
    reject_slug_collisions(qid, "positives", pools["listenFor"])
    reject_slug_collisions(qid, "negatives", pools["warnIf"])
    texts: list[str] = []
    paired: set[tuple[str, str]] = set()
    for fu in q["followups"]:
        if isinstance(fu, str):
            text = fu
        elif isinstance(fu, dict) and isinstance(fu.get("text"), str) and fu["text"].strip():
            text = fu["text"]
            unknown = set(fu) - {"text", "listenFor", "warnIf"}
            if unknown:
                fail(f"question {qid} follow-up has unknown fields {sorted(unknown)}: {text}")
            if "listenFor" not in fu and "warnIf" not in fu:
                fail(f"question {qid} follow-up object needs listenFor or warnIf: {text}")
            for field, pool in pools.items():
                if field not in fu:
                    continue
                value = fu[field]
                if value not in pool:
                    kind = "positives" if field == "listenFor" else "negatives"
                    fail(f"question {qid} {field} is not one of its {kind}: {value}")
                if (field, value) in paired:
                    fail(f"question {qid} pairs one signal with two follow-ups: {value}")
                paired.add((field, value))
        else:
            fail(f"question {qid} follow-up must be text or an object with non-empty text")
        texts.append(text)
    reject_slug_collisions(qid, "follow-ups", texts)


def validate_spec(spec: dict[str, Any]) -> None:
    for key in REQUIRED_TOP:
        if key not in spec:
            fail(f"missing required field: {key}")
    if not isinstance(spec["candidate"], str) or not spec["candidate"].strip():
        fail("candidate must be a non-empty string")
    if not isinstance(spec["role"], str) or not spec["role"].strip():
        fail("role must be a non-empty string")
    if not isinstance(spec["durationMinutes"], int) or spec["durationMinutes"] <= 0:
        fail("durationMinutes must be a positive integer")
    if not isinstance(spec["sections"], list) or not spec["sections"]:
        fail("sections must be a non-empty list")
    if not isinstance(spec["scoreDimensions"], list) or not spec["scoreDimensions"]:
        fail("scoreDimensions must be a non-empty list")

    section_ids: set[str] = set()
    question_ids: set[str] = set()
    timeboxed_minutes = 0.0
    for section in spec["sections"]:
        for key in ("id", "title", "minutes", "meta", "coach", "questions"):
            if key not in section:
                fail(f"section missing field: {key}")
        sid = str(section["id"])
        if sid in section_ids:
            fail(f"duplicate section id: {sid}")
        section_ids.add(sid)
        try:
            timeboxed_minutes += section_minutes(section["minutes"])
        except ValueError as exc:
            fail(f"section {sid}: {exc}")
        if not isinstance(section["questions"], list) or not section["questions"]:
            fail(f"section {sid} has no questions")
        for q in section["questions"]:
            for key in ("id", "index", "title", "purpose", "ask", "followups", "positives", "negatives"):
                if key not in q:
                    fail(f"question in section {sid} missing field: {key}")
            qid = str(q["id"])
            if qid in question_ids:
                fail(f"duplicate question id: {qid}")
            question_ids.add(qid)
            if not str(q["ask"]).strip():
                fail(f"question {qid} has an empty ask field")
            if not isinstance(q["positives"], list) or len(q["positives"]) < MIN_POSITIVES:
                fail(f"question {qid} needs at least {MIN_POSITIVES} positive signals")
            if not isinstance(q["negatives"], list) or len(q["negatives"]) < MIN_NEGATIVES:
                fail(f"question {qid} needs at least {MIN_NEGATIVES} negative signals")
            validate_followups(qid, q)

    if abs(timeboxed_minutes - spec["durationMinutes"]) > 0.01:
        fail(
            f"section minutes sum to {timeboxed_minutes:g}, expected durationMinutes "
            f"{spec['durationMinutes']}; reserve sections use \"if time\""
        )

    score_keys: set[str] = set()
    for dim in spec["scoreDimensions"]:
        if "key" not in dim or "label" not in dim:
            fail("each score dimension needs key and label")
        key = str(dim["key"])
        if key in score_keys:
            fail(f"duplicate score dimension key: {key}")
        score_keys.add(key)

    interview_date = spec.get("interviewDate")
    if interview_date is not None:
        if not isinstance(interview_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", interview_date):
            fail(f"interviewDate must be YYYY-MM-DD, got {interview_date!r}")
        try:
            date.fromisoformat(interview_date)
        except ValueError:
            fail(f"interviewDate is not a real calendar date: {interview_date!r}")

    language = spec.get("language", "en")
    if not isinstance(language, str) or not LANGUAGE_TAG.fullmatch(language):
        fail(f"language must be a BCP 47 tag such as \"en\" or \"ru\", got {language!r}")

    instructions = spec.get("analysisInstructions", [])
    if not isinstance(instructions, list) or not all(
        isinstance(x, str) and x.strip() and "\n" not in x for x in instructions
    ):
        fail("analysisInstructions must be a list of non-empty single-line strings")

    validate_requirement_links(spec)
    validate_background(spec)
    validate_profile(spec.get("candidateProfile"), {str(q["index"]) for s in spec["sections"] for q in s["questions"]})
    validate_career(spec)


def validate_background(spec: dict[str, Any]) -> None:
    """Source availability survives drafting; preparation evidence also catches legacy omissions."""
    required = spec.get("candidateBackgroundRequired", False)
    if not isinstance(required, bool):
        fail("candidateBackgroundRequired must be a boolean")
    required = required or bool(spec.get("candidateFacts") or spec.get("candidateInsights") or spec.get("candidateCareer"))
    if required:
        profile = spec.get("candidateProfile")
        if not isinstance(profile, dict) or not isinstance(profile.get("portrait"), str) or not profile["portrait"].strip():
            fail("professional context requires candidateProfile with a non-empty factual portrait; "
                 "build Background from the supplied sources before generating")


def validate_profile(profile: Any, indices: set[str]) -> None:
    """Candidate background: a portrait and short sourced lists the interviewer reads mid-call."""
    if profile is None:
        return
    if not isinstance(profile, dict) or not isinstance(profile.get("portrait", ""), str):
        fail("candidateProfile must be an object whose portrait is a string")
    for key in PROFILE_LISTS:
        items = profile.get(key, [])
        if not isinstance(items, list) or len(items) > MAX_PROFILE_ITEMS:
            fail(f"candidateProfile.{key} must be a list of at most {MAX_PROFILE_ITEMS} entries")
        for item in items:
            if not isinstance(item, dict) or not all(
                isinstance(item.get(f), str) and item[f].strip() for f in ("text", "source")
            ):
                fail(f"every candidateProfile.{key} entry needs non-empty text and source")
            if "ask" in item and not (isinstance(item["ask"], str) and item["ask"].strip()):
                fail(f"candidateProfile.{key} ask must be a non-empty string when present")
            ref = QUESTION_REF.search(item.get("ask", ""))
            if ref and ref.group(1) not in indices:
                fail(f"candidateProfile.{key} ask ends in → {ref.group(1)}, which is no question index in the spec")
    validate_timeline(profile.get("timeline", []))
    validate_career_entries(profile.get("additionalExperience", []), "candidateProfile.additionalExperience", reason=True)
    if not profile.get("portrait", "").strip() and not any(profile.get(k) for k in (*PROFILE_LISTS, "timeline", "additionalExperience")):
        fail("candidateProfile is empty; omit the field instead")


def validate_career_entries(entries: Any, label: str, reason: bool = False) -> None:
    if not isinstance(entries, list):
        fail(f"{label} must be a list")
    for entry in entries:
        required = ("org", "source", "reason") if reason else ("org", "source")
        if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) and entry[k].strip() for k in required):
            fail(f"every {label} entry needs non-empty {', '.join(required)}")
        for key in ("role", "scale", "dateNote"):
            if key in entry and not (isinstance(entry[key], str) and entry[key].strip()):
                fail(f"{label}.{key} must be a non-empty string when present")
        for key in ("from", "to"):
            if key in entry and not (isinstance(entry[key], str) and
                                    (TIMELINE_DATE.fullmatch(entry[key]) or key == "to" and entry[key] == "now")):
                fail(f"{label}.{key} must be YYYY or YYYY-MM; only to may be now; omit unknown dates")
        if entry.get("from") and entry.get("to") not in (None, "now") and month(entry["to"], True) < month(entry["from"], False):
            fail(f"{label} {entry['org']!r} ends before it starts")


def validate_career(spec: dict[str, Any]) -> None:
    """Cover the full source inventory by identity; a summary or duplicate cannot stand in for a role."""
    if "candidateCareer" not in spec:
        if spec.get("candidateBackgroundRequired") or spec.get("candidateFacts") or spec.get("candidateInsights"):
            fail("candidateCareer inventory is required for professional context; extract all career entries "
                 "from the full sources, or use [] when no career entries are supplied")
        return
    inventory = spec["candidateCareer"]
    validate_career_entries(inventory, "candidateCareer")
    profile = spec.get("candidateProfile") or {}
    timeline = profile.get("timeline", [])
    validate_career_entries(timeline, "candidateProfile.timeline")
    for entry in timeline:
        if "to" not in entry or entry.get("dateNote"):
            fail("covered timeline entries need explicit source dates, including to; "
                 "keep unknown or qualified dates in additionalExperience")
    shown = [*timeline, *profile.get("additionalExperience", [])]
    expected = [tuple(row.get(k) for k in CAREER_IDENTITY) for row in inventory]
    actual = [tuple(row.get(k) for k in CAREER_IDENTITY) for row in shown]
    if len(set(expected)) != len(expected) or len(set(actual)) != len(actual):
        fail("career coverage contains duplicate entries; each source career identity must appear exactly once")
    if set(expected) != set(actual):
        missing = [str(inventory[i]["org"]) for i, key in enumerate(expected) if key not in actual]
        extra = [str(shown[i]["org"]) for i, key in enumerate(actual) if key not in expected]
        fail(f"career coverage mismatch: missing {missing}; unexpected or changed {extra}; "
             "cover every source entry in timeline or sourced additionalExperience with a reason")


def career_coverage_status(spec: dict[str, Any]) -> str:
    if "candidateCareer" not in spec:
        return "not checked: source inventory absent (legacy spec)"
    profile = spec.get("candidateProfile") or {}
    return (f"{len(spec['candidateCareer'])}/{len(spec['candidateCareer'])} source entries covered "
            f"({len(profile.get('timeline', []))} timeline, {len(profile.get('additionalExperience', []))} additional); "
            "source extraction completeness requires source review")


def month(value: str, end: bool) -> tuple[int, int]:
    """(year, month) of a YYYY or YYYY-MM date: a bare year starts in January and ends in December."""
    year, _, mon = value.partition("-")
    return int(year), int(mon) if mon else (12 if end else 1)


def validate_timeline(timeline: Any) -> None:
    if not isinstance(timeline, list) or len(timeline) > MAX_TIMELINE:
        fail(f"candidateProfile.timeline must be a list of at most {MAX_TIMELINE} entries")
    for entry in timeline:
        if not isinstance(entry, dict) or not (isinstance(entry.get("org"), str) and entry["org"].strip()):
            fail("every candidateProfile.timeline entry needs a non-empty org")
        start, end = entry.get("from"), entry.get("to", "now")
        if not (isinstance(start, str) and TIMELINE_DATE.fullmatch(start)) or not (
            end == "now" or isinstance(end, str) and TIMELINE_DATE.fullmatch(end)
        ):
            fail(f"candidateProfile.timeline {entry['org']!r}: from and to must be YYYY or YYYY-MM; to may be \"now\"")
        if end != "now" and month(end, True) < month(start, False):
            fail(f"candidateProfile.timeline {entry['org']!r} ends before it starts")
        if entry.get("kind", "job") not in ("job", "parallel"):
            fail(f"candidateProfile.timeline {entry['org']!r}: kind must be \"job\" or \"parallel\"")
        if any(f in entry and not isinstance(entry[f], str) for f in ("role", "scale")):
            fail(f"candidateProfile.timeline {entry['org']!r}: role and scale must be strings")


def validate_requirement_links(spec: dict[str, Any]) -> None:
    """Keep coverage links explicit; section links alone are not question evidence."""
    if "requirements" not in spec:
        return  # Legacy plans can carry section metadata without a matrix.
    requirements = spec["requirements"]
    if not isinstance(requirements, list):
        fail("requirements must be a list")
    ids: set[str] = set()
    for row in requirements:
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k].strip() for k in ("id", "text")):
            fail("each requirement needs non-empty id and text strings")
        if row["id"] in ids:
            fail(f"duplicate requirement id: {row['id']}")
        ids.add(row["id"])

    def links(item: dict[str, Any], label: str) -> set[str]:
        values = item.get("requirementIds", [])
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            fail(f"{label}: requirementIds must be a list of strings")
        if len(values) != len(set(values)) or set(values) - ids:
            fail(f"{label}: duplicate or unknown requirementIds")
        return set(values)

    for section in spec["sections"]:
        section_links = links(section, f"section {section['id']}")
        for question in section["questions"]:
            question_links = links(question, f"question {question['id']}")
            if "requirementIds" in section and question_links - section_links:
                fail(f"question {question['id']}: requirementIds must belong to its section")


def approved_plan_errors(spec: dict[str, Any], approved: Any) -> list[str]:
    """Skeleton differences between the spec and the approved plan; enrichment fields are not compared."""
    try:
        errors: list[str] = []
        for field in ("candidate", "role"):
            if approved.get(field) != spec[field]:
                errors.append(f"{field}: approved {approved.get(field)!r}, spec {spec[field]!r}")
        if approved.get("durationMinutes") != spec["durationMinutes"]:
            errors.append(f"durationMinutes: approved {approved.get('durationMinutes')!r}, spec {spec['durationMinutes']!r}")
        a_sections = {str(s["id"]): s for s in approved["sections"]}
        s_sections = {str(s["id"]): s for s in spec["sections"]}
        a_questions = {str(q["id"]): (sid, q) for sid, s in a_sections.items() for q in s["questions"]}
        s_questions = {str(q["id"]): (sid, q) for sid, s in s_sections.items() for q in s["questions"]}
    except (AttributeError, KeyError, TypeError):
        return ["approved plan is malformed: it needs sections with IDs and question lists"]
    for kind, a_items, s_items in (("section", a_sections, s_sections), ("question", a_questions, s_questions)):
        errors += [f"{kind} {key}: missing" for key in a_items if key not in s_items]
        errors += [f"{kind} {key}: not in the approved plan" for key in s_items if key not in a_items]
    if "requirements" in approved and approved["requirements"] != spec.get("requirements"):
        errors.append("requirements: approved matrix changed")
    shared = [sid for sid in a_sections if sid in s_sections]
    if shared != [sid for sid in s_sections if sid in a_sections]:
        errors.append(f"section order changed: approved {shared}, spec {[sid for sid in s_sections if sid in a_sections]}")
    for sid in shared:
        a_sec, s_sec = a_sections[sid], s_sections[sid]
        if "requirementIds" in a_sec and a_sec["requirementIds"] != s_sec.get("requirementIds"):
            errors.append(f"section {sid}: requirementIds changed")
        errors += [f"section {sid}: {f} changed" for f in APPROVED_SECTION_FIELDS
                   if a_sec.get(f) not in (None, "") and a_sec.get(f) != s_sec.get(f)]
        stayed = [str(q["id"]) for q in a_sec["questions"] if s_questions.get(str(q["id"]), ("",))[0] == sid]
        if stayed != [str(q["id"]) for q in s_sec["questions"] if str(q["id"]) in stayed]:
            errors.append(f"section {sid}: question order changed")
    for qid, (a_sid, a_q) in a_questions.items():
        if qid not in s_questions:
            continue
        s_sid, s_q = s_questions[qid]
        if "requirementIds" in a_q and a_q["requirementIds"] != s_q.get("requirementIds"):
            errors.append(f"question {qid}: requirementIds changed")
        if a_sid != s_sid:
            errors.append(f"question {qid}: moved {a_sid} -> {s_sid}")
        errors += [f"question {qid}: {f} changed" for f in APPROVED_QUESTION_FIELDS
                   if a_q.get(f) not in (None, "") and a_q.get(f) != s_q.get(f)]
    return errors


def approval_errors(approved: Any) -> list[str]:
    """The approved copy must carry the interviewer's own approving words; a bare draft copy proves no approval."""
    record = approved.get("approval") if isinstance(approved, dict) else None
    if not isinstance(record, dict):
        return ["no approval record"]
    errors = [f"approval.{key} must be a non-empty string" for key in ("by", "at", "quote")
              if not (isinstance(record.get(key), str) and record[key].strip())]
    if not errors:
        try:
            datetime.fromisoformat(record["at"])
        except ValueError:
            errors.append(f"approval.at must be an ISO-8601 datetime, got {record['at']!r}")
    return errors


def generation_stamp(value: str | None) -> str:
    """Local time with UTC offset, minute precision: 2026-10-11 14:32 +02:00."""
    if value is None:
        moment = datetime.now().astimezone()
    else:
        try:
            moment = datetime.fromisoformat(value)
        except ValueError:
            fail(f"--generated-at must be an ISO-8601 datetime, got {value!r}")
        if moment.tzinfo is None:
            fail(f"--generated-at needs a UTC offset, e.g. 2026-10-11T14:32:00+02:00, got {value!r}")
    offset = moment.strftime("%z")
    return f"{moment:%Y-%m-%d %H:%M} {offset[:3]}:{offset[3:5]}"


def skill_version(skill_md: Path) -> str:
    """metadata.version from the skill's own SKILL.md, so a stale installed copy stamps its own number."""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read skill version from {skill_md}: {exc}")
    match = re.search(r'^metadata:\n(?:[ \t]+.*\n)*?[ \t]+version:[ \t]*"?([^"\s]+)"?', text, flags=re.M)
    if not match:
        fail(f"{skill_md} has no metadata.version")
    return match.group(1)


def serialize_for_script(spec: dict[str, Any]) -> str:
    text = json.dumps(spec, ensure_ascii=False, separators=(",", ":"))
    # Prevent user-provided strings from breaking out of the script element.
    return (
        text.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--approved", required=True, type=Path,
                        help="approved plan JSON with an approval record; refuse to generate when it is missing or the spec's skeleton drifts from it")
    parser.add_argument(
        "--generated-at",
        default=None,
        help="ISO-8601 datetime with UTC offset to stamp instead of now, for reproducible output",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    template_path = args.template or (root / "assets" / "interview-helper-template.html")
    if not template_path.exists():
        fail(f"template not found: {template_path}")
    if not args.spec.exists():
        fail(f"spec not found: {args.spec}")

    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON spec: {exc}")
    if not isinstance(spec, dict):
        fail("spec root must be a JSON object")
    validate_spec(spec)
    try:
        approved = json.loads(args.approved.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(f"cannot read approved plan {args.approved}: {exc}")
    unapproved = approval_errors(approved)
    if unapproved:
        fail("approved plan lacks evidence of the interviewer's approval; get explicit chat approval, then add "
             "approval {by, at, quote} with their words verbatim:\n- " + "\n- ".join(unapproved))
    drift = approved_plan_errors(spec, approved)
    if drift:
        fail("spec drifts from the approved plan; fix the spec, not the approved copy:\n- " + "\n- ".join(drift))
    stamp = f"{generation_stamp(args.generated_at)} · skill {skill_version(root / 'SKILL.md')}"

    template = template_path.read_text(encoding="utf-8")
    marker = "__INTERVIEW_CONFIG_JSON__"
    if template.count(marker) != 1:
        fail(f"template must contain exactly one {marker} marker")
    stamp_marker = "__GENERATED_AT__"
    if template.count(stamp_marker) != 1:
        fail(f"template must contain exactly one {stamp_marker} marker")
    # Stamp first, so spec text that happens to contain the stamp marker stays untouched.
    language = spec.get("language", "en")
    lang_attr = '<html lang="en">'
    if template.count(lang_attr) != 1:
        fail(f"template must contain exactly one {lang_attr}")
    html = template.replace(lang_attr, f'<html lang="{language}">', 1)
    html = html.replace(stamp_marker, stamp).replace(marker, serialize_for_script(spec))

    if untranslated_cyrillic(spec):
        fail("generated HTML contains Cyrillic characters outside the candidate name; translate descriptive spec content to English "
             "or set the spec language")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(args.output)
    print("Background: " + ("present" if spec.get("candidateProfile") else "not required"))
    print("Career coverage: " + career_coverage_status(spec))
    record = approved["approval"]
    print(f"Approved plan: checked; approved by {record['by']} at {record['at']}: \"{record['quote']}\"")
    print("Visible rendering: not checked by generator")


if __name__ == "__main__":
    main()
