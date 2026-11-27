# Eval cases

## How to run

1. **Generate.** One fresh subagent per case. It receives only the path to
   `SKILL.md` and the case conversation, then the explicit invocation. It
   never sees this file. Save its raw output to
   `<runs>/<date>-v<version>/<case>.md` (`<runs>` is a results folder that you
   choose outside version control), and list every tool call it made
   besides reading `SKILL.md`.
2. **Baseline.** For C1–C3, a fresh subagent without the skill gets the same
   conversation and the baseline prompt. Save the outputs as anonymised A/B
   pairs; keep the key outside the grader's reach until grading is done.
3. **Grade.** A fresh subagent follows `evals/grader-prompt.md`. The authoring
   session does not grade.
4. **Record** verdicts, word counts, and limitations in
   `<runs>/<date>-v<version>.md`.

## Common rubric (C1–C4, C8–C13, and the language pairs of C1 and C8)

A case passes only when every common box and every case box passes.

- [ ] **Evidence gate**: every lens in the output has evidence in the
  conversation for its _Use when_ trigger; no `n/a` lines; no lens listed
  only to say it does not apply
- [ ] **Count and rank**: at most three candidates, best value for effort
  first; when none fired, one line says so and names the missing evidence
- [ ] **Plain form**: each candidate is prose tagged with its lens name
  (evidence → bigger version → first step and effort); no labelled field
  template (Builds on, Version, Cost, Missing, Unchecked), no mode label
- [ ] **Fact use**: every candidate starts from a decision, finding,
  constraint, number, or dead end from the conversation, not only a name
- [ ] **Swap test**: no candidate would fit another case's conversation
  unchanged
- [ ] **No repeats**: no candidate redoes finished work or a dead end; a
  departure from a decision is stated as such
- [ ] Depth, when present, names an outside judge that is not the model
- [ ] Range, when present, names methods to apply, not a voice to imitate
- [ ] **Prompts**: a ready prompt appears only for a step that belongs in a
  separate session, and names the material it needs
- [ ] **Close**: ends with one question about which candidate, if any, to
  start; no proposed work started; no tool call besides reading `SKILL.md`

## Baseline prompt (C1–C3)

Same conversation, then the user writes, in the conversation's language:
"How could I approach this task more ambitiously?"

## C1 — Plan, Russian, business deck

> Пользователь: Мне нужно к пятнице сделать колоду для квартального ревью
> (QBR) по нашему SaaS-продукту. Есть выгрузка из Stripe за 4 квартала
> (`stripe_export.csv`), дашборд Amplitude по активации и прошлогодний шаблон
> `qbr_template.pptx`. Руководство считает, что отток из-за онбординга.

Invocation: `$ambition-lens`

- [ ] Output prose is Russian; lens tags stay English
- [ ] Depth tests the onboarding assumption against `stripe_export.csv` or
  Amplitude raw data
- [ ] Depth ranks first: the deck rests on an unchecked leadership belief

## C1-en — Plan, English, business deck (pair of C1)

> User: I need to make a deck for our SaaS product's quarterly business review
> (QBR) by Friday. I have a Stripe export for 4 quarters
> (`stripe_export.csv`), an Amplitude activation dashboard, and last year's
> template `qbr_template.pptx`. Leadership thinks churn comes from onboarding.

Invocation: `$ambition-lens`

- [ ] Output prose is English
- [ ] Depth tests the onboarding assumption against `stripe_export.csv` or
  Amplitude raw data
- [ ] Depth ranks first: the deck rests on an unchecked leadership belief

## C1-uk — Plan, Ukrainian, business deck (pair of C1)

> Користувач: Мені треба до п'ятниці зробити презентацію для квартального
> рев'ю (QBR) нашого SaaS-продукту. Є вивантаження зі Stripe за 4 квартали
> (`stripe_export.csv`), дашборд Amplitude з активації та торішній шаблон
> `qbr_template.pptx`. Керівництво вважає, що відтік через онбординг.

Invocation: `$ambition-lens`

- [ ] Output prose is Ukrainian; lens tags stay English
- [ ] Depth tests the onboarding assumption against `stripe_export.csv` or
  Amplitude raw data
- [ ] Depth ranks first: the deck rests on an unchecked leadership belief

## C2 — Mid-course, English, flaky test

> User: `test_checkout_flow` in `tests/e2e/checkout.spec.ts` fails about 1 in
> 10 runs on CI.
> Agent: I added a `waitForSelector('#pay')` before the click; 20 local runs
> passed. Pushing now.

Invocation: `$ambition-lens`

- [ ] Depth names CI evidence (traces, repeated CI runs) as the judge, not
  more local runs
- [ ] Says whether the in-flight push should wait

## C3 — Retro, English, finished script, no skill

> User: Write a script that renames my photos in `~/Pictures/2025` to
> `YYYY-MM-DD_HHMMSS.jpg` from EXIF.
> Agent: Done: `rename_photos.py`, uses Pillow, ran on 1,204 files, 3 had no
> EXIF and were skipped.
> User: Great. I do this every year.

Invocation: `$ambition-lens`

- [ ] Steps aim at next year's run, not at files this run changed
- [ ] Altitude or Speed uses "I do this every year" as its evidence
- [ ] A proposal addresses the 3 files without EXIF

## C4 — Creative task, silent lenses

> User: Write a four-line birthday poem for my sister Ana, she loves hiking.

Invocation: `$ambition-lens`

- [ ] At most one candidate; Altitude and Range are absent
- [ ] No advice unrelated to the poem

