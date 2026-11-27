# Prepared questions - Marek Halloway (rough)

1. Triage assistant runtime: walk me through one claim from intake to
   decision. What owns state? What is deterministic vs model-driven? (~10 min)
2. Evaluation: how did you evaluate the triage assistant? Which metrics, who
   defined them, what blocked the last release? (~8 min)
3. What is the difference between RAG and fine-tuning? Define both.
4. Peter asks this: 15-min live coding - write a Python wrapper that retries a
   flaky tool call with backoff and an idempotency key.
5. Give him a messy process (subrogation referral) and ask for an
   engineer-ready spec: steps, exceptions, validation rules, when a human
   steps in. (~10 min)
6. PII: what goes into prompts and logs, what gets redacted, how long do you
   keep traces? (~6 min)
7. Why leave Tessaline after five years?
8. Retrieval over the policy docs: chunking, access filtering, what happens
   when a policy is amended mid-claim? (~8 min)
9. Team: how do you run design reviews? Last design you rejected, and why?
   (~6 min)
10. Tool-call retries and timeouts: how did you design them? (~5 min)
