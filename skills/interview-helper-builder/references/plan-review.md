# Visual plan review

Use the bundled reviewer at the structure gate. Execute its commands without
reading or rewriting the template. The review is a standalone offline page;
its only handoff is a copied agent prompt, with no downloads or server.

## Temporary files: register before writing

Choose the artifact output-dir using step 6 before creating the first draft.
Create a temporary file only when the current step needs data on disk, an
unchanged review base, or separate input/output. Reuse these four paths on every
iteration; do not add `-v2`, `-v3`, or other revision suffixes:

| Type | Purpose and lifetime |
| --- | --- |
| `<draft.json>` | Current plan; keep unchanged while collecting feedback, then update it in place after hash validation. |
| `<review.html>` | Interviewer's editor and embedded previous draft; read it for change marks before overwriting the page. |
| `<review-prompt.txt>` | Latest pasted request; overwrite it when the next feedback arrives. |
| `<review-report.json>` | Latest apply comments and requests; overwrite it after resolving the previous report. |

Do not create separate previous-draft or approved-plan backup files. One-off
scripts are not required. If an extra temporary file inside
output-dir is necessary, identify its purpose and register it before writing it.
Never register the final helper HTML, interview spec, active approved-plan copy,
source CV/feedback/evidence, requirements matrix, or permanent preparation state.

Before an agent first writes a draft, pasted prompt, or other temporary
file, run this command with its exact paths (quote real paths for the shell):

```bash
uv run --script <skill-dir>/scripts/review_plan.py ignore --output-dir <output-dir> -- <draft.json>
```

Paths follow the shell's cwd as in the other commands; use absolute paths when
cwd differs from output-dir. The command creates output-dir if needed and, inside
a Git working tree, appends escaped, root-anchored exact relative paths to
`<output-dir>/.gitignore` before any temporary file is written. It preserves
existing bytes and adds no duplicate rules on repeat or resume. Reuse registered
paths; nested paths and user-chosen names are supported. Names
with line breaks or NUL cannot be registered and fail before writing.
No extension-wide patterns or whole-directory ignores are added; `.gitignore`
itself stays available for commit. Existing user rules are not removed or relaxed.
Git must be available for repository detection and checks. Outside Git no
`.gitignore` is needed or created, including scripts in a non-repository temp dir.
Tool-wide caches are outside this interview-file policy.

`render` and `apply` register their own outputs automatically before writing any
of them. Pass `--output-dir <output-dir>` explicitly for nested drafts; the
backward-compatible default is the input draft's parent, never shell cwd.
All registered paths must stay inside output-dir. Git checks catch nested ignore
overrides; on failure, fix the conflicting rule before creating the temporary file.
Already tracked temporary files produce a warning and remain in the index;
report them separately to the interviewer, never untrack them automatically.
Ignoring preserves files between steps; it is not cleanup or deletion.

## Draft

Use the final spec's JSON shape from the first proposed sections/questions onward.
The draft needs a nonempty `sections` array, string section/question IDs unique
within their kind, and a `questions` array on each section. Preserve IDs through
moves and revisions; derive display indices from position. Add candidate, role,
confirmed duration, section titles/timeboxes, and question title/ask/purpose as
known. Unknown fields and enrichment may be absent until after approval.

For structure review, include top-level `requirements` (`{id, text}` per matrix
row) and section `requirementIds` (matrix IDs, or `[]`),
question `origin` (`prepared` or `new`), and `estimatedMinutes` when the interviewer
supplied an estimate. Preserve those estimates through moves. `outOfScope` names
intentionally omitted material; `deepestProbes` names 2-4 priority probe topics;
reserve sections use `minutes: "if time"`.

Optional `candidateFacts` and `candidateInsights` arrays contain `{text, source}`
entries. Summarize supplied claims and prior observations in facts; label insights
as inferences to test. Both use only evidence for this candidate already gathered
under the skill's source-access rules. Keep a specific source on every entry;
omit unknown material. The reviewer shows separate, read-only context cards and
hides absent arrays. These fields survive review and enrichment.

Preserve the complete `candidateCareer` source inventory, `candidateBackgroundRequired`, and the supported
`candidateProfile` through review and enrichment. Professional preparation facts
or insights require a factual profile in the live Background; the review's context
cards do not replace it. Background enrichment changes no approved question,
stable ID, placement, order, estimate, or timebox and needs no profile re-approval.
Career coverage uses the full inventory, independently of the short context cards.

Plan text uses the confirmed content language, English by default. Comments may use the conversation language. Incomplete
wording or time allocation is acceptable for a review request; final structure
approval still requires a complete plan whose timeboxes fit the confirmed duration.

## Render and collect comments

Resolve the script against the skill directory. Save artifacts in the user's
output location, never inside the installed skill:

