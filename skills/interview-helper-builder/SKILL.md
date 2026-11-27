---
name: interview-helper-builder
description: Build a reusable, candidate-specific interview helper as one self-contained local HTML file. Use when the user provides a role description, candidate CV/resume, prior interview feedback, hiring context, or connected Calendar/Slack/Drive context and wants a structured live interview page with adaptive questions, graded positive-signal and follow-up ratings, negative-signal marks, collapsible sections, LocalStorage autosave, pacing, scoring, sourced candidate background, optional interpretations, and a final handoff prompt. Walks the interviewer through candidate, prepared-question, requirements-match, and structure checkpoints before generating the HTML.
metadata:
  version: "2026.11.27.1"
disable-model-invocation: true
---

# Interview Helper Builder

Create a candidate-specific interview plan and render it into a stable, reusable local HTML interview helper.

The UI mechanics stay consistent across candidates. The interview sections, questions, follow-ups, positive/negative signals, timeboxes, score dimensions, and analysis context must adapt to the role, candidate, and evidence already available.

## Modes

- **Help**: when invoked with `help` or `--help`, or asked how to use this skill,
  what its flow is, or what it takes in and produces, read
  [references/usage-help.md](references/usage-help.md). Explain in the conversation
  language. A help-only request ends with the explanation and preserves any active
  draft and approvals; candidate gates and artifact generation belong to Build.
  When the user asks for help and building together, explain briefly, then continue
  Build from the existing confirmed state.
- **Build**: for interview preparation, follow Workflow below.

## Workflow

Follow these steps in order. Steps 1, 2, 3, and 5 are **gates**: each asks the interviewer for one thing and ends on its completion criterion.

Gate rules:
- Skip a gate only when the user's own statements in this conversation already meet its criterion in full, and name the skipped gate in one line. Gate 5 is met only by explicit chat approval or a complete supplied structure (step 5).
- Every other skip is the interviewer's call. Ask in one line, for example "Skip the visual review and go straight to the final helper? yes/no", and wait for the answer.
- Confirm inferred interview decisions and logistics from files or connected sources. Readable professional evidence is reusable as sourced claims or observations; extracting it for the candidate card or Background needs no separate confirmation.
- Ask one gate per message and wait for the answer. Write gate messages in the user's conversation language.
- Candidate and matrix gates carry their full content as text. The structure gate uses the bundled visual reviewer; link or open its generated page instead of repeating the plan in chat. When the harness has a structured question tool, a form answer confirms only the fields the form itself showed.

Prefer user-provided text and files. Use connected Calendar, Slack, Drive, or other sources only when the user explicitly asks for them or clearly references them as necessary context. When files contain relevant context, read them rather than inferring unseen content.

