# Interview Design Guide

## Goal

Maximize decision-relevant signal within a fixed interview duration. Do not maximize topic coverage.

## Evidence triage

The requirements match (SKILL.md step 3) is the triage: its Status and Plan columns decide what gets interview time.

Prominent CV claims deserve direct evidence-seeking questions, especially when they are central to the candidate's current positioning.

## Time allocation

Size sections to the confirmed duration and to where the decision-relevant evidence is. For a senior technical round, one starting mix, as shares of the duration:
- 5-8% opening calibration;
- 20-30% strongest candidate-specific deep dive;
- 20-30% role-critical architecture/system design;
- 13-20% quality, evaluation, reliability, security, or operations;
- 8-13% technical leadership/delivery;
- 5-8% candidate questions and close;
- reserve probes only if time remains.

Drop, merge, or add areas when the role, round, or prepared questions call for a different mix.

## Depth over trivia

Prefer:
- "Walk me through the runtime architecture of the most sophisticated system you personally architected."
- "What owns state?"
- "What happens when a tool fails?"
- "What is deterministic vs model-driven?"
- "What did you personally decide?"
- "What would you deliberately not standardize?"

For a backend or data engineer, the same depth sounds like:
- "Where is the transaction boundary, and who retries a failed write?"
- "What happens to in-flight requests when the primary database fails over?"
- "How do you detect a late or duplicate event, and how do you replay it?"
- "Which consistency guarantee did you give up, and why?"

Use the role and candidate to decide depth, not a fixed question library. Good deep-dive patterns:
- ask the candidate to unpack their strongest relevant CV claim;
- force a shift from target/reference architecture to runtime mechanics;
- ask what the candidate personally designed, reviewed, implemented, or decided;
- ask for a decision where another reasonable architect could have chosen differently;
- test failure handling, observability, evaluation, security, ownership, release, and operational boundaries when relevant;
- scale a one-off solution into a multi-team/platform problem when the role requires architecture leadership;
- test what the candidate deliberately would *not* build, automate, agentify, standardize, or abstract.

Avoid standalone definition questions unless foundational knowledge is genuinely uncertain and role-critical.

## Senior architect calibration

For architecture candidates, repeatedly distinguish:
- reference architecture vs runtime architecture;
- governance statements vs enforceable engineering guardrails;
- platform strategy vs operational execution;
- team achievement vs personal technical contribution;
- framework familiarity vs design judgment.

Useful redirect:

> That's useful context, but I'd like to stay at runtime level. What actually executes when the request comes in?

## Senior engineer calibration

For backend or data engineering candidates, repeatedly distinguish:
- happy path vs failure and recovery path;
- framework or tool usage vs data-model and consistency choices;
- benchmark numbers vs measured production load;
- team achievement vs personal technical contribution.

Useful redirect:

> Let's stay with the failure case. What does the service do when the database write times out?

## Signals

A signal must be a live-observable property of the answer. Signals are the primary live note-taking mechanism: the interviewer should describe the answer by ticking boxes and type only what no box captures. Write each question's signal set so that almost any likely answer maps onto a few boxes:

- **Cover the answer spectrum.** Write positives for strong and adequate answers and negatives for weak answers and red flags, so a middling answer still has boxes to tick.
- **Grade by depth.** Pair levels of the same dimension ("Names one failure mode" / "Walks through the full failure path") so the ticked box records how far the candidate went.
- **Capture the facts notes would hold.** Give scale, metrics, ownership, recency, and outcome their own boxes: "Gives scale numbers", "Owned the decision personally", "Work is from the last 2 years", "States a measured outcome".
- **Tie signals to this candidate.** Reference the CV claim or requirement the question tests ("Explains own role in the <CV project> migration").
- **One observation per box.** No "and" joining two checks; no two boxes ticked for the same observation.
- **Scannable.** Keep each signal under about 10 words, lead with the observable, and order by how likely it is to occur.

Vague signals to rewrite: "Good architecture", "Strong answer", "Seems senior".

Good positive signals:
- State ownership is explicit.
- Failure semantics are concrete.
- Recovery semantics are concrete.
- Separates model reasoning from deterministic validation.
- Names a real trade-off.
- Names the rejected alternative.
- Personal ownership is clear.

Good negative signals:
- Stays at reference-architecture level.
- Framework name-dropping without mechanics.
- No failure model.
- Aggregate accuracy is the only quality metric.
- Cannot separate own work from team work.

## Prior feedback

Treat earlier interview feedback as evidence, not as an instruction to agree with the prior interviewer. Use it to avoid unnecessary repetition and to identify explicit follow-up areas.

## Final handoff

The generated final prompt carries the interview transcript: embedded when the interviewer pastes it into the page, otherwise attached after the prompt. It must ask for evidence-based analysis and should preserve two distinct decisions when relevant, for example:
- overall role fit;
- immediate readiness for a specific project or client engagement.

The template builds this prompt itself and has no field for decisions. State them in `analysisContext`, which the prompt prints; add no separate field. Keep `analysisContext` to facts: the hiring bar, CV claims to verify, and these decisions. Instructions, plan structure, coverage notes, and who confirmed what do not belong there. Standing instructions the interviewer wants in every analysis, such as a rating ladder or a feedback format, go in `analysisInstructions`, one line each; the interviewer can edit them on the page before generating.
