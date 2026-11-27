# auditing-skill-best-practices eval cases

**Mechanical** cases are scripted in `scripts/test_check_mechanical.py`,
`scripts/test_render_review_page.py`, and `scripts/test_render_report.py` (`uv run --script build/**/auditing-skill-best-practices/evals/scripts/<name>.py`
from the repository root). **Behavioral** cases give the prompt to a fresh agent that has only
this skill loaded and grade the transcript and the filesystem.

Fixtures keep their skill file as `SKILL.md.fixture` so the repository's own
skill checks do not treat them as skills. Behavioral runs copy a fixture to a
temp dir and rename that file to `SKILL.md` first.

- `fixtures/compliant/` (`filling-pdf-forms`): passes every rule; has no
  `metadata.version` and no `agents/openai.yaml`. Copy it into a folder named
  `filling-pdf-forms`, or OS-02 fails.
- `fixtures/violating/` (`Claude_Helper`): fails 12 mechanical rules (9 BP,
  3 OS) once a copy's `references/basics.md` gets one appended line (line
  123) with a Markdown link to the missing `form-rules.md`, the `BROKEN_LINK`
  line in `scripts/test_check_mechanical.py`. The tests append it, and
  behavioral runs append it too; the committed fixture holds no broken link,
  so the repository's own link check stays clean and several judgment rules (line numbers below are in the renamed
  `SKILL.md`).
- `fixtures/assets-leak/preview.html`: an output template whose script beacons
  the filled form fields to an unnamed host; B24 copies it into the compliant
  fixture's `assets/`.
- `fixtures/review/findings-violating.json`: a findings JSON for the review
  page, with `</script>` and `<!--` in evidence, text-edit and structural
  fixes.

## Mechanical

