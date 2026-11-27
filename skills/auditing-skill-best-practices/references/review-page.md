# Review page

Read this for every audit: it defines the one model-authored findings JSON
and the local report/page rendering interface. The page is one
offline HTML file built by `scripts/render_review_page.py` from
`assets/review-page-template.html` and the findings JSON below. The reviewer
marks each failure accept, reject, or edit, adds comments, and exports the
accepted and edited fixes as a plain-text instruction for an agent, ending
with a step to summarize applied/skipped/conflicting fixes, offer a re-audit,
and stop to wait for the user's reply. Another
audit or mechanical checker run requires a separate explicit user request. A rejected fix with a comment goes in as the
reviewer's reason not to apply it, and one without a comment as rejected
with no reason given. A comment on an undecided fix goes in as
a question: the agent answers it before the completion summary and leaves that fix
alone; an export of questions only changes no files and skips the re-audit.

## Contents

- [Findings JSON](#findings-json)
- [Render](#render)
- [Review controls](#review-controls)

## Findings JSON

Write exactly this shape (schema 1). The script rejects unknown fields and
names every problem with its JSON path.

```json
{
  "schema": 1,
  "lang": "en",
  "target": "/home/ana/skills/filling-pdf-forms",
  "snapshot": "2026-10-18",
  "audited": "2026-10-19",
  "hosts": "all (assumed: nothing states a host)",
  "auditor": "Opus 5.5 in Claude Code",
  "rules": [
    {
      "id": "BP-15",
      "status": "fail",
      "evidence": "SKILL.md:3 \"I can help you fill PDF forms\""
    }
  ],
  "failures": [
    {
      "rule": "BP-15",
      "location": "SKILL.md:3",
      "why": "Descriptions are injected into the system prompt; first or second person confuses skill discovery.",
      "evidence": "The description opens with \"I can help you fill PDF forms\".",
      "before": "I can help you fill PDF forms.",
      "after": "Fills PDF forms and checks field mappings. Use when the user mentions PDF forms."
    },
    {
      "rule": "BP-11",
      "location": "SKILL.md:3",
      "why": "Claude decides when to load a skill from its description; without a when-clause it triggers late or never.",
      "evidence": "No \"Use when ...\" clause.",
      "fix_ref": "BP-15"
    },
    {
      "rule": "BP-55",
      "location": "SKILL.md:15",
      "why": "Without the server prefix Claude may not find the tool when several MCP servers are connected.",
      "evidence": "\"call the create_issue tool\" names the tool bare.",
      "before": "call the create_issue tool",
      "after": "call the <server>:create_issue tool",
      "fix": "Replace <server> with the MCP server that provides create_issue, such as GitHub.",
      "placeholders": ["<server>"]
    }
  ]
}
```

The example shortens `rules` to one entry; a real file lists every rule you
judged, BP-11 and BP-55 included. The report command's `--mechanical` flag
adds the rules the checker decided, so the saved file holds every rule of
both catalogues.

- `lang`: the conversation's language code, such as `en` or `de`. The page
  sets it as its HTML language. Every text field below is in the
  conversation language, except quoted evidence and Before text, which stay
  verbatim.
- `labels`: optional, the page and report labels in the conversation
  language. The labels are English by default; `assets/labels.json` holds
  them as `{"page": {key: text}, "report": {key: text}}`. When `lang` is not
  `en`, read that file and write `labels` with the same two parts and your
  translation of each value. Keep each `{n}`, `{m}`, `{s}`, `{t}`, and `{v}`
  token of a value; the script refuses an unknown part or key, a value that
  is not a non-empty string, and a changed token set. A key you leave out
  stays English. Leave out the `must`, `should`, `consider`, and `na` keys:
  rule IDs, the ✅, ❌, and n/a markers, and the level words stay as they are.
- `target`: the audited skill's absolute path. `snapshot`: the article
  catalogue's snapshot date. `audited`: today's date. `hosts`: the report
  header's Hosts value.
- `auditor`: the model and harness running this audit, as your own context
  names them, such as `Opus 5.5 in Claude Code`; write `unknown` for a part
  you cannot tell. The page header shows it beside the audit date, so a
  reviewer can compare audits by different models.
- `rules`: one entry per rule you judged: `id`,
  `status` (`pass`, `fail`, or `n/a`), `evidence` (the shortest `file:line`
  or quote that supports the status, or the n/a reason). Add `source` only when the rule has
  several Source links and one other than the first fits the evidence
  better; it must be one of them. The script fills title, level, type, and
  the default source from the catalogues, so do not write them. With
  `--mechanical` it adds each mechanical rule with the checker's status and
  each `not_applicable` rule as n/a with its reason, in catalogue order. An
  entry of yours for a mechanical rule must carry the checker's status; an
  entry of yours for a `not_applicable` rule replaces the checker's n/a. It
  refuses a rule still missing after that, an unknown rule, and a `source`
  outside the rule's Source links.
- `failures`: one entry per ❌ finding. The renderer groups entries by catalogue and
  level; keep related entries together. `rule`
  names a rule whose status is `fail`, and every such rule has at least one
  entry. `location`: `file:line`, a range, or the file alone; for absent material,
  the searched folder (`./` for the target root). `why`: the catalogue's Why
  line in the conversation language, or the rule's purpose when none is given.
  `evidence`: the decisive quote, count, or file:line. The fix takes one
  of these forms, with the following rules:
  - text edit: `before` (the shortest exact excerpt copied verbatim, a phrase or at most
    three lines)
    and `after` (its replacement); `fix` may add a one-line note;
  - large edit: `range` (the exact line range, such as `SKILL.md:21-520`) and
    `fix` (the step for those lines), plus `before` and `after` for the first
    changed span when that helps;
  - structural fix: `fix` alone, as one concrete step;
  - shared edit: `fix_ref`, the rule ID of the entry that holds the edit,
    and no other fix field. That rule must have exactly one entry with its
    own fix. The page links to that entry, and the export
    applies the edit once and lists every rule it resolves.
- `reviewer_reason`: optional, beside any fix form, `fix_ref` included: the
  reason the export gave for rejecting this failure, verbatim, or "No reason
  given" in the conversation language when it gave none. The page starts the
  card rejected with that reason and keeps Accept and Edit on, so the
  reviewer can switch the decision; the fix is still required.
- `fix_location`: optional, the file and line to edit when it differs from
  `location`.
- `placeholders`: optional, every `<placeholder>` in `after` or `fix` that
  the reviewer must fill in. The page highlights them and keeps Accept off
  until the current draft or saved revision has filled them all.

Every fix must stand alone. If one fix works only with another (for example a
name change and matching folder rename), combine the changes under one owner
and use `fix_ref` elsewhere. Propose fixes satisfying every rule. A large edit
uses its exact range and a concrete step, not a full rewritten file. Never
repeat a long value when its shortest changed span is enough.

- `not_evaluated`: optional list of `{"rule": "BP-22", "reason": "..."}`,
  required when evidence could not be evaluated; `--mechanical` adds the
  checker's own entries. Each ID appears once with a
  combined reason and has status `n/a` or a confirmed `fail`. Do not include
  genuine applicability n/a here. This distinguishes missing evidence from
  rules that do not apply without changing old schema-1 findings files.

## Render

Invoke the report command directly; it calls its HTML helper internally. The
[bundled-script execution boundary](../SKILL.md#bundled-script-execution-boundary)
and the interpreter fallback in SKILL.md's Rules apply.

```bash
uv run --script <skill>/scripts/render_report.py --new "<target>"
uv run --script <skill>/scripts/render_report.py "<findings path>" [<report path.md>] [--page] [--mechanical]
```

Run `--new` once per audit or page request. It allocates an exclusive empty
`$TMPDIR/skill-audit-<target folder>-<YYYYMMDD-HHMMSS>.json` and prints only
its path. Write the findings JSON there; for a page-only request with
a saved current snapshot, copy that file locally to the new path instead of
rewriting its content with the model. Never write findings into the target
or this skill's directory.

Run the second command to validate JSON and write the complete Markdown
report. Add `--mechanical` for every audit, and omit it for a page-only
request, whose copied findings are already complete: it reruns the checker on
`target`, completes `rules`, and saves the completed findings file. A failing
mechanical rule still needs your failure entry. Add `--page` only when
requested; it delegates HTML generation to the
existing renderer. Defaults use `$TMPDIR` with the findings stem and `.md` /
`.html`. For a requested destination folder, join it with the findings file
name, replacing `.json` with `.md`, and pass that full path. Output paths
inside the audited skill or this skill, including through symlinks, are refused.

A successful render also saves a Git inventory snapshot beside the findings as
`<findings stem>.scope.json` for the same-conversation stale-scope command.
Keep it with the findings; the renderer preserves an existing baseline.
If Git or snapshot capture is unavailable, the audit still renders and a later
re-audit uses full reading. The baseline stays on disk with the prior findings.

Exit 0 prints one compact JSON object with `counts` (article/other, each with
pass/fail/n/a), `findings`, `report`, and optional `page` absolute paths. It
never prints report or page bodies. Exit 2 names input/path problems on stderr;
fix the named JSON fields and retry. For a refused destination, request a path
outside both protected directories.
For an unexpected script/internal failure, report the command, exit code, and
diagnostic and stop rendering. Do not read or repair implementation unless the
user separately requests maintenance of this auditor.

Use this stdout to return counts and artifact links. Do not `cat` the generated
report/page, load it through a file-reading tool, or copy/rewrite it in chat.
Read it only on an explicit request for its content or to investigate a rendering
error, limited to the necessary output portion; this does not authorize reading
script bodies or template source. The report and the page show the
`labels` of the findings JSON, and English for every label it does not give.
Report content comes from JSON; titles/levels/types/default sources and counts
come from code and catalogues. The Markdown report preserves rejected reasons
instead of showing their fixes; JSON/HTML retain those fixes for reconsideration.

## Review controls

Clicking a card or group header toggles its contents; source links and buttons
keep their own actions. Header badges show each card's decision and the group's
common decision or review progress. Accepted, rejected, edited, and undecided
cards keep distinct colours, including on hover.

Edit opens a draft in After for a simple text edit, or a Change editor for a
range or structural fix. A draft leaves the saved decision and instruction
unchanged. Save change stores the revision as edited; Cancel restores the saved
state. Accept commits a valid draft or accepts the saved revision, retaining its
text and comments. A hand-edited instruction stays intact until Rebuild.

Placeholder fields stay inside the surrounding code. They support Enter and
multiline paste, fit the placeholder or current text, and shrink on deletion.
Width stops at the column; height stops at 240 px. Longer lines scroll
horizontally and additional lines vertically. Saving a placeholder replacement
updates After and the fix's note together. Empty text or remaining placeholders
keep Save and Accept unavailable.
