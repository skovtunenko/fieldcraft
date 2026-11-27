#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Validate the generated standalone interview helper HTML."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from generate_interview_helper import career_coverage_status, untranslated_cyrillic, validate_spec


def validate_embedded_spec(text: str) -> list[str]:
    """Validate data bound to the live renderer, not a candidate name elsewhere in the page."""
    match = re.search(r"\bconst CONFIG\s*=\s*", text)
    if not match:
        return ["embedded interview CONFIG is missing"]
    try:
        spec, end = json.JSONDecoder().raw_decode(text[match.end():])
        if not text[match.end() + end:].lstrip().startswith(";") or not isinstance(spec, dict):
            return ["embedded interview CONFIG must be a JSON object followed by a semicolon"]
        validate_spec(spec)
        if untranslated_cyrillic(spec):
            return ["Cyrillic text found outside the candidate name; translate English-page descriptive content"]
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return [f"invalid embedded interview CONFIG: {exc}"]
    except SystemExit as exc:
        return [str(exc)]
    return []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    path = args.html
    if not path.exists():
        raise SystemExit(f"ERROR: file not found: {path}")
    text = path.read_text(encoding="utf-8")
    errors = validate_embedded_spec(text)

    required = {
        'localStorage': 'LocalStorage persistence is missing',
        'Positive signals': 'positive signal UI is missing',
        'Negative signals': 'negative signal UI is missing',
        'Done + collapse': 'Done + collapse control is missing',
        'class="btn small skip-question"': 'question Skip control is missing',
        'class="btn small skip-section"': 'section Skip control is missing',
        'id="requirementCoverage"': 'role coverage panel is missing',
        'function requirementCoverage(': 'role coverage calculation is missing',
        'id="openReqList"': 'Still open requirement list is missing',
        'id="paceRail"': 'pace rail is missing',
        'data-view-btn="noverdict"': 'question status filter is missing',
        'class="probe-cues"': 'follow-up probe cues are missing',
        'skipped by interviewer; not assessed by this question': 'skipped-question prompt status is missing',
        'Expand all sections': 'topbar expand-all-sections control is missing',
        'Collapse all sections': 'topbar collapse-all-sections control is missing',
        'Generate analysis prompt': 'final prompt generator is missing',
        'id="transcriptInput"': 'optional transcript field is missing',
        'function xml(': 'prompt XML escaping is missing',
        'function touched(': 'touched-question filtering is missing',
        'function sectionTouched(': 'untouched-section filtering is missing',
        'Save HTML With Comments': 'save-HTML backup button is missing',
        'id="embeddedState"': 'embedded-state element is missing',
        'function saveHtml(': 'save-HTML with embedded notes is missing',
        'showSaveFilePicker': 'File System Access save path is missing',
        'data-scale-key': 'follow-up and positive-signal rating scale markup is missing',
        'id="previousFeedback"': 'previous-interviewer-feedback field is missing',
        'id="i-partial"': 'rating-scale icons are missing',
        'data-reasons-for': 'reason-chip markup is missing',
        'data-time-key': 'mark timestamp markup is missing',
        'function stampNow(': 'mark timestamping is missing',
        "'redflag'": 'red-flag overall signal is missing',
        'aria-disabled': 'Done gating on an overall signal is missing',
        'id="flagMoment"': 'flag-moment control is missing',
        'id="timerEndAt"': 'local end-time correction field is missing',
        'function setTimerEnd(': 'end-time correction handler is missing',
        'section-skipped-count': 'live section skipped total is missing',
        '.timer-box.ended': 'stopped-timer style is missing',
        'function highlightSyntax(': 'offline Markdown/XML highlighting is missing',
        'id="finalNotesPreview"': 'final-notes syntax preview is missing',
        'id="previousFeedbackPreview"': 'feedback syntax preview is missing',
        'id="transcriptInputPreview"': 'transcript syntax preview is missing',
        'id="promptOutputPreview"': 'analysis-prompt syntax preview is missing',
        'id="candidateProfile"': 'candidate insights block is missing',
        'id="prepPeek"': 'candidate-background overlay is missing',
        'id="openPrep"': 'header Background button is missing',
    }
    for needle, msg in required.items():
        if needle not in text:
            errors.append(msg)

    lang = re.search(r'<html lang="([A-Za-z0-9-]+)"', text)
    if not lang:
        errors.append("document language is missing")

    forbidden_patterns = [
        (r'<script\b[^>]*\bsrc\s*=', 'external script dependency found'),
        (r'<link\b[^>]*\brel\s*=\s*["\']?stylesheet', 'external stylesheet dependency found'),
        (r'\bfetch\s*\(', 'network fetch call found'),
        (r'XMLHttpRequest', 'XMLHttpRequest network call found'),
        (r'new\s+WebSocket\s*\(', 'WebSocket network call found'),
        (r'@import\s+url\s*\(', 'CSS import found'),
    ]
    for pattern, msg in forbidden_patterns:
        if re.search(pattern, text, flags=re.I):
            errors.append(msg)

    if '__INTERVIEW_CONFIG_JSON__' in text:
        errors.append('template configuration marker was not replaced')
    if '__GENERATED_AT__' in text:
        errors.append('generation stamp marker was not replaced')
    elif not re.search(r'Generated \d{4}-\d{2}-\d{2} \d{2}:\d{2} [+-]\d{2}:\d{2}', text):
        errors.append('generation stamp is missing')
    elif not re.search(r'Generated \d{4}-\d{2}-\d{2} \d{2}:\d{2} [+-]\d{2}:\d{2} · skill \d', text):
        errors.append('generation stamp has no skill version; regenerate the page with the current skill')

    scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', text, flags=re.I | re.S)
    if not scripts:
        errors.append('embedded JavaScript not found')
    elif shutil.which('node'):
        js = '\n'.join(scripts)
        with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as tmp:
            tmp.write(js)
            tmp_path = tmp.name
        try:
            proc = subprocess.run(['node', '--check', tmp_path], text=True, capture_output=True)
            if proc.returncode != 0:
                errors.append('embedded JavaScript failed syntax check: ' + (proc.stderr.strip() or proc.stdout.strip()))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    if errors:
        print('VALIDATION FAILED')
        for error in errors:
            print('- ' + error)
        raise SystemExit(1)

    print(f'VALID: {path}')
    spec, _ = json.JSONDecoder().raw_decode(text[re.search(r"\bconst CONFIG\s*=\s*", text).end():])
    print('Background data: ' + ('present' if spec.get('candidateProfile') else 'not required'))
    print('Career coverage: ' + career_coverage_status(spec))
    print('Static HTML: checked')
    print('JavaScript syntax: ' + ('checked' if shutil.which('node') else 'not checked: Node unavailable'))
    print('Approved plan: not checked by HTML validator; use generator --approved')
    print('Visible rendering: not checked; requires a browser check')


if __name__ == '__main__':
    main()