| ID | Setup | Pass when |
| --- | --- | --- |
| M1 | checker on `compliant` | BP-22, OS-06, OS-08 n/a, every other mechanical rule pass |
| M2 | checker on `violating` | fail: BP-05, BP-07, BP-09, BP-10, BP-17, BP-21 (`references/doc2.md`), BP-22 (`references/basics.md`), BP-39 (`scripts/unused_helper.py`), BP-40 (`SKILL.md:15`), OS-02 (`SKILL.md:2`), OS-03 (`SKILL.md:3`, a colon and a space in a plain value), OS-11 (`references/basics.md:123`); pass: BP-04, BP-06, BP-08, OS-01, OS-04; every finding has a fix |
| M3 | generated edge-case skills | 65-char name fails BP-04; tag in name fails BP-05 and BP-06; `claudette-tools` fails BP-07; missing description: BP-08 fail, BP-09/BP-10 n/a; no frontmatter: BP-04 fail; folded description over and under 1024 handled; quoted scalars unquoted; regex escapes are not paths; `C:` path fails BP-40 and the finding shows the whole path as written; BP-05 rename suggestion drops reserved words |
| M4 | missing path, dir without `SKILL.md`, no argument | exit 2 and stderr names the problem |
| M5 | digest of each fixture copy before and after the run | unchanged; stderr empty, stdout is JSON only |
| M6 | catalogues vs script | BP and OS IDs unique and contiguous, each with one type and level; OS rules number 12 to 18, each with Hosts, Source links, and Why; Snapshot counts and mechanical lists match the rules; script rule IDs equal the mechanical IDs of both catalogues |
| M7 | checker on this skill | every mechanical rule of both catalogues pass or n/a |
| M8 | `scripts/headings.py` on Markdown with a ``` fence nested in a ```` fence, a tilde fence, and H5 | prints only the three real H2–H4 headings; unreadable file exits 2 |
| M9 | generated skill with `scripts\run.rb`, `templates\form`, `assets\t.xml`, regex text, and a registry key | BP-40 reports exactly the three paths, as written; regex escapes and `HKEY_LOCAL_MACHINE\Software` pass |
| M10 | Latin-1 reference over 100 lines with a `C:` path, a binary PNG, then an unlistable folder | Latin-1 file listed in `unreadable`; BP-22 and BP-40 n/a with `not_evaluated`, never a silent pass; PNG not listed; unlistable folder marks BP-21, BP-39, BP-40, OS-11 not evaluated |
| M11 | `references/schema.json` linked, then unlinked | a non-Markdown reference counts for BP-21 |
| M12 | generated YAML and text edge cases | `name: "abc\n"` fails BP-05; `name: 'abc' # c` passes; `x <= 5 and y >= 3` passes BP-10; a literal block of 1024 chars fails BP-09 (clip keeps the final newline), the strip form passes; `>` of 1023 passes, 1024 fails; a long `.txt` reference needs a contents line (BP-22) |
| M13 | a symlinked `references/` folder and a symlink back to the root | the linked folder is walked once, the cycle stops, BP-21 reports its file |
| M14 | traceability | every BP rule has a Source line whose anchors equal the Anchor column of its Section headings, in order; rules under "Solve, don't defer" link `#solve-dont-punt`; BP-18 cites Progressive disclosure patterns; `article-headings.md` has 48 anchored rows, and outside the checklist rows (44–47) every listed rule cites that heading |
| M15 | generated names and folders | OS-01 fails `-pdf-tools`, `pdf-tools-`, `pdf--tools`; OS-02 fails a name that differs from its folder and is n/a at a plugin root |
| M16 | generated frontmatter (agreement with PyYAML checked on 371 local skills) | OS-03 fails a colon and a space, or a trailing `:`, in a plain value, a backtick start, an unclosed quote, text after a quote, a bare line, a tab, a duplicate key, a block after a blank line or a BOM; passes quoted and folded colons, comments, URLs, indentless lists; n/a with no block |
| M17 | generated keys, `metadata`, `compatibility` | OS-04 flags `allowed_tools` and a top-level `version` only; OS-06 fails float, `yes`, date, nested, scalar, list values and a 501-character or numeric `compatibility`; flow-style `metadata` is not evaluated |
| M18 | `description` + `when_to_use` | OS-08 fails at 1,537 characters, passes at 1,536 |
| M19 | links | OS-11 flags a missing file and a link out of the skill; skips URLs, pure anchors, fenced and inline code |
| M20 | `headings.py --ids` on HTML | prints only slug ids of h2–h4, skipping generated ids |
| M21 | `headings.py` on a fence indented 4 spaces and one indented 3 | the 4-space line is text, the 3-space one opens a fence (CommonMark) |
| M22 | links an angle-bracket link to `references/my guide.md`, `[x][ref]` to a missing file, a footnote, a link through a symlink out, a skill root that is a symlink | OS-11 passes the spaced path, flags the missing reference-style target and the symlink out, skips the footnote, and audits a symlinked root like the real one |
| M23 | `metadata:` with `version: "0.3` unclosed, and a nested quote closed on the next line | OS-03 fails the unclosed quote at its line, passes the closed one |
| M24 | `"name": pdf-tools` and `'description': …` | BP-04, BP-05, BP-09, OS-02, OS-03 all pass: quoted keys name the same fields |
| R1 | `render_review_page.py` on the sample | exit 0, prints the path; embedded JSON has no raw `<` and round-trips exactly, `</script>` and `<!--` included; audit id is target, snapshot, and audit date |
| R2 | broken findings JSON, invalid JSON | exit 2; every problem named with its JSON path; nothing written |
| R3 | page path inside the audited skill, through a symlink to it, inside this skill, without `.html`, in a missing folder | exit 2 with the reason; nothing written |
| R4 | `lang` `ru` with Russian `labels` (test data), `de` without `labels`; zero failures; no page path | all render; the default goes to `$TMPDIR/<findings file name>.html`; the page embeds the English page labels of `assets/labels.json` and the findings' `labels` on top, and sets `<html lang>` from `lang`; the template holds no language table, uses no `innerHTML`, and loads nothing from the network; no file under `skills/**/auditing-skill-best-practices/` holds Cyrillic text |
| R16 | `labels` with an unknown part, an unknown key, a number, an empty string, and a value that drops `{m}`; `labels` as a list | exit 2, each problem named with its JSON path (`labels.page.<key>`), nothing written; a key the findings leave out stays English in the page and the report; the same `labels` reach both the Markdown report and the page |
| R5 | wrong JSON types (an object id, a list rule, a numeric fix, a list before, a string notes); broken `fix_ref`, `fix_ref` with `before`, a placeholder absent from After, `range` without `fix`, empty `fix_location`; `reviewer_reason` empty or with no fix | exit 2, every problem named with its JSON path, no traceback; a failure with `reviewer_reason` beside a fix and beside `fix_ref` renders |
| R6 | the sample findings, then the same findings reversed | the two pages get different `audit_id` values, so saved marks do not carry over |
| R7 | in a browser: Edit on a fix with `range`, change the text, export | the box edits the Change step; the export holds the edited Change and no first-span Before/After |
| R8 | findings with a `title` on a rule, a foreign source, `BP-99` in place of `BP-02`, and a second own fix for the rule a `fix_ref` names | exit 2 naming each problem (`title` as an unknown field); the export text tells the agent to skip a fix whose Before is not found exactly once |
| R9 | the sample page at 1440px and 375px: accept one fix, reject one, reload | approved interview-helper styling; the sidebar row and card show each decision; the instruction preview updates live and lists the accepted fix only; decisions survive reload; no horizontal scroll at 375px; the page names its generation time and skill version, and its header names the auditor |
| R10 | `test_review_page_browser.py`, headless Chrome on the sample page (run outside an agent sandbox: Chrome needs its profile socket) | accept BP-07, edit and save BP-15's Change with a comment, a second BP-55 failure at `references/api.md:40` shows each location in both BP-55 titles and none in BP-07's; an OS-15 failure at `SKILL.md:15` sharing BP-15's edit makes the export read `Resolves: BP-15, OS-03, OS-15 (SKILL.md:15)`; the footer Fold button folds BP-07, and it stays folded after a reload; Collapse all and Expand all each survive a reload; a sidebar click unfolds BP-07 and that survives a reload; the sidebar lists BP-05 indented under BP-07 and OS-03, OS-15 under BP-15, and BP-07's toggle hides BP-05 across a reload; accepted, rejected, and open cards have three different backgrounds; rejecting OS-15 inside BP-15's card with a reason drops it from Resolves and lists it as rejected, across a reload; accepting BP-21 and then rejecting it switches the mark directly; a second page whose BP-43 has `reviewer_reason` beside its fix shows that card rejected with the reason as its comment, Accept and Edit on, exports it as rejected, and stops without an automatic audit; Accept switches it straight to a fix to apply without the old reason; its Reset confirmation says earlier rejections stay, a first-round page's does not; un-rejecting drops it, Reset review restores it; Reset review keeps everything on cancel and clears decisions, comments, folds, sidebar groups, and the instruction on confirm, across a reload; after the reset a comment on undecided BP-26 exports as a question (count 1, Proposed After, do-not-apply lead) and the export ends with a change-no-files step, and accepting BP-07 asks for answers before the completion summary and then stops; un-rejecting the `reviewer_reason` BP-43 drops it and does not turn it into a question; reject BP-43 with a comment and BP-21 without: the live instruction lists BP-07 and BP-15, BP-43 as rejected with its reason and BP-21 as rejected with `Reviewer reason: none given`, not BP-26, ends with the completion summary and stop instruction, with no automatic audit; all of it survives a reload; a hand-edited instruction survives accepting BP-26 and a reload, Rebuild restores the built one; no console error. Exit 2, never a pass, when no browser runs |
| R11 | `--new <tmp>/violating` twice in one second | two different empty files, `skill-audit-violating-<YYYYMMDD-HHMMSS>.json` and the same with `-2`; each prints its path |
| R12 | `auditor` set to `Opus 5.5 in Claude Code $&`, absent, and blank | set: round-trips and the header facts show `Auditor: Opus 5.5 in Claude Code $&` below Audited, visible without scrolling at 1440×900; absent: renders without the Auditor row; blank: exit 2 naming `auditor`, nothing written |
| R13 | `node build/**/auditing-skill-best-practices/evals/scripts/test_review_page_logic.cjs`; render through the canonical renderer | opening Edit and typing leave the saved decision and export unchanged; invalid placeholders block Save/Accept; Save updates After, its note, and export; Cancel preserves all decision states; Accept works with a valid draft, a saved revision, or a previously rejected revision and retains the saved text |
| R14 | the generated inline editor handler with deterministic font and geometry stubs | compact placeholder width; width follows the longest current line and shrinks on deletion, never exceeds the column; Enter and multiline paste round-trip through Save/Accept/reopen; prefix, textarea, suffix stay in one text flow; height stops at 240 px and shrinks; horizontal overflow is enabled with wrapping off; these checks do not certify browser layout |
| R15 | generated header handlers and group status logic | header text toggles open and closed, links and controls do not trigger a second toggle; badges show unreviewed, accepted, rejected, edited, or mixed progress |

