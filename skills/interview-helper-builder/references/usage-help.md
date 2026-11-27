# Usage help

Explain the skill to the interviewer in the conversation language. Use the current
Workflow in `SKILL.md` as the authority for fields, gates, defaults, and output
names. Start with the practical result, then cover the following in plain language.
Answer a narrow usage question directly; give the full guide for a general help request.

## What to prepare

Distinguish the minimum context from optional material:

- Minimum: candidate, target role, interview duration, hiring expectations, and
  candidate experience. A CV and job description can supply the context; a pasted
  summary also works. The agent gathers what is available and asks for gaps.
- Optional: prior-round feedback, prepared questions or topics, their time
  estimates, question owners and panel members, employer, role pitch, date, and
  requested content language. Prepared questions may be absent; duration has no
  default. Page content defaults to English while the conversation can use another
  language; the interviewer can request a different content language.
- Files may be text, screenshots, PDF, or DOCX. Connected sources are used only
  under Workflow's source-access rules. The interviewer supplies context rather
  than authoring JSON or running the bundled scripts.

## How the flow works

Explain the checkpoints in order: confirm the candidate card and the agent's
reading of the role (position, hiring bar, what to look for, red flags), read the
short candidate portrait with what stands out and what does not add up, supply
prepared questions or ask the agent to generate them, confirm the requirements
match, then review the proposed structure. Already satisfied checkpoints are
skipped under Workflow's rules. Readable CV or professional context automatically
supplies a sourced factual Background; it needs no separate insights request or
profile confirmation. The agent asks only about unresolved specifics. Prior
feedback alone yields an attributed overview; missing sources yield no invented
career. Structure and requirements approval still apply.
The career history is reconciled with the full source list, including earlier
roles. Entries outside the 12-row timeline, including undated work, remain visible
with their sources and placement reasons; they are not silently dropped.

The visual review lets the interviewer fold sections, reorder them from the
sidebar or main handles, move questions, adjust timing (also by resizing timeline
blocks), request additions or removals, and leave comments. A coverage card shows
which role requirements the kept sections still test. **Copy review prompt** sends nothing itself: paste
its text into the agent chat to request revisions. The agent applies the requests
in the same draft and regenerates the same review file. Draft, review, saved
feedback, and report paths are reused across rounds; the existing review page
provides the prior plan for change marks. Explicit chat approval of the revised structure is
separate; explain the existing exception for a complete user-supplied structure.
**Reset review** restores this file's original plan after confirmation, clearing
the current review's changes. It leaves source files and other saved interviews intact.

## What comes out

Distinguish the review HTML used during preparation from the final offline HTML
used during the interview. Explain that the agent also keeps the JSON spec and
approved-plan copy for regeneration; their paths follow the user's output location
or Workflow's default. The user-facing result is an openable page with a direct
link, not a JSON editing assignment.

During the interview, start the timer with the recording, rate observations and
take notes; **Done** requires an overall question signal. Browser autosave keeps
working state, and **Save HTML With Comments** creates a portable backup. After
the round, use **Generate analysis prompt**, then **Copy prompt** and paste it into
an AI chat; paste the transcript into the page or attach it in that chat. The copied
prompt is a handoff for analysis, not an analysis already performed by the page.

## How to start

Show `$interview-helper-builder help` for this mode and one short build-request
example that names a role, duration, candidate context, and desired content
language. Reuse supplied context when present. Help-only finishes without asking
the interviewer to confirm a candidate card or supply interview data.