The CV, prior feedback, and interviewer remarks arrive in any form: pasted text, images or screenshots, PDF, DOCX, or other files. Tell the form from the content itself, extract its text (read images visually; render a scanned PDF's pages and read them), and pull out the facts the workflow needs. Ask only about a specific unreadable part, material contradiction, or decision the sources cannot resolve. Omit an optional unknown detail and continue with supported material.

The bundled scripts need only Python 3.9 or newer and its standard library. Run `uv --version` before the first script call: when uv works, run every script with `uv run --script` as written; otherwise run the same commands with `python3` in place of `uv run --script` after `python3 --version` shows 3.9 or newer. Install no Python packages: the scripts need none. With neither available, ask the user to install uv or Python 3.9+.

Material about a different candidate, such as another person's brief or plan for the same role, is not evidence for this one. Use it only as far as the interviewer explicitly asks, or as an inferred guess for shared facts (duration, employer) that gate 1 confirms.

### 1. Gate: candidate and role

Build the card and your reading of the role from the working context before asking anything: the conversation, attached files (CV, job description, prior feedback), and sources the user pointed at, such as a calendar invite. Then show both and ask the interviewer to confirm them and fill only the gaps:

```text
Candidate: <name or identifier>
Role: <target role>
Employer: <hiring company or client, if known>
Role pitch: <1-3 facts to tell the candidate about the role and team, or "unknown">
Duration: <minutes>
Date: <interview date, or "unknown">
Experience: <3-5 lines: CV summary with the strongest claims>
Prior feedback: <1-3 lines, or "none">
Language: English (default; name another to change it)
Missing: <fields still unknown>

Role understanding
Position: <1-2 lines: what the job does, its level, and the client or team context>
Hiring bar: <3-6 criteria, each with its source: job description, your remark, or inferred>
We look for: <2-4 observable signals that would make this candidate a strong hire>
Red flags: <1-3 signals that would rule a candidate out for this bar>
```

The role understanding is your reading of the position, so the interviewer confirms it every time. When the user's own statements already meet the card, show the role understanding alone.

Duration has no default. Take it from the context (a stated length, the calendar slot) or ask for it; a length read from a file or connector is inferred and needs confirmation. So is a date read from a file or connector, such as a calendar invite.

Done when candidate, role, duration, hiring bar, and experience are known, the interviewer confirms the role understanding, and inferred decisions/logistics are confirmed; experience read from supplied sources needs no re-approval. Accept explicitly unavailable experience without inventing it. Employer, date, role pitch, and prior feedback are optional: ask once and accept "none" or "unknown". Language is English unless the interviewer names another; it sets the language of the plan, the spec, and the page content, while comments may use any language. Build the role pitch only from what the user states or confirms, never from a file alone; when the user's statements already meet this gate, leave the role pitch and any inferred date `unknown` rather than opening the gate for them.

### 2. Gate: prepared questions

Open this gate's message with a short candidate portrait in the conversation language: the **Chat summary** in `references/candidate-insights.md`, built from the confirmed card and this candidate's sources (CV, prior feedback, interviewer remarks). It states who this professional is by the facts and surfaces what stands out, what does not add up, and what is worth probing. It is information for the interviewer, not a gate: apply any correction they give, and carry its entries into gate 3 evidence and `candidateProfile`. When this gate is skipped, show the portrait in the next message anyway.

Ask whether the interviewer already has questions they want to use. A rough list, pasted notes, or bare topics all count; "none, generate them" is a valid answer.

When prepared questions name an owner ("Peter asks this"), also ask who is in the room: a block whose owner is absent drops out.

Done when the interviewer supplies a list or says to generate the questions, and the panel is known whenever a question names an owner.

### 3. Gate: requirements match

Match the role's requirements against every piece of evidence about this candidate: the CV, prior feedback, the prepared questions, and any other file found for this candidate. Take the requirements from the job description; without one, from the hiring bar confirmed in step 1. Show the result:

```text
Requirements match - <role>
| #  | Requirement   | Evidence (source)               | Status       | Plan      | Prepared |
| R1 | <requirement> | <CV: led X migration, 2023>     | claimed      | deep-dive | Q2       |
| R2 | <requirement> | <Round 1 feedback: strong on X> | demonstrated | skip      | -        |
| R3 | <requirement> | <CV says X; feedback says Y>    | conflict     | probe     | Q5       |
| R4 | <requirement> | none                            | unknown      | must test | new      |
Low value for this bar: <prepared topics or areas, or "none">
```

Cite a source for every evidence cell, or write `none`. Status sets the plan: `demonstrated` → skip, `claimed` → deep-dive, `conflict` → probe, `unknown` → must test. Write requirement labels in the confirmed content language: they become section and score-dimension names.

One row per requirement. Split a requirement into lettered sub-rows under the same number (R1a, R1b) only when its parts get different statuses; parts with the same status stay one row.

Done when the interviewer confirms the matrix, with corrections applied and the matrix re-shown after each correction.

### 4. Build the interview strategy

Read `references/interview-design.md` before drafting questions: it holds time allocation, deep-dive patterns, and signal wording.

The matrix sets priority: `must test` and `probe` rows first, `deep-dive` next; `skip` rows get no meaningful interview time.

Place every prepared question by the first rule that matches:
1. The interviewer explicitly declined it → drop it.
2. Low value for this bar → list it under "Intentionally omitted" in the skeleton; the interviewer can restore it at step 5.
3. Fits the bar but not the time → reserve section. The interviewer's own time estimates, when given, are the fit test.
4. Otherwise → a timeboxed section.

Tighten a prepared question's wording without changing its intent. Generate new questions only for `must test`, `probe`, and `deep-dive` rows that no prepared question covers.

Prioritize discriminating questions over broad knowledge coverage. Favor questions that reveal how the candidate reasons and makes implementation decisions.

For senior architecture roles, distinguish strategy/reference-architecture fluency from implementation/runtime depth. For backend or data engineering roles, distinguish framework or tool familiarity from data-model, consistency, and failure-recovery depth.

Do not include generic coding, trivia, framework definitions, certifications, or theory quizzes unless they materially affect the hiring decision for this role.

Derive the score dimensions from the matrix requirements.

Start the draft JSON now using the final spec's shape and stable section/question IDs. Read `references/plan-review.md` for draft fields, pre-write temporary-file registration, and the review cycle. Choose the output location from step 6 now. Reuse the same draft, review HTML, saved feedback, and report paths on every iteration; do not create numbered revisions or backup copies. The existing review HTML retains the prior draft for change marks. Before an agent writes a temporary file, register its exact path with `ignore` in `<output-dir>/.gitignore` when inside Git, even when shell cwd differs. Keep final artifacts, the active approved plan, sources, the requirements matrix, and permanent preparation state out of these rules. Fill only known draft fields and defer signals/follow-ups until structure approval.

Carry the confirmed candidate card and requirements evidence into optional
`candidateFacts` and `candidateInsights` entries (`text`, `source`). Facts summarize
supplied claims or prior observations; insights state tentative interpretations
worth testing. Cite the existing source in every entry, label inferences, and
omit unsupported entries. Use only this candidate's material already available
under the source-access rules above.

Set `candidateBackgroundRequired` to `true` in the draft when a readable CV or
substantive professional context is available (including prior feedback alone),
and to `false` when none is available. Preserve it through review and enrichment.
Read `references/candidate-insights.md` and prepare the sourced factual
`candidateProfile` automatically; facts/insights in preparation cards do not
populate the live Background. A separate insights request is unnecessary.
Extract the complete `candidateCareer` inventory from the full professional
sources, independently of the 3-5-line candidate card. Preserve every role,
engagement, and supplied project with its source and original date precision;
use `[]` only when sources contain no career entries. Preserve this inventory
through review and enrichment, and reconcile every entry with the source before
generating. The profile must account for each identity exactly once as a timeline
row or visible `additionalExperience` with a reason; see the reference for limits.

### 5. Gate: visual interview structure

Place every proposed question in the draft's timeboxed sections. Derive their number, order, titles, and minutes from the role, matrix, prepared questions, and confirmed duration. Include opening, closing, or candidate-question blocks only when needed; every included section has a question. Set question `origin` to `prepared` or `new` and section `requirementIds` to the matrix IDs it tests (empty for none). List every matrix row in top-level `requirements` as `{id, text}` with a short requirement label, so the review can show which requirements stay tested. Keep intentionally omitted topics. Supplied question estimates are the interviewer's own figures: change one only when the interviewer changes that question's estimate. A section-minute change sets section `minutes` alone; an estimate above its timebox stays, so the review shows the overrun.

Render the draft with the bundled `scripts/review_plan.py render` command from `references/plan-review.md`. Keep its template as shipped: inject data deterministically rather than writing a reviewer per candidate. It shows editable section titles and question text beside visible comment fields, with compact sidebar section reordering, question move/removal requests, whole-section removal requests, and timing steppers. Ask the interviewer to paste **Copy review prompt** into chat; downloads are not part of this workflow. All returned feedback is a request for the agent to fix the plan, not approval.

Apply the prompt's structured requests (wording edits, section and question additions, section removals, question moves and removals, and reviewer timing) with `review_plan.py apply` using the same draft path for `--spec` and `--output`, then resolve its comments in that JSON and regenerate the same review HTML. Apply wording edits exactly as written unless they break the plan; ask in chat if they do. On that regenerate, pass the existing review HTML as both `--previous` and `--output`: its embedded previous plan is read before replacement so the page marks what changed without another file; a missing previous file still builds the page. Complete new sections with questions, requirement links, and reconciled timeboxes, and draft each added question from its request text, before asking for approval; keep the reviewer timing values and rebalance the other timeboxes around them. Ask only about unresolved decisions. Keep IDs through edits and moves. Obtain explicit chat approval of the revised plan before enrichment; copying a review prompt never approves it.

When the interviewer supplied the whole structure (every section with a timebox, together covering the confirmed duration), place the questions into it and skip the approval prompt and review generation unless they ask for visual review. Keep that supplied structure as the approved draft. A partial instruction, such as "sections 1-2 like X's plan", supplies only those sections, so this gate runs.

On approval, save `<output-dir>/<candidate>-approved-plan.json`: the unchanged draft plus a top-level `approval` record `{"by": "<approver>", "at": "<ISO-8601 datetime with offset>", "quote": "<approving words, verbatim>"}`. Copy `quote` from the interviewer's own chat message that approves this plan, supplies its complete structure, or answers yes to skipping the review; without such a message the plan is not approved yet. Never edit the copy afterward; step 7 checks the spec against it. When the interviewer changes the plan after approval, re-save the copy with a new record once they approve the change.

Done when the visual plan is approved with feedback applied and comments resolved, or the supplied structure holds every question, and the approved copy carries its approval record. Draft JSON and review HTML may exist before approval; generate the final live interview HTML only afterward.

### 6. Create the interview spec

After approval, enrich the same draft into the complete JSON spec following `references/spec-schema.md`. It holds exactly the approved plan's included questions, wording, section placement, and order. Add follow-ups/signals without recreating the question list from prose.

Preserve the approved `requirements` and section `requirementIds`. Add question
`requirementIds` for the requirements that each question directly tests, using
only IDs from its section. Use `[]` for a question that tests none. These links
drive live role coverage; a section link alone does not prove that every question
tests that requirement. Preserve question links already present in the approval.

Save the spec and the generated HTML in the output directory: the location the user names, else the host's designated output directory when it has one, else the current working directory. Never write into this skill's own directory.

For every question in the approved skeleton, write:
- targeted follow-ups;
- 8-12 positive and 6-10 negative signals, written per the Signals section of `references/interview-design.md`;
- a probe pair on each follow-up that elicits one specific positive or negative signal, per the follow-up rules in `references/spec-schema.md`;
- a short interviewer cue where the answer is likely to drift or needs a timebox, saying only what its section's `coach` line does not.

All descriptive content inside the spec must be in the confirmed language (English by default), even if source materials or the current conversation use another one. Set `language` to its tag (for example `"ru"`) when it is not English.

Preserve the top-level `candidate` name in its original script, including on English pages. Translate descriptive content into concise professional prose in the confirmed language.

Section timeboxes are positive minute strings, such as `"10m"`; they sum to the confirmed duration. Reserve sections use `"if time"`. Draft approval and final generation apply the same timebox check.

Write `interviewDate` as `YYYY-MM-DD` when gate 1 confirmed a date; omit it otherwise.

Write `candidateBriefing`: at most 4 short bullets the interviewer tells the candidate at the start: the confirmed role pitch, the round's structure as the approved skeleton's blocks in order, and what the round expects from answers. Logistics the candidate already has, such as duration and names, stay out. Leave out what is unknown; an empty list hides the block.

Complete `candidateProfile` from the available professional sources under
`references/candidate-insights.md`: a factual portrait plus only supported career
data and list entries. Preserve attribution and uncertainty. Prior feedback alone
supports an attributed overview, with no invented career. With no professional
sources, omit the profile. Readable supplied evidence needs no profile-approval
gate; ask only for unresolved specifics under Gate rules. An addition or correction
after page generation updates the same spec and page while preserving the approved
questions, IDs, order, and timing.

Done when every approved question has follow-ups, signals within these ranges that each record one observation, and a cue wherever drift is likely. The generator rejects a spec with fewer signals or with timeboxes that miss the duration.

### 7. Generate the HTML deterministically

Resolve `scripts/` and `assets/` against this skill's directory (the folder containing this `SKILL.md`), not the current working directory. Run with the script runner picked under Workflow:

```bash
uv run --script <skill-dir>/scripts/generate_interview_helper.py --spec <output-dir>/<candidate>-interview-spec.json --approved <output-dir>/<candidate>-approved-plan.json --output <output-dir>/<candidate>-interview-helper.html
```

The generator refuses an approved copy without a complete `approval` record, and a spec whose candidate, role, duration, sections, questions, wording, order, or timing drift from the approved copy, listing each difference. Fix the spec, never the copy; a missing record means step 5 is unfinished. Without `--approved` it exits with a usage error and writes no page.

The generator stamps the page with the current local time and this skill's `metadata.version`; pass `--generated-at <ISO-8601 datetime with offset>` only to reproduce an exact stamp.

Use the bundled `assets/interview-helper-template.html`. Keep the template's UI as is. Do not read either template or any generated HTML page: the scripts render and validate them, and each file costs tens of thousands of tokens. When the user explicitly asks to change it, edit the template and read `references/ux-contract.md` first: every item there must survive the change.

### 8. Validate before sharing

Run:

```bash
uv run --script <skill-dir>/scripts/validate_interview_helper.py <output-dir>/<candidate>-interview-helper.html
```

Fix all validation errors before returning the artifact.

The validator checks Background presence and career coverage against the full
inventory separately from HTML structure and JavaScript syntax. Verify inventory
extraction against the full sources; a passing comparison cannot detect entries
already lost during extraction. Report approved-plan preservation, Background
presence, career coverage, and visible rendering as separate results.
Then use an available browser preview to
open Background and verify that the portrait and available career data are visible,
not merely embedded in CONFIG. If browser inspection is unavailable, state that
rendering was not verified; static/data checks alone are not visual verification.

### 9. Return only the useful deliverable

Open the generated HTML in the host's preview when available and return a direct clickable file link; attach it when the host supports file delivery. Add a short summary of what was adapted for this candidate, and quote the approval record the generator printed. When step 5 skipped the approval prompt, list the `new` questions you added.

Do not dump the full interview spec into chat unless the user asks for it.

## Resources

- `references/spec-schema.md` - JSON contract used by the generator.
- `references/plan-review.md` - progressive drafts, bundled visual review, and compact feedback application.
- `references/interview-design.md` - question selection, time allocation, deep-dive patterns, and signal wording.
- `references/candidate-insights.md` - automatic factual background, source attribution, and optional interpretations.
- `references/ux-contract.md` - stable HTML/UX contract; read before changing the template.
- `assets/interview-helper-template.html` - stable HTML/CSS/JS UI shell.
- `assets/interview-review-template.html` - fixed offline preparation editor; inject data without rewriting it.
- `scripts/review_plan.py` - render the preparation reviewer and apply exported changes.
- `scripts/generate_interview_helper.py` - injects an approved interview spec into the template.
- `scripts/validate_interview_helper.py` - validates the finished standalone HTML.