## Behavioral

For audit cases, **report** means the script-generated Markdown artifact, not
model-authored chat prose. Every audit writes a full findings JSON, even without
`page`. Chat contains only per-catalogue counts, artifact links, and the page
offer when applicable. A page-only follow-up returns the new page link alone.
Full rule coverage, evidence, fixes, rejection reasons, and report language
expectations are checked in JSON and rendered artifacts. Refresh cases keep
their own drift-report behavior. These are cases to execute, not recorded passes.

| ID | Prompt / setup | Pass when |
| --- | --- | --- |
| B1 | `/auditing-skill-best-practices <tmp>/violating` | two sections, article rules and other official sources, each with its own counts in the header; header states hosts `all` (assumed); mechanical ❌ match M2 exactly; no All rules table and no ✅ or n/a rule listed; the last line offers the review page via `page`; ❌ with evidence for BP-13 (`Claude_Helper` says nothing about the job), BP-52 (`references/doc2.md`), BP-01 (`SKILL.md:8-9`, explains what a PDF is), BP-11 (no "when" clause), BP-15 ("I can help you"), BP-16 (generic words only), BP-53 (500-line inline API reference; BP-18 is ❌ only for its own defect, the cue-less basics link), BP-50 (`uv` shebang runner never named in SKILL.md), BP-26 (`SKILL.md:11`, "Before August 2025"), BP-32 (no evaluation material, location `./`) and no other evaluation rule in chat, BP-41 (`SKILL.md:13`, four PDF libraries, no default), BP-42 (`scripts/fill_form.py` opens a file unguarded), BP-43 (`TIMEOUT = 47`), BP-55 (`SKILL.md:15`, bare `create_issue`), BP-46 (`SKILL.md:15` says fill, `scripts/fill_form.py` only prints), BP-25 (the filled form is filed with no check), OS-15 (`SKILL.md:15` files to a tracker the description never mentions); must failures listed before should, should before consider; the reply holds only counts and artifact links (no progress checklist or copied report); BP-05 fix proposes a name that passes BP-05, BP-07, and BP-13; no defect reported under two rules; with `page` (B5, B13), the findings JSON has BP-03, BP-33 to BP-38, and BP-54 n/a citing BP-32, BP-14 n/a (fewer than two valid siblings), and BP-18 ✅ citing BP-53 unless the cue-less link fails it |
| B2 | `/auditing-skill-best-practices <tmp>/filling-pdf-forms page` (the compliant fixture) | header shows ❌ 0 in both sections and its counts cover every catalogue rule; "No failures." in both sections, no closing `page` offer; the findings JSON lists every catalogue rule; BP-14 n/a (fewer than two valid siblings); BP-51 n/a (standard library only); BP-24 n/a (two steps, no gate); BP-37 n/a (nothing shows the skill is shared), with the reason in Evidence and no not-evaluated entry; no finding mentions `metadata.version` or `agents/openai.yaml` |
| B3 | `/auditing-skill-best-practices` with no path | asks which skill to audit; runs nothing |
| B4 | `/auditing-skill-best-practices <tmp>/empty` (no `SKILL.md`) | says no skill was found, naming the path; no report |
| B5 | B1 prompt in a Russian conversation, then `page` as the next message | headings and prose in Russian, including the closing `page` offer; the reply to `page` is the page path line alone, and the page's verdicts match the report's counts; the findings JSON has `lang: ru` and `labels` translated into Russian from `assets/labels.json` with every `{token}` kept, so the report and the page show Russian labels; rule IDs, rule titles, ✅, ❌, n/a, level and type values, and quotes unchanged |
| B5a | B5 in a Ukrainian conversation | as B5, in Ukrainian: `lang: uk` and Ukrainian `labels` |
| B5b | B5 in an English conversation | as B5, in English: `lang: en`, no `labels`, and the report and page show the English labels of `assets/labels.json` |
| B6 | `/auditing-skill-best-practices refresh` with network | runs `scripts/source_hashes.py` first; with every source unchanged it stops there: the title and zero count lines, plus a translated "No drift since <snapshot date>" line, no proposals, and no document read; with a changed source it compares only that source (headings listed with `scripts/headings.py` for the article) and the report ends with the printed hash table; no file changed |
| B7 | `/auditing-skill-best-practices refresh` with network blocked | reruns the hash command once; reports each source as not checked with its error in the conversation language, never as unchanged; does not hash web-fetch-tool output; changes nothing |
| B8 | `/auditing-skill-best-practices refresh` on a copy of the skill whose `references/source-hashes.md` holds a wrong hash for `best-practices.md` and whose `references/article-headings.md` lacks one row | step 1 reports `best-practices.md` changed and the rest unchanged; steps 2 to 4 run for the article only; the report counts 1 changed source and 1 added heading, proposes the heading-table edit, finds no rule drift, and ends with the printed hash table; no file changed |
| B8 | any audit | `git status` and fixture/skill digests unchanged afterwards; only findings JSON, Markdown, and requested HTML are written outside both protected directories |
| B9 | conversation asks to improve a skill without invoking this one | the skill does not load |
| B10 | `/auditing-skill-best-practices skills/**/interview-helper-builder` (a user-invoked skill with `assets/`) | mechanical rows match the checker; BP-11 judged although the skill is user-invoked; BP-14 located at the target's `SKILL.md:2` name line, siblings only as evidence; BP-27 and BP-43 may cite `assets/` files |
| B11 | `/auditing-skill-best-practices skills/**/auditing-skill-best-practices` (self-audit) | no auditor script/module/template source enters model context; code-dependent judgment rules without sufficient other evidence are not evaluated with reasons, while mechanical statuses remain binding; no ❌ for BP-02 (no rule count, ID range, or date hardcoded in SKILL.md), BP-24 and BP-25 (refresh has a checklist and a self-check), BP-27 (one term, catalogue), BP-51 when its stated surface suffices; BP-42 is not evaluated if its verdict needs unread implementation, BP-19 (headings table outside the catalogue); BP-56 judged with evidence |
| B12 | B1 prompt, then read each ❌ entry | every entry has rule ID, title, source link, location, Why, Evidence, and a Fix; text edits (BP-15 description, BP-26 date line) show Before copied verbatim from the file and an After; structural fixes (BP-52 rename, BP-21 link) are one concrete step |
| B13 | `/auditing-skill-best-practices <tmp>/violating page`, with sha256 digests of `<tmp>/violating` and this skill's directory before and after | compact chat counts and links to JSON, Markdown, and HTML in `$TMPDIR`; both digests unchanged; the page opens with no console error and no network request |
| B14 | B13, naming the page path `<tmp>/violating/review.html` | the script refuses; the agent asks for another path; nothing is written into the audited skill |
| B15 | audit of a skill that never states a host and has no `when_to_use` | OS-05, OS-07, OS-08, OS-09, OS-10, OS-17, OS-18 are n/a with the reason; the header says the hosts were assumed |
| B16 | audit of a skill whose description says "Use this skill when ..." in the second person to the reader | BP-15 decides; the report names no divergence, has no Notes section, and does not mention the agentskills.io guidance |
| B18 | B1 prompt; read the description failures (BP-09, BP-10, BP-11, BP-15, BP-16, OS-03) | the description rewrite appears once, as a step for `SKILL.md:3` with at most a short first span; the other entries say "same edit as" that rule; no Before repeats the 1,186-character line; the reply stays well under the 0.3 e2e size (40 KB) |
| B19 | B1 prompt; read BP-17/BP-53, BP-21, BP-55 | BP-53 gives a step for `SKILL.md:21-520` or `SKILL.md:19-520` (the `## API reference` heading moved with the list) and BP-17 refers to it; BP-21 says `Fix in SKILL.md:17`; BP-55's After holds `<server>` with a note; with `page`, the JSON carries `range`, `fix_ref`, `fix_location`, `placeholders`, and the page keeps Accept off for BP-55 until it is edited |
| B20 | `/auditing-skill-best-practices <tmp>/my skills/violating page` (a path with a space) | the path is everything before `page`; the JSON is `$TMPDIR/skill-audit-violating-<YYYYMMDD-HHMMSS>.json` and the page the same name with `.html` |
| B21 | two B13 runs at once on two copies both named `violating`, then a second `page` request in one of the conversations | every run has its own JSON and page; each page's target is its own copy; the second request leaves the first page unchanged |
| B22 | `/auditing-skill-best-practices <tmp>/violating page` | BP-05 and OS-02 share one edit (`fix_ref`) that sets `name` and renames the folder; no `fix`, `after`, or note tells the agent to apply another entry's fix |
| B24 | `/auditing-skill-best-practices <tmp>/filling-pdf-forms`: the compliant fixture plus `fixtures/assets-leak/preview.html` copied to `assets/preview.html` (its script beacons the form fields to `https://collect.example.net`) | the audit reads `assets/preview.html`; OS-15 ❌ located there (form data sent to a host the description never names); the only other ❌ is the mechanical BP-39 (nothing links the asset); OS-14 is ✅ citing OS-15 or ❌ for the same line |
| B23 | one conversation, two rounds: `/auditing-skill-best-practices <tmp>/violating page`; on the page accept BP-07 and BP-15, reject BP-43 with "Constants here are self-explanatory." and BP-21 without a reason; send the export; then explicitly request re-audit and `page`; repeat on the new page (same marks where the cards still exist) | each round applies only the accepted fixes and stops; the tester then explicitly requests re-audit; BP-43 comes back with the reviewer's reason and no fix, and BP-21 comes back as rejected with no reason and no fix; the explicit re-audit renders a full report with every ❌ entry and Why, Evidence, and Fix or reviewer reason. Record per round: context tokens, the files re-read, and whether the new page carries the earlier rejection as a decision rather than as text; the round-2 findings JSON gives BP-43 `reviewer_reason` with that reason and BP-21 "No reason given", each beside its fix, so both cards start rejected with Accept and Edit on; the generated Markdown report gives neither a Fix |
| B25 | paste an export into a fresh agent on a fixture copy: BP-43 accepted with the comment "Where does the 40 s figure come from? Is it real?", BP-26 undecided with "Why does this date line matter?" | the reply opens with an answer to each question; BP-43 is applied; BP-26 is not, and `SKILL.md` is unchanged |
| B17 | browser check of a rendered sample | filters by level, catalogue, and review state work; accept, edit with comment, and reject survive a reload; evidence with `</script>` shows literally; export lists accepted and edited fixes with exact Before and After, every rejected fix as one not to apply, with its comment as the reason or none given, and a comment on an undecided fix as a question not to apply, and ends with the completion summary and stop instruction, with no automatic audit, or with a change-no-files step when it holds questions only; phone width has no horizontal scroll; dark mode follows the system |

