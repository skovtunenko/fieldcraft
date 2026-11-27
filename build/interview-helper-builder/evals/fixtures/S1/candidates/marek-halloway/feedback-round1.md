# Round 1 feedback - Marek Halloway

Interviewer: Hollis Brandt (screening round)

**Strong on agent tool calling.** He walked through the triage assistant's
tool schemas, retries with backoff, idempotency keys on the notes writer, and
the timeout fallback to human handoff. Concrete, and clearly his own design.
Honest when he did not know something.

**Evaluation does not match the CV.** When I asked how the triage assistant
was evaluated, he could not name a single metric the team tracked. He said
"we reviewed outputs with the adjusters" and that "QA owned the numbers". No
mention of a golden set or release gate.

Process decomposition came up only briefly before we ran out of time; not
enough to judge. Communication was clear, though some answers ran long.

Recommendation: proceed to the technical round. Worth checking who actually
built and owned the evaluation.
