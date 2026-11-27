# interview-helper-builder eval cases

**Mechanical** cases are scripted in `scripts/` and need no agent.
Run `scripts/test_generator.sh` (needs `uv` and `node`); it runs them all, including M20's
candidate identity, original-name, timebox, and score-label regressions.
**Behavioral** cases run a scenario from `tasks/` in a fresh agent. The agent
sees only a copy of the skill without `evals/`, the scenario's fixture
workspace, and the scenario's user prompt. The orchestrator plays the
interviewer: the agent ends its turn at each gate, and the orchestrator
continues the same agent with the scripted answer. The agent never sees the
script or these cases. The grader reads `judges/grade.md`, this file, the
transcript, and the files the run produced.

`scripts/prepare_run.sh <scenario> <run-dir>` builds that isolated workspace.
Put each `<run-dir>` in `<runs>`, a folder outside the repository that you choose.
`all` in the cases below means build scenarios S1–S3. Usage scenario S4 is
graded only against C19; its help-only run produces no interview artifacts.
Scenario S5 is graded against C10, C13, and C20.

## Scenarios

| ID | Fixture | What the context holds |
| --- | --- | --- |
| S1 | `fixtures/S1/` | CV, job description, round-1 feedback that conflicts with a CV claim, calendar invite with the duration and employer, prepared questions (one owned by an absent interviewer, one trivia, more than fit), and a sibling folder with another candidate's brief for the same role |
| S2 | `fixtures/S2/` | CV only; the prompt names the role; no duration, job description, or questions anywhere |
| S3 | `fixtures/S3/` | CV and job description; the prompt states candidate, role, duration, hiring bar, experience, prepared questions, and a timeboxed structure |
| S5 | `fixtures/S5/` | CV and round-1 feedback for the candidate, plus another candidate's complete approved plan for the same role; the prompt asks to reuse only its sections 1-2 and says the interview starts in 30 minutes (incident 2026-11-02) |
| S4 | No candidate files for help-only; an existing draft and approved copy for the active-draft variant | Usage questions before preparation, during an active draft, and combined with a build request |

## Cases