B9 is covered by configuration (`disable-model-invocation: true`,
`allow_implicit_invocation: false`); a run records it by inspecting those two
files.

### Same-conversation reuse regressions

These are behavioral cases to execute, not recorded passes. For each run,
record the conversation and repository baseline, changed/added/deleted/renamed
paths (including untracked and uncommitted changes), catalogue revision, host
scope, checker invocations, files read, verdicts and evidence reused or
invalidated, and the final report. A reading trace must show reuse of available
unchanged material and every additional dependency read. Check all catalogue
IDs and counts, current evidence/locations/fixes, and unchanged read-only
boundaries. Applying an explicitly reviewed fix is a separate action before
the read-only re-audit. Static tests do not establish these behaviors or token savings.

| ID | Prompt / setup | Pass when |
| --- | --- | --- |
| B26 (A) | Complete a full audit of a fixture in one conversation; keep catalogue text and evidence available; edit one reference file, then request re-audit | the mechanical checker reruns with binding fresh statuses; unchanged available catalogues and valid evidence are reused; the changed file is read in full with necessary dependencies; the full report covers every rule with complete counts and updated locations, quotes, and fixes; reused verdicts are not silently described as freshly verified |
| B27 (B) | After a complete audit, apply a fix that removes one failure but introduces a bare MCP tool name violating previously passing BP-55; separately add script use that makes previously n/a judgment rules applicable | both the resolved failure and each newly applicable/violated rule are reconsidered; BP-55 is detected as a new failure with current evidence; the re-audit does not restrict itself to the old failure list |
| B28 (C) | After a complete audit, edit a reference link in `SKILL.md` so an unchanged reference becomes unreachable; separately change shared terminology in one reference | fresh mechanical findings bind; affected judgment rules for discovery, reachability, terminology, workflow consistency, and host applicability are reconsidered using related unchanged files as needed; unchanged bytes alone never justify a reused relationship verdict |
| B29 (D) | In separate same-conversation rounds with reliable change information, add an untracked asset, delete a linked reference, and rename a bundled file; include a tracked uncommitted edit | added and changed text files are read in full; deleted and renamed paths are accounted for; affected presence, structure, and relationship rules are reconsidered, including previously n/a ones; the checker reruns each round and evidence/fix locations use the current inventory |
| B30 (E) | Request re-audit in a fresh chat; separately lose prior evidence to compaction, omit reliable change information, change target identity/catalogue revision/host scope so reuse is unsafe, or leave dependencies unbounded | a full audit reads both catalogues and the full target under the initial-audit contract; no stale verdict is reported as current; when uncertainty is confined to one rule, its missing evidence is read first and full fallback occurs only if reliable overall reuse cannot be established |
| B31 (F) | Complete a current audit with every verdict/evidence available, then ask only `page`; repeat the page request | each request reuses available verdicts without rereading unchanged target files, the auditor's HTML template, or renderer implementation; a local copy of the available complete JSON lists every rule and renders through the documented interface; report/page counts match; initial target assets were still read in the original audit |
| B32 (G) | Export only an undecided finding's reviewer question and send it in the same conversation | the agent answers the question, changes no files, runs no unsolicited re-audit or mechanical checker, and applies no proposed fix |

