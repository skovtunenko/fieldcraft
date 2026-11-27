# Interview Spec Schema

The generator consumes a UTF-8 JSON object with this shape.

The same shape is used progressively during preparation. Drafts may omit unknown
fields and enrichment; see `plan-review.md` for draft checks and visual review.
The final generator still requires the complete contract below.

## Required top-level fields

```json
{
  "candidate": "Candidate Name",
  "role": "Enterprise AI Architect",
  "durationMinutes": 60,
  "subtitle": "60-minute technical round - focus on ...",
  "candidateBriefing": [
    "The role: what the team builds and for whom.",
    "Structure: a system you built, a design scenario, your questions.",
    "What we expect: your own decisions and failure cases, not definitions."
  ],
  "analysisContext": [
    "Hiring bar: ...",
    "CV claim to verify: ..."
  ],
  "analysisInstructions": [
    "Optional standing instruction for the analyst, one line each"
  ],
  "outOfScope": [
    "Low-value topic one",
    "Low-value topic two"
  ],
  "sections": [],
  "scoreDimensions": []
}
```

Values in these examples are illustrative: `role` can as well be `Senior Backend Engineer` or `Data Engineer`. `durationMinutes` is the confirmed duration, and sections follow the approved skeleton.

`candidateBriefing` is optional: up to 4 short strings the interviewer says to the candidate, shown at the top of the page as checkboxes the interviewer ticks once said; ticks never reach the analysis prompt. Omit it or leave it empty when nothing is known; the block is then hidden.

`interviewDate` is optional: the interview date as `YYYY-MM-DD`, for example `"2026-10-14"`. The page appends it to the heading and the browser tab title (`Candidate - Role · 2026-10-14`). Omit it when the date is unknown; the generator rejects any other format.

`candidateBackgroundRequired` is a boolean set during source intake: `true` when
a readable CV or substantive professional context (including prior feedback alone)
is available, `false` otherwise. Preserve it in draft, approved copy, and final
spec. Older specs may omit it. A `true` value or nonempty `candidateFacts` or
`candidateInsights` (or a nonempty `candidateCareer` inventory) requires
`candidateProfile` with a nonempty factual `portrait`;
`false` cannot override preparation evidence. The generator and HTML validator
reject a missing or empty required background with a completeness error.

`candidateCareer` is the full extracted career inventory, independent of the brief
candidate card: a list of `{org, source, role?, from?, to?, dateNote?, scale?}`.
Professional context requires this field; use `[]` when no career entries are
supplied. Read the full sources, including earlier experience, before populating
it. Dates retain their source precision; omit unknown values and put qualified
date wording in `dateNote`. `to: "now"` means explicitly current work.

Every inventory identity (`org`, `role`, `from`, `to`, `source`, `dateNote`) must
appear exactly once across `candidateProfile.timeline` and
`candidateProfile.additionalExperience`. Both must preserve those fields exactly;
additional entries also need a nonempty `reason`. Missing, extra, changed, and
duplicate identities fail generation and embedded-spec validation. Timeline
entries need explicit `from` and `to` and no date qualifier; unknown or qualified
dates belong in additional experience. Up to 12 dated entries appear on the
timeline by default; any remainder stays visible with reasons, without a count
limit. Selected timelines are labelled. A legacy spec without professional-context
indicators may omit the inventory; its career coverage is explicitly unverified.
Legacy profiles without inventory retain their former timeline syntax, with coverage
explicitly unverified. Code verifies the inventory, not extraction completeness
against the raw CV.

`candidateProfile` is created automatically from those sources: an object with a `portrait` string, a
`timeline` list of `{from, to, org, source, role?, scale?, kind?}` (at most 12;
dates `YYYY` or `YYYY-MM`, `kind` is `job` or `parallel`), optional
`additionalExperience` with the inventory entry shape plus `reason`, and
`standouts`, `inconsistencies`, and `probes` lists of `{text, source, ask?}`, at
most 5 entries each; see `candidate-insights.md`. The page shows it at the top
of the `Candidate background` block, above the out-of-scope topics,
and keeps it out of the analysis prompt. The generator rejects an empty profile,
a longer list, an entry without text or source, an `ask` ending in
`→ <index>` that names no question index in the spec, and a timeline entry
without an org, with a malformed date, or ending before it starts. Attribute
portrait claims in its text and retain CV claims versus prior observations and
explicit interpretations under `candidate-insights.md`. Include only supported
timeline rows and list entries; feedback alone can yield a portrait and empty
lists. With no professional sources, omit the profile. Readable supplied evidence
requires no separate profile approval.

`language` is optional: the content language tag, `"en"` by default, for example `"ru"`. It sets the page's `lang`; the generator and validator reject Cyrillic descriptive content only on English pages. The top-level `candidate` name keeps its original script. The page's own controls stay English.

All descriptive strings must be in that language. The approved copy must have the same `candidate` and `role` as the final spec; missing identity fields also fail generation.

## Section

```json
{
  "id": "1",
  "title": "Opening calibration",
  "minutes": "5m",
  "meta": "Target: 5 minutes. ...",
  "coach": "Time-box background answers ...",
  "questions": []
}
```

Use short stable IDs. The empty `questions` list above is a placeholder: every section needs at least one question. `minutes` is a string containing a positive finite number of minutes with an optional `m`, or `"if time"` for reserve sections. Draft approval and final generation reject zero, negative values, unknown reserve labels, and trailing text. The generator requires the numeric minutes of all sections (`"15m"` counts as 15; `"if time"` does not count) to sum to `durationMinutes`.