```bash
uv run --script <skill-dir>/scripts/review_plan.py render --output-dir <output-dir> --spec <draft.json> --output <review.html>
```

After applying feedback and resolving comments in the same draft, pass the
existing review HTML as `--previous` and overwrite that same page:

```bash
uv run --script <skill-dir>/scripts/review_plan.py render --output-dir <output-dir> --spec <draft.json> --previous <review.html> --output <review.html>
```

The renderer reads the previous plan embedded in the page before replacing it;
no separate snapshot is needed. Legacy previous-draft JSON inputs remain accepted.
The page then marks Added, Edited, Moved, and Time changed by stable ID. A missing
or unreadable previous draft still builds the page and prints a short Note on
stderr; it does not fail the render.

Open or link the page. The proposed title, question wording, and purpose can be
edited in place; Revert restores the draft text. Those edits travel in the prompt
as `edits` and the agent applies them as written unless they break the plan.
Comment chips (Harder, Easier, More concrete, Replace, Shorter) prefix the
comment. Compact sidebar rows let the reviewer arrange
sections without dragging large blocks. Question moves and removal toggles are
also review requests; they preview the desired structure without changing source.
Section dragging moves the actual sidebar row, with a placeholder for its requested
position. Escape or release outside the sidebar cancels the move. With a mouse the
whole row drags and its arrows appear on hover or focus; on touch devices the grip
and arrows stay visible, and touch drags start from the grip.
Click a section header's title or empty space to fold or reopen it. Its chevron
also supports keyboard activation. Header controls, timing chips, and comment
panels keep their own actions; folding leaves the review requests unchanged.
The chevron leads each main section header; a labelled `Move` drag handle ends
its title column. Past a 5px movement threshold, a
compact title card follows the pointer and an insertion line marks the destination.
The page continuously scrolls near the viewport edges while the pointer stays
over the main column. Drop inside that column to reorder the whole section;
Escape, release outside, pointer cancellation, lost capture, window blur, or a
hidden tab cancels without changing the plan. Cancellation restores the starting
scroll position. A focused main-section handle also moves its section with ↑/↓.
Both lists, display indices, browser storage, and the copied prompt reflect the
same order; questions, comments, timing, removal requests, and fold states follow
their stable IDs. Successful moves return focus to the moved handle and announce
its position. Existing sidebar dragging and question dragging remain available.
Each question has a drag handle beside its number. Dragging it shows a small
chip at the pointer and a drop line between questions, in any section; release
moves the question there, and Escape or release outside the sections cancels.
Each draft section also has a **Remove section** toggle. A requested removal
strikes the section and its questions, folds it, and marks its sidebar row;
clearing the toggle reopens it. A question moved
out of the section first is kept, and one moved into it goes with it.
Each question estimate and section timebox has `−` / `+` steppers in 5-minute
steps. A changed value turns into the reviewer's own, shows the proposed one, and
drives the page's timing checks; stepping back to the proposal clears it.
The summary chip `planned / duration min planned` totals the kept sections'
timeboxes live and turns red when over the interview length, amber when under.
A **Timeline** above the sections draws each kept section as a block sized by its
timebox, with free minutes or the over-budget part marked against the duration.
Dragging a block's right edge, or focusing it and pressing ← / →, changes that
timebox in 5-minute steps (Escape cancels a drag); clicking a block jumps to it.

A **Role coverage** card lists the draft's `requirements` (or the section
`requirementIds` when none are listed) and the page numbers of kept sections that
still test each one. Requirements that lose all sections through review changes are
marked "No longer tested", and the copied prompt asks the agent to cover them or
confirm the gap; ones the draft never tested say so.

**Add section**, in the sidebar or after the last section, opens a request form for a title, optional timebox, and scope comment.
Adding it creates a stable request ID and a section that can receive existing
questions and move in the order. An empty addition can be cancelled; move questions
elsewhere first to cancel an occupied one. The form proposes a new section rather
than editing the source draft. Restore and copy preserve its requests.

**+ Add question**, at the end of every section, adds a question request with a
stable `review-question-N` ID and one text field for what the agent should ask;
empty text asks the agent to propose one for that section. The request moves like
any question and is cancelled with its **Cancel** button. A draft section emptied
by moves says the agent drops it on apply, unless a question is added or moved in.