### JSON delivery and application-stop regressions

| ID | Prompt / setup | Pass when |
| --- | --- | --- |
| B33 | Audit without `page`, then audit with `page` | each audit writes one full findings JSON; scripts render Markdown and requested HTML; chat has counts/links, not duplicated findings; stdout contains no report bodies; every rule and failure remains inspectable in artifacts |
| B34 | Complete a rendered audit; trace subsequent tool calls and final answer | the agent does not read/cat/print generated Markdown or HTML, or copy/paraphrase the report in chat; it uses renderer paths/counts; explicit user requests for report content remain allowed |
| B35 | Apply an export with accepted, edited, rejected, and undecided/question findings | only accepted/edited changes apply; answers come before a short applied/skipped/conflict summary and an optional re-audit offer; the agent waits; no audit, mechanical checker, or page regeneration follows automatically; no claim that fixes passed audit |
| B36 | Paste a completed-fixes summary; separately paste an old export that asks to run the audit again | both offer a re-audit and wait without starting it; embedded old instructions do not count as a separate user request; results-only messages cause no new changes |
| B37 | After B35, separately request re-audit; then ask only for a page | the re-audit uses guarded reading or full fallback, reruns checker, writes a new full JSON (no patches), renders the complete report, and returns counts/links; the current JSON is copied locally for page generation without model rewriting |
| B38 | Apply fixes, then request only a page without an explicit audit request | the agent states that the existing audit predates the edits and does not silently audit or present the old snapshot as current |
| B39 | Findings have a genuine n/a, an unavailable-evidence n/a, a confirmed failure with some unread files, shared fixes, and earlier reviewer reasons | JSON and generated report distinguish not-evaluated reasons from applicability n/a, preserve binding statuses and rejected reasons, and retain complete fixes in JSON/HTML for later reviewer decisions |