An optional section `index` holds its display number after reordering; the live
page uses it in headings, navigation, and the handoff, falling back to `id` for
older specs. IDs stay stable while section and question display indices follow
the approved order.

Optional preparation metadata survives enrichment: section `requirementIds` is
an array of matrix IDs; question `origin` is `prepared` or `new` and
`estimatedMinutes` is a positive number when an estimate was supplied. The optional
top-level `deepestProbes` array lists the plan's most important probe topics.
The optional top-level `requirements` array lists the matrix as unique
`{id, text}` entries; the reviewer reports which of them the kept sections still
test. The live page uses this same matrix for role coverage.

Each enriched question has `requirementIds`, an array of the matrix IDs that
its wording directly tests; `[]` means none. Its IDs must belong to its section.
The generator rejects duplicate IDs, unknown links, and links outside the section.
The approved matrix and section links stay unchanged during enrichment; approved
question links also stay unchanged when already present.

Older specs may omit the matrix or question links. Without the matrix, live
coverage is hidden. With only section links, coverage shows `Section links only`
and never treats those links as evidence for individual questions.

Optional `candidateFacts` and `candidateInsights` arrays hold `{text, source}`
entries for preparation. Facts summarize supplied claims or prior observations;
insights are explicitly tentative interpretations to test. Every entry names its
source, unknown entries are omitted, and both arrays survive enrichment. The
reviewer shows them separately; they do not populate the live Background.
Carry their supported professional content into `candidateProfile` for that page.

## Question

```json
{
  "id": "q1",
  "index": "1.1",
  "title": "How hands-on are you today?",
  "purpose": "Critical calibration for every later technical answer.",
  "ask": "Before we go deeper ...",
  "followups": [
    {
      "text": "What did you personally touch ...?",
      "listenFor": "Recent implementation-level work",
      "warnIf": "Personal ownership is unclear"
    },
    "Which decision would you make differently now?"
  ],
  "positives": [
    "Recent implementation-level work",
    "Can name concrete low-level decisions"
  ],
  "negatives": [
    "Stays at strategy level",
    "Personal ownership is unclear"
  ],
  "cue": "Optional interviewer redirect or exit phrase."
}
```

`cue` is optional. `followups` may be empty. Positive and negative signals should be observable and checkable during the answer; the generator requires at least 8 positives and 6 negatives per question.

A follow-up is a string or a probe object. A probe object has `text` and at
least one of `listenFor` and `warnIf`. `listenFor` is an exact string from the
question's `positives`: the answer to this follow-up shows that signal.
`warnIf` is an exact string from the question's `negatives`: the answer to this
follow-up can show that signal. Each signal pairs with one follow-up at most.
The page shows the pair in one probe row: the follow-up keeps its rating, and
the paired positive and negative signals each get a checkbox.
Signals without a pair stay in the signal panels. Pair a signal only when one
follow-up elicits it; leave signals that apply to the whole answer unpaired.
The generator rejects an unknown field, an unknown or reused signal, a probe
without a pair, and a repeated follow-up text.

## Score dimension

```json
{
  "key": "agenticDepth",
  "label": "Agentic runtime depth"
}
```

For a backend engineer, a matching dimension is `{"key": "failureHandling", "label": "Failure handling and data consistency"}`.

Use 5-9 dimensions. Prefer role-specific dimensions over generic categories.

## Analysis prompt behavior

The generated HTML automatically produces a transcript-analysis prompt after the interview. It includes:
- the assessment context from `analysisContext`;
- only marked questions and sections (a skip or Done alone does not count), each question with its title, `purpose`, and `ask` text, which the task marks as planned wording to match by meaning;
- rated follow-ups, with ticked paired cues on the same line (`; heard: "..."`, `; observed: "..."`), and rated positive signals, each with its meaning and any reason chips spelled out (`Follow-up "...": − (weak answer; no specifics, buzzwords)`, `Positive signal "...": mentioned, shallow (±)`), and observed negative signals;
- overall question signals without a time (`Red flag` marks a disqualifying observation);
- the time each mark was set, as elapsed interview-timer time `@ 12:40` (no wall-clock time);
- notes, if any;
- flagged moments, when any: each flag's note (or `(no note)`) and its time, in its own block;
- final scorecard entries that the interviewer actually selected;
- provisional decision and confidence when selected;
- previous interviewer feedback, when pasted into the page, in its own block framed as another interviewer's opinion;
- the transcript, when the interviewer pasted one into the page.

Each part sits in its own XML tag; interpolated text is XML-escaped.

Unmarked sections and questions are omitted, and so are unrated follow-ups, unmarked signals, and requirement coverage. The prompt never lists what was not marked.

`analysisInstructions` is optional: single-line instructions that the page adds to its default analysis task before the output and language lines, such as a company rating ladder or a required feedback format. The interviewer can still edit the whole task on the page. Put facts in `analysisContext`, not here.

`analysisContext` holds facts the analyst needs and cannot get from the transcript: the hiring bar, CV claims to verify, and decisions the feedback must answer. Do not put instructions, plan structure (section or question counts), coverage notes, or who confirmed what into it: the template writes the task itself, and these lines point the analyst at content that was not marked.

## Generation stamp

The generator stamps the page header with the generation time in local time with UTC offset, for example `Generated 2026-10-11 14:32 +02:00`. It is not a spec field. Pass `--generated-at <ISO-8601 datetime with offset>`, such as `--generated-at 2026-10-11T14:32:00+02:00`, to reproduce an exact stamp.