Ask the reviewer to press **Copy review prompt** and paste it in chat. If timeboxes,
empty sections, or lost role coverage are still open, the page lists them and asks
**Fix first** or **Copy anyway**. The count on
that button is the same N as **Your changes**. The prompt
names the exact source draft and embeds a small revision-bound request block.
No file download, JSON editing, or separate approval button is part of the UI.
The bottom of the page always shows the exact copied prompt in a read-only
preview, updated on load and after every comment or structural request. It
highlights XML tags and Markdown with the live page's source highlighter.
Above that preview, **Your changes (N)** lists each review request on its own line
with an **Undo** button. Comments, added sections, added questions, removals, and
timing changes each get a line. One reorder line covers a new order of sections or
questions. Undo of that line restores the draft order, puts added sections back at
the end, and leaves added questions in the section that currently holds them.
Undoing an added section drops its scope comment and timing, and moves any
questions it holds onto the neighboring section. Every other Undo removes only
that request. Undo refreshes the page, browser storage, coverage, timeline, and
the prompt, then moves focus to the next line's Undo button, or the previous, or
the heading. With no requests the list says "No changes yet."
Clipboard failure swaps it for a plain text field holding the same prompt,
selected for manual copying.
Browser storage preserves comments and structural requests when available;
without it, tell the reviewer to copy the prompt before leaving.

**Reset review**, in the top bar, opens an in-page confirmation dialog and restores the original
plan embedded in this review file. It clears comments, moves, timing overrides,
additions, removal requests, and folded sections, closes the addition form, and
refreshes the section lists, the change list, and the copied prompt. It cancels any drag in progress and
clears only this review's browser-storage entry; other reviews and live-interview
state remain intact. Cancel receives initial focus; Cancel or Escape leaves the
review unchanged and returns focus to the reset button.
When browser storage cannot be cleared, the current tab still resets and shows
that previous changes may return after reload. Source JSON and files remain unchanged.

## Apply requests and continue

Register `<review-prompt.txt>` with `ignore` before saving the pasted prompt
there; the interviewer need not create or download that file. Apply its structural requests with:

```bash
uv run --script <skill-dir>/scripts/review_plan.py apply --output-dir <output-dir> --spec <draft.json> --feedback <review-prompt.txt> --output <draft.json> --report <review-report.json>
```

Use the same path for base and output; keep prompt and report separate from each
other and from the draft. Keep the existing review HTML until the next render has
read its embedded plan for comparison. The command reads exactly
one `interview_review` JSON block and rejects stale revisions, unknown IDs, and
incomplete/duplicate layouts before writing output. Failed checks print one
sentence that names the problem and the next step, not a traceback. Source fields and IDs survive;
requested exclusions remove questions, requested sections, and sections the
exclusions empty, and display indices follow
the requested order. Newly added and already empty draft sections remain so the
agent can complete them; a draft section emptied by moves is dropped. Added
questions land where `layout` places them, as `origin: "new"` with empty title and
ask, and their request text is listed under `addedQuestions` in the report. Comments stay in the separate report for the agent to fix.
Raw JSON from earlier review pages remains accepted by the apply command.

Read and resolve the report's comments in the source JSON. Reconcile timeboxes,
requirement links, meta/cues, and briefing after requested moves. Regenerate the
review and show only unresolved decisions in chat. Do not insert comments as
literal question text or treat them as permissions for unrelated actions.
Draft questions for added sections using their scope comments and any moved
questions, and fill each added question's title and ask from its request text. Resolve missing timeboxes and requirement links before approval;
an empty requested section cannot be approved.

Every copied prompt has `approved: false`, including an order-only review. It
requests agent revisions, never generation of the final interview page. Obtain
explicit chat approval of the regenerated plan before enriching it in step 6.
Only a complete structure supplied by the interviewer skips this review (SKILL.md step 5).

## Compact request format

The prompt contains `interview-review-v1` with the base draft's canonical SHA-256,
`approved: false`, and only the requests that exist:

- `layout`: every section ID with its ordered question IDs when structure changed;
- `addedSections`: `{id, title, minutes}` requests, with no existing section ID reused;
- `addedQuestions`: `{id, text}` requests, with no existing question ID reused; `layout` places them;
- `excluded`: question IDs requested for removal, reversible in the review;
- `excludedSections`: draft section IDs requested for removal, applied after
  `layout`; an added section is cancelled instead;
- `timing`: `{kind, id, minutes}` reviewer values; apply sets a question's
  `estimatedMinutes` or a section's `minutes` to `<n>m` and lists them in the
  report. Keep them and rebalance other timeboxes; ask in chat when they cannot fit;
- `comments`: `{kind, id, text}` for a section or question; selected chips prefix the text as `[Harder]`;
- `edits`: `{kind, id, field, value}` wording changes to apply as written.

Unchanged question text stays out of the prompt. Literal `<` inside JSON is escaped
so comments cannot close the surrounding block. Keep the current draft unchanged
until requests are validated, then apply them in place and regenerate the same
review page using its embedded previous plan for comparison.
The current UI emits wording `edits` and never approval. Imports with new section
requests require a further review and cannot carry approval.