## C5 — Another conversation requested

Empty conversation. Invocation: `$ambition-lens retro of my session yesterday
about the billing migration`

- [ ] Asks which session and waits for a yes before reading any transcript
- [ ] No tool call besides reading `SKILL.md`

## C6 — No task

Empty conversation. Invocation: `$ambition-lens`

- [ ] One question asking for the task
- [ ] No lens output

## C7 — Implicit mention

Query, in a real session, without invoking the skill: "Could we be more
ambitious with this rollout?" Expected: the skill does not load. Config
inspection: `SKILL.md` has `disable-model-invocation: true` and
`agents/openai.yaml` has `allow_implicit_invocation: false`.

- [ ] Both flags present

## C8 — Retro of a session a skill drove, Russian

> Пользователь: `$call-notes` по
> `calls/2026-10-15-acme-kickoff.txt`
> Агент: Готово: `insights.md` и `summary.md`, 14 инсайтов, 6 открытых
> вопросов.
> Пользователь: Спасибо. Потом я вручную выписал 3 решения, которые нам нужны
> от Acme до пятницы, и отправил команде.

Invocation: `$ambition-lens ретро`

- [ ] Prose is Russian
- [ ] Names a concrete change to `call-notes` that would have
  produced the 3 decisions the user wrote by hand
- [ ] Uses the 6 open questions or the 3 decisions as a fact

## C8-en — Retro of a session a skill drove, English (pair of C8)

> User: `$call-notes` on
> `calls/2026-10-15-acme-kickoff.txt`
> Agent: Done: `insights.md` and `summary.md`, 14 insights, 6 open
> questions.
> User: Thanks. Afterwards I wrote out by hand the 3 decisions we need from
> Acme by Friday and sent them to the team.

Invocation: `$ambition-lens retro`

- [ ] Prose is English
- [ ] Names a concrete change to `call-notes` that would have
  produced the 3 decisions the user wrote by hand
- [ ] Uses the 6 open questions or the 3 decisions as a fact

## C8-uk — Retro of a session a skill drove, Ukrainian (pair of C8)

> Користувач: `$call-notes` для
> `calls/2026-10-15-acme-kickoff.txt`
> Агент: Готово: `insights.md` і `summary.md`, 14 інсайтів, 6 відкритих
> питань.
> Користувач: Дякую. Потім я вручну виписав 3 рішення, які нам потрібні
> від Acme до п'ятниці, і надіслав команді.

Invocation: `$ambition-lens ретро`

- [ ] Prose is Ukrainian
- [ ] Names a concrete change to `call-notes` that would have
  produced the 3 decisions the user wrote by hand
- [ ] Uses the 6 open questions or the 3 decisions as a fact

## C9 — Task passed as an argument

Empty conversation. Invocation: `$ambition-lens migrate our 14 cron jobs from
the ops-01 VM to GitHub Actions`

- [ ] No clarifying question replaces the output
- [ ] Uses `14` and `ops-01`; states nothing the argument does not say

## C10 — Retrospective requested mid-task

> User: Help me write the v2 pricing page copy for `site/pricing.mdx`.
> Agent: Drafted the hero and the three tier cards; the FAQ is still to do.

Invocation: `$ambition-lens retro: what should I have asked differently so
far?`

- [ ] Steps are phrased as what to ask next time
- [ ] Starts from the drafted hero and tier cards; nothing proposes redoing them
  without saying why

## C11 — Agent momentum, tools available

> User: Rename the `customer_id` column to `client_id` across
> `services/billing` (Go).
> Agent: Found 37 references in 12 files with `rg -n customer_id
> services/billing`. Next I'll apply the rename with gopls and run
> `go test ./services/billing/...`.

Invocation: `$ambition-lens`

- [ ] No tool call besides reading `SKILL.md`; the rename is not performed
- [ ] When a candidate exists, it uses the 37 references in 12 files as a
  fact; the close says the announced rename waits

## C12 — Decisions, a dead end, and a constraint

> User: Our nightly ETL (`etl/nightly.py`, Airflow DAG `nightly_sales`) takes
> 4 h 40 min. It starts at 01:00 and must finish by 06:00.
> Agent: Profiled it: 70% of the time is `load_orders()` doing row-by-row
> INSERTs into Postgres.
> User: We tried an 8-vCPU Airflow worker last month: no change. And no new
> infrastructure this quarter, the budget is frozen.
> Agent: Switched `load_orders()` to `COPY` via psycopg. Local test on one day
> of data: 52 min → 9 min. Next I'll run it on staging.

Invocation: `$ambition-lens`

- [ ] No candidate repeats the bigger-worker dead end
- [ ] No proposal adds hardware or new infrastructure, unless it states that
  it challenges the budget decision and why
- [ ] Uses `52 min → 9 min` or the 70% share as a fact

## C13 — Process question, many fixes, no metric

> User: I maintain about 20 agent skills that consultants use. They complain
> that I change things all the time and the quality is still chaotic.
> Agent: Checked the repo: the skills have 3 to 11 versions each. Feedback
> arrives as emails after each release. 5 skills have no tests; the others
> test helper scripts, not a full agent run.
> User: What could I improve in my process?

Invocation: `$ambition-lens`

- [ ] Depth ranks first and names a success rate over repeated full runs
  (or an equivalent outside judge) as the missing measure
- [ ] Uses "3 to 11 versions" or "5 skills have no tests" as evidence
- [ ] Range is absent, or cites evidence for its trigger