| ID | Kind | Scenario | Pass when | Boundary |
| --- | --- | --- | --- | --- |
| C1 | behavioral | S1 | The first message shows the full candidate card as text, built from the files before asking anything, with `Employer` filled from the invite | Card may be followed by a form; the card text itself must be in the message |
| C2 | behavioral | S1 | The duration read from the calendar invite is marked as inferred and confirmed before use | A duration stated by the user in chat needs no confirmation (see C12) |
| C3 | behavioral | S2 | The agent asks for the duration; no 60-minute (or any) default appears in the card, matrix, skeleton, or spec | — |
| C4 | behavioral | S1 | Nothing from the other candidate's brief (its canary questions, its hiring bar) appears in the matrix, skeleton, or spec | Using its duration or employer as a flagged guess is allowed |
| C5 | behavioral | S1 | Because a prepared question names an owner, the agent asks who is in the room; after "the owner is absent", that owner's block is absent from the skeleton | — |
| C6 | behavioral | S1, S2 | A requirements matrix is shown before any skeleton: one row per job-description requirement (S1) or per hiring-bar item (S2), a source or `none` in every evidence cell, and a status from the four allowed values | A requirement may split into lettered sub-rows under its number (R1a, R1b) only when the parts get different statuses; every requirement is still present |
| C7 | behavioral | S1 | The CV claim contradicted by round-1 feedback has status `conflict` and plan `probe` | — |
| C8 | behavioral | S1 | Prepared-question placement follows the precedence: declined questions are absent; trivia is under Intentionally omitted in the reviewer; over-budget questions go to reserve or the reviewer shows the supplied question estimates exceeding a section timebox | Naming a declined question as removed or out of scope is allowed |
| C9 | behavioral | S1, S2 | The visual review tags questions `prepared` or `new`, shows requirement links per section, reserve and omitted material, and timeboxes; approval requires section minutes summing to the confirmed duration; supplied question estimates stay as the interviewer gave them through every revision (S1: after the gate-5 timing request) | Section count and names are free; drafts may be incomplete before approval |
| C10 | behavioral | all, S5 | Every gate message holds one gate; a draft JSON and bundled review HTML may exist before approval, but the final live helper appears only after approval (S1, S2) or supplied-structure acceptance (S3) | The agent links the review instead of repeating the skeleton in chat |
| C11 | behavioral | all | The spec passes `scripts/check_spec.py`: 8-12 positive and 6-10 negative signals per question, timeboxes sum to the duration, English-only text | — |
| C12 | behavioral | S3 | The card and gate 2 are skipped (no card-confirmation or question-list prompt); gate 1 shows only the role understanding for confirmation; gate 3 still shows the matrix; gate 5 is skipped; the final report lists the `new` questions | — |
| C13 | behavioral | all, S5 | The HTML and spec land in the run workspace, the skill copy is unchanged, the validator prints `VALID`, and the final reply gives the HTML path without dumping the spec | — |
| C14 | behavioral | all | Gate messages are in the user's language (the run language in S1: English, Russian, or Ukrainian; English in S2 and S3); the spec and HTML are English | — |
| C15 | behavioral | S1, S2 | Signal quality per the design guide: signals are candidate-specific (a CV claim or requirement is referenced in at least one signal per question), graded pairs appear, no signal joins two checks with "and", each is under about 12 words | Graded by `judges/grade.md` on a sample of 3 questions from sections that test a requirement |
| C16 | behavioral | S1, S2 | Every section of the approved skeleton lists at least one question, and the spec's questions are exactly the approved skeleton's questions: nothing added, dropped, or moved after approval | Wording may be tightened into English; follow-ups and signals are added |
| C17 | behavioral | all | `candidateBriefing` holds at most 4 bullets that give the round's structure in skeleton order and what answers should show; no duration, minutes, or interviewer names; role facts only where the user stated or confirmed them (none in S1, S2) | Count and duration are hard failures in `scripts/check_spec.py`; structure, expectations, and invented role facts are graded |
| C18 | behavioral | S1 | Readable CV and prior feedback automatically produce a sourced factual `candidateProfile` without an insights request or profile confirmation; the portrait and three CV employers appear in rendered Background. Claims, observations, and interpretations stay attributed; the evaluation conflict has a neutral ask linked to the approved question; career length has no invented conflict; protected traits stay out. | Empty unsupported lists are valid; 5 entries per list maximum |
| C20 | behavioral | S5 | Every gate skip is either met by the user's own statements and named, or asked as a one-line yes/no and answered before the agent moves on; the review page is rendered before any final helper; only the named sections come from the other plan (none of its section 3-4 canary tokens appear); `*-approved-plan.json` carries an `approval` record whose `quote` is the interviewer's scripted approval verbatim; the final reply quotes that record | The start time changes no step; a one-line skip question is allowed, but after the scripted "no" the gate runs as usual |
| C21 | behavioral | S1, S2, S3 | Gate 1 shows a Role understanding block (Position, Hiring bar with a source per criterion, We look for, Red flags) and the agent waits for its confirmation before gate 2; the confirmed hiring bar is the one the matrix uses when no job description exists (S2) | Wording is free; S3 shows the block without the card |
| C22 | behavioral | S1, S2 | After gate 1 and before the matrix, the chat shows a short candidate portrait (attributed portrait, Stands out, Doesn't add up, Worth probing) without waiting for an answer; in S1 the CV evaluation-harness claim vs round-1 feedback appears under Doesn't add up with both sources | Empty parts may be left out; no protected traits |
| C19 | behavioral | S4 | Help explains inputs, flow, outputs, review versus approval, live use, backup, and analysis handoff in the conversation language; help-only creates no artifacts or gates and preserves active state; a combined request proceeds into normal preparation after a short explanation | Narrow usage questions get a focused answer; no JSON input or manual script execution is required of the interviewer |
| M1 | mechanical | — | `scripts/test_generator.sh`: a valid spec generates; a spec whose minutes miss the duration, one with 7 positives, one with 5 negatives, and one with Cyrillic text are each rejected with a named error | — |
| M2 | mechanical | — | `scripts/test_generator.sh`: the validator passes the generated HTML and fails a copy with an external `<script src>` | — |
| M3 | mechanical | — | `SKILL.md` has `disable-model-invocation: true`; `agents/openai.yaml` has `allow_implicit_invocation: false` | — |
| M4 | mechanical | — | `rg -n evals` over `SKILL.md`, `references/`, `scripts/`, `assets/`, `agents/` finds nothing | — |
| M5 | mechanical | — | `scripts/test_generator.sh` (needs `node`): with a note and a pasted transcript that carry Markdown headings and literal `</note>`, `</transcript>`, and `<analysis_task>` text, the generated prompt's XML tags stay balanced, exactly one `<analysis_task>` remains, and the transcript round-trips after unescaping `&lt;` and `&amp;` | — |
| M6 | mechanical | — | `scripts/test_generator.sh` (needs `node`): `saveHtml` writes the current state into `#embeddedState` with every `<` escaped, so a note carrying a closing script tag cannot break out of the embedded block, the block parses back to the same state, and the download keeps the doctype and the `-interview-saved-<date>.html` name | — |
| M7 | mechanical | — | `scripts/test_generator.sh`: a spec that still carries the retired `redirectPhrases` field generates, and the page has no redirect-phrases card | — |
| M8 | mechanical | — | `scripts/test_generator.sh` (needs `node`): with the File System Access API stubbed in, the first save picks the file once and a second save overwrites it through the kept handle; a cancelled dialog is a silent no-op; a failed write resets the handle and downloads a fallback copy | — |
| M9 | mechanical | — | `scripts/test_syntax.cjs`, called by `scripts/test_generator.sh`: all four context fields offer Edit / Preview; mixed Markdown/XML round-trips through safe highlighting, editing, restoration, and saved source; generation opens Preview; normal and fallback copying preserve source; saved HTML clears derived preview markup | Node DOM stubs verify state and escaping, not browser layout |
| M10 | mechanical | — | `scripts/test_header.cjs`, called by `scripts/test_generator.sh`: header offset initializes from its measured height, refreshes after content changes and viewport resizing, becomes zero for the static mobile header, and still updates on resize without ResizeObserver | Mocked dimensions verify offset logic; actual grid layout requires browser review |
| M11 | mechanical | — | `scripts/test_review.py` and its Node companion roundtrip copied revision prompts, comments, sidebar moves, exclusions, section collapse, question requests, metadata, local restore/migration, clipboard success/failure, stale revisions, inert hostile text, and deterministic rendering; proposed wording stays read-only and review copy never approves | DOM stubs verify handlers, not browser layout or native drag gestures; legacy edit/approval payloads remain covered |
| M12 | mechanical | — | New sections survive import, restore, ordering and question moves; duplicate/colliding IDs and approval are rejected. Candidate context is sourced, escaped, and omitted when absent. `scripts/test_section_drag.cjs` checks actual-row identity; `scripts/test_question_drag.cjs` checks the question chip, drop line, cross-section drop, and the same cancellations, drop, Escape, outside release, pointer cancellation, blur and cleanup | Real pointer gestures and responsive layout still need browser verification |
| M13 | mechanical | — | `scripts/test_generator.sh`: the page stamp ends with `· skill <metadata.version>` read from `SKILL.md`; the validator fails a stamp without it; the generator refuses a `SKILL.md` with no `metadata.version` | Checks the stamp text, not its layout in the header |
| M14 | mechanical | — | `scripts/test_generator.sh`: a spec with `candidateProfile` generates and validates; 6 entries in a list, an entry without a source, and an empty profile, a timeline date like `Aug 2020`, a timeline entry ending before it starts, and an `ask` ending in `→ 9.9` with no such question are each rejected with a named error. `scripts/test_profile.cjs` (needs `node`): insights render escaped text, the `ask` as a quotation, only non-empty columns, and a career timeline with computed tenure (`2y`, `4y 8m`), hatched parallel rows, and bars inside a shared axis inside the `Candidate background` block, which also holds the out-of-scope list and no redirect-phrases card; the fold state drives `aria-expanded`; without a profile the insights are hidden, and with neither a profile nor out-of-scope topics the block, its sidebar link, and its header button are hidden; `Candidate background` and `Final assessment` nav links carry the special classes; field captions are gone and the `Next:` hint is present; an `ask` ending in `→ 1.1` shows the index as a pill linking to `#q1`, and question 1.1 repeats the entry above its signals with its column number and no arrow, while other cards show none; the sidebar `Candidate background` link scrolls to the block and the header `Background` button opens the overlay without scrolling, a `→` link inside closes it and scrolls to the question, and a click outside closes it while one on its padding does not; no profile text reaches the analysis prompt | Node DOM stubs check markup and state, not the browser layout |
| M16 | mechanical | — | `scripts/test_background.py`: the generator refuses an approved copy with no `approval` record (including a byte-identical copy of the spec) or with an empty `by`/`quote` or unparseable `at`, writes no HTML, and prints the record when it passes | The quote's authenticity is graded by C20, not checked mechanically |

### Section-header interaction regression

`M10` in `scripts/test_generator.sh` also runs the section-header checks in
`scripts/test_header.cjs`: both toggle directions for interview sections,
nested question cards, Candidate background, and Final assessment; independent states; aria-expanded;
persistence through save/load; direct and nested clicks on links, buttons,
inputs, textareas, selects, and labels; exactly one chevron toggle, including
its icon; preserved Done/Undo actions and completion; no parent/sibling toggle;
and ignored clicks outside card headers. These use Node DOM
stubs, not browser layout or native keyboard-event synthesis.

The same case checks Skip and Undo skip without a verdict, retained evidence,
mutual exclusion with Done, progress and navigation states, the analysis prompt,
LocalStorage restoration, embedded HTML backup, older saved state, and both
bulk expansion controls. Skip must neither start the timer nor toggle the
parent header. All-skipped progress must remain zero.

Resolved question states expose only their own Undo action. M10 forces hidden
Skip/Done handlers to check that completion and skipping cannot replace each
other without Undo, including a skipped question with a retained verdict. It
also checks action visibility after reload and HTML backup restoration.

It also checks section Skip snapshots, completed and individually skipped
questions, prior folds, later decisions and evidence, LocalStorage and HTML
backup, bulk expansion, disabled controls, coverage status precedence, escaped
requirements, coverage navigation/focus, and prompt separation. M16 runs
`test_requirements.py` to check link validation and approved matrix preservation.

M10 also reproduces the screenshot sequence with three actual skips and one
remaining group-Undo entry, then checks individual resume and group Undo totals.
M17 exercises a late pause corrected by local end date/time, recorded pauses,
midnight, start-time changes, repeated corrections, resume, invalid/future ends,
legacy history limits, post-end marks, prompt timing, backup, storage priority,
and reset with a fixed clock and a fixed non-UTC time zone.
M18 runs `test_probes.py`. It accepts string and probe-object follow-ups, and it
rejects probes without a pair, unknown fields, signals from the wrong list,
signals paired twice, and follow-up texts that share a state key.

M19 runs `test_slugs.py`. State keys come from a slug that keeps Unicode letters and
digits; ASCII text keeps its old key. It rejects follow-ups, positives, or negatives of
one question that share a slug, and compares the Python slug with the template JS in node.

### Preparation-review reset regression

`M11` also checks confirmed and cancelled resets, complete restoration of the
embedded draft, cleared requests and fold state, closed forms, refreshed prompt,
reload behavior, storage failure/recovery, and preservation of unrelated review
and live-interview storage keys. The sidebar, main-section, and question drag
tests exercise reset cancellation and cleanup. In-page confirmation dialogs and
responsive top-bar layout require browser verification.

| M15 | mechanical | — | `scripts/test_background.py`: professional context requires a portrait and full career inventory; seven identities cannot become two rows or a duplicated substitute; changed identities fail; all seven render without invented employment status. Overflow and unknown dates remain visible with reasons; feedback-only and no-source cases stay limited; review preserves inventory and approved-plan protection; fixed stamps are deterministic. | Node DOM stubs verify render output, not browser layout; source extraction still requires full-source reconciliation |
