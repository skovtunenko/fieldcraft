# Candidate Insights

`candidateProfile` supplies the live page's `Candidate background` automatically
when a readable CV or substantive professional context is available. The interviewer
reads it before the call and glances back at it mid-call, so every entry must
land in one read. The page keeps it out of progress and the analysis prompt.

```json
"candidateProfile": {
  "portrait": "According to the CV (cv.md), a platform engineer who grew from support into owning a payments runtime. Interpretation: the described work suggests implementation depth.",
  "timeline": [
    {"from": "2021-03", "to": "now", "org": "Acme", "role": "Staff Engineer", "scale": "Payments runtime, 40M checkouts/month, team of 6", "source": "CV · Acme"},
    {"from": "2020", "to": "2021-06", "org": "Beta", "role": "Contractor", "scale": "Kafka migration, 3 services", "source": "CV · Beta"}
  ],
  "standouts": [
    {"text": "Cut checkout p99 from 900 to 180 ms at Acme", "source": "CV · Acme 2021-2023"}
  ],
  "inconsistencies": [],
  "probes": [
    {"text": "Round 1 found Kafka depth shallow; CV claims a Kafka migration lead", "source": "Round 1 feedback vs CV", "ask": "Walk me through one Kafka failure you debugged yourself. → 2.1"}
  ]
}
```

A required background needs a nonempty factual `portrait`. Add only supported
timeline and list entries; all lists may be empty. An optional legacy profile
must hold a portrait or at least one entry. A timeline entry needs `org` and `from`;
place undated work in `additionalExperience`, preserving its source and explaining
why it is outside the dated timeline.

## Career coverage

Keep `candidateCareer` as the complete extracted source inventory in the draft
and final spec. Build it from the full CV or transcription, including earlier
experience, rather than the short card, preparation facts, or opening question.
Each entry has `org`, `source`, and any supplied `role`, `from`, `to`, `dateNote`,
and `scale`. Omit unknown dates; use `dateNote` for qualified or unparseable date
wording, and `to: "now"` only for explicitly current work. Use `[]` when feedback
or other available sources supply no career positions.

Default to all dated positions in `candidateProfile.timeline` when there are at
most 12. For more than 12, put the newest 12 fully dated entries on the timeline
and the rest in `candidateProfile.additionalExperience`. Undated or qualified-date
entries also go there. Each additional entry copies its inventory identity and
has a nonempty `reason`, displayed alongside its details and source. If a selective
timeline is justified, account for every other position there with its reason;
the page labels the timeline as selected whenever additional entries exist.

Coverage compares organization/engagement, role, original dates, source, and
date qualification, exactly once across both displays. Preserve overlapping dates
as supplied; an overlap alone establishes neither full-time status nor wrongdoing.
Mark parallel work only when the source establishes it. Review the inventory
against the raw sources: code validates inventory-to-profile coverage, not whether
extraction captured the complete CV. Source reconciliation needs no new approval.

## Sources

Draw on this candidate's material only: the CV, prior interviewers' feedback,
the interviewer's own remarks in chat, and the confirmed card and requirements
matrix. Start from the matrix evidence and any `candidateFacts` and
`candidateInsights` already in the draft.

Set `candidateBackgroundRequired: true` as soon as professional sources are
available, even when the preparation arrays are absent. Populate the profile
without an insights request or a second approval of readable sources. For prior
feedback alone, write an attributed overview of that interviewer's observations;
leave the career timeline empty unless that source supplies career dates. With no
professional sources, set the flag to `false` and omit the profile.

CV statements remain candidate claims, prior feedback remains the interviewer's
observation, and interpretations remain tentative. Attribute the portrait within
its text (for example, "According to the CV (cv.md) ...; Round 1 feedback notes ...").
Each career row also displays its own `source`. Preserve qualifiers and approximate dates; optional
missing details do not block the supported profile. Clarify only a specific
unreadable part, material contradiction, or decision the sources cannot resolve.

Every entry's `source` points to where the interviewer can check it:
`CV · Acme 2021-2023`, `Round 1 feedback`, `Your remark`, `CV vs Round 1 feedback`.
Mark an interpretation as one in the text ("reads as", "suggests").

## What each part holds

- `portrait`: 2-3 sentences, at most 60 words. Summarize supported professional
  experience with source attribution. Include motivation or a characterization
  only when supported, marking any interpretation explicitly.
- `timeline`: the career at a glance, rendered as bars on a shared year axis.
  One entry per role, engagement, or significant own project, newest first, at
  most 12. `from` and `to` are `YYYY-MM`, or `YYYY` when the CV gives only the
  year; `to` is `now` only for explicitly current work. An unknown end date is
  not evidence of current work: describe that role outside the timeline. Copy dates as the CV states them, so
  overlaps and gaps stay visible. `scale` says how big the work was in about 12
  words, with numbers where the CV has them: team size, users, sites, money,
  systems. Mark work done alongside a main role (consulting, side projects, an
  own lab) `"kind": "parallel"` only when the source says it was parallel.
- `additionalExperience`: all career entries outside the dated timeline, without
  a count limit. Copy their inventory identity, optional scale, and the reason for
  placement here. This list is independent of the five-entry insight lists.
- `standouts`: what is interesting or unusual. A rare skill combination, steep
  growth, an unusual domain, an achievement with numbers.
- `inconsistencies`: what is strange or does not add up. Overlapping dates, a
  title larger than the described scope, a technology listed but absent from
  every role, an unexplained gap, prior feedback contradicting the CV, claims
  with no outcomes. Name both sides with their sources. Give each side's full
  sentence its most charitable plain reading, the one that lets both hold (a
  sum, a subset, a rounded figure), and list the entry only when no such
  reading exists. Several innocent explanations usually exist, so the `ask`
  is a neutral question that lets the candidate explain.
- `probes`: points worth highlighting or probing to form an impression. Claims
  worth verifying, ownership, motivation for the move, how they talk about past
  teams. Add an `ask` when a ready question helps.

An `ask` in any list ends with `→ <question index>` when that question's ask or
one of its follow-ups asks the same thing; a question on the same topic is not
enough. The page then repeats the entry on that question's card, so the
interviewer meets it at the moment of asking; the index must exist in the spec.

Each list holds at most 5 entries, most decision-relevant first. Each `text`
has about 15 words or fewer and opens with its subject. An `ask` is one sentence
the interviewer can say aloud as written. Leave a list empty when the material
gives nothing for it.

Write about professional evidence only. Age, nationality, family, health,
religion, and other protected traits stay out of every entry.

All text is in the spec's content language.

## Chat summary

After gate 1, the workflow shows this summary in the conversation language; later
it serves any summary or correction request. It introduces no approval gate and
does not ask the interviewer to revalidate readable CV facts. The same rules as
the profile apply: sources, charitable reading, list limits, no protected traits.
Before the questions exist, write each `ask` without `→ <index>`:

```text
Candidate insights - <candidate>
Portrait: <portrait>
Stands out:
1. <text> (<source>)
Doesn't add up:
1. <text> (<source>)
   Ask: <ask>
Worth probing:
1. <text> (<source>)
   Ask: <ask>
```

Leave out empty parts. Add a newest-first timeline (`<from> - <to> · <org> · <role> · <scale>`) only when the interviewer asks for it.