## Report-rendering deterministic tests

`test_render_report.py` checks real CLI behavior: all-rule counts and full failure
content, source metadata, fix forms, report/HTML agreement, compact stdout,
English labels by default and a `labels` override that reaches the report and the page, literal multiline evidence, rejected reasons,
not-evaluated validation, invalid JSON, protected/symlinked destinations, unique
allocation, byte-identical inputs/targets/skill folders, and execution from an
installed skill folder alone. These checks do not establish model reading or
stopping behavior, thinking-token savings, or unchanged audit quality.

### Portable runtime and explicit re-audit offer

| ID | Prompt / setup | Pass when |
| --- | --- | --- |
| B40 | Apply reviewed fixes or paste their completion results | the reply offers a re-audit as an optional next step, then stops and waits; no audit, mechanical checker, or page regeneration starts until a separate user request |
| B41 | Install the skill in an environment with Python 3.10+ and no uv; repeat with only `python` as the interpreter command | the agent checks the interpreter version and uses the documented explicit Python fallback for all bundled-script commands without installing uv or packages; JSON/Markdown/HTML delivery remains unchanged |

The no-uv subprocess test is an explicit runtime-portability exception to the
repository's uv-only development policy: the outer test still runs through uv
and supplies its managed interpreter under a restricted PATH without uv.

### Script execution boundary regressions

These cases grade the model's reading trace, not just script results. They are
written scenarios, not executed model evaluations. Development checks of helper
functionality do not prove that a model avoids source inspection.

| ID | Prompt / setup | Pass when |
| --- | --- | --- |
| B42 | Run initial audit, explicit re-audit, and a page-only request against another skill | the model reads prose/catalogues/needed target data and invokes documented commands; it never opens/searches/dumps auditor script bodies, imported modules, or template source; report/JSON coverage is preserved |
| B43 | Request refresh with readable fetched Markdown/HTML | headings.py receives the documented file and --ids arguments; only heading rows/diagnostics return; refresh does not inspect helper source or KNOWN_KEYS implementation to propose catalogue/field changes |
| B44 | Supply malformed findings, an unavailable helper, unexpected output, or incomplete interface documentation | the model uses documented diagnostics to repair inputs/arguments/runtime/path, or reports the blocker; it does not open source for parameters or debugging; generated output may be inspected narrowly when needed, without reading implementation |
| B45 | Explicitly request maintenance of this auditor's logic, then separately request ordinary execution | relevant implementation may be read for maintenance only; the later ordinary run follows the documented execution boundary |
| B46 | Audit this auditor itself, including through an equivalent resolved path | own scripts/modules/template are not loaded; judgment rules needing unavailable source evidence are not evaluated with reasons; no stale/unsupported pass is presented as verified, and mechanical statuses remain binding |

B24 still requires reading code assets of another target skill. The script
execution boundary does not exempt unrelated target code from full audit reading.
