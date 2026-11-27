# Eval cases

The skill makes the end of every reply predictable: a work report after work,
numbered asks, and one fixed last line. Each case checks one of these
promises. Boxes marked **[script]** are checked by `check_reply.py`; the
grader checks the other boxes.

## How to run

The steps work in any agent host (Claude Code, Codex, Copilot). Run each
session with `HOME` pointing to an empty folder where the host allows it:
R2 and R5 assume no SSH hosts and no cloud credentials.

1. **Generate.** Start one fresh session per case and per arm.
   - Skill arm: the skill is installed, and the first message is
     "Use the reply-contract skill for this session." followed by the case
     prompt. Case R6 is the exception: it states its own setup.
   - Baseline arm (cases marked _baseline_): the same prompt in a session
     without the skill.
   Save the final reply verbatim to
   `<runs>/<date>-v<version>/<case>-<arm>-r<i>/reply.md`, with the tool calls in `tools.txt` next to it.
   `<runs>` is a results folder that you choose; keep it out of version control.
   Record the host, model, and effort in `run.md` in the same folder.
2. **Script.** From this `evals/` folder, run
   `uv run check_reply.py <files>`.
   Add `--work` for R3 and R5.
3. **Grade.** Give a fresh agent the grader prompt below. The session that
   generated the replies does not grade them.
4. **Record** the verdicts and the limits in `run.md`.

A case passes only when every box passes in the skill arm. A baseline arm
passes nothing; it shows how much of the behaviour the skill adds. Run each
case at least 3 times before you call it stable.

## Common boxes (every case)

- [ ] **[script]** The last line is exactly `⏸️ Nothing needed from you right now.`
  or `⏩ Needed from you: N ⤴️`, with N in keycap digits.
- [ ] **[script]** N equals the number of ask items; the items are numbered
  1️⃣ to N in order, and each item has an empty line before it.
- [ ] The reply has no ask that the agent could decide or do alone.

## R1 — Plain question, nothing needed _baseline_

> What does `git rebase --onto A B C` do? Answer in three sentences.

- [ ] Last line is `⏸️ Nothing needed from you right now.`
- [ ] No Evidence block, and no sentence about its absence: the agent did no work.
- [ ] No ask section at all, not even an empty one.

## R2 — The task needs the user _baseline_

> Deploy my static site to my VPS.

Run it in an empty folder: the agent has no host, credentials, or site files.

- [ ] One topic per item (facts about one thing, such as host and SSH user, are one
  topic; a permission is a separate topic), each with what to do, where, and
  what to send back.
  "I need SSH access" fails; "Send the VPS host name and SSH user" passes.
- [ ] Most blocking ask first; after the last item, one line on what the agent
  does meanwhile ("nothing until you reply" is acceptable).
- [ ] The heading of the ask section is in English.

## R3 — Work done

> In this folder, create `hello.py` that prints `hi`, run it, and show me the result.

Run it in an empty scratch folder with Python available.

- [ ] **[script, --work]** `**Evidence**`, `**How I check it**`, and
  `**Decided without me**` appear in this order, before any asks.
- [ ] Evidence shows the real output `hi`, not a description of it.
- [ ] How I check it gives a command and the expected output.

## R4 — Russian conversation, two asks

> Помоги настроить отправку писем из моего приложения через SMTP. Провайдера я ещё не выбрал.

Run it in an empty folder.

- [ ] The ask heading and the items are in Russian.
- [ ] **[script]** The last line is still the English contract line with `2️⃣`
  or the real number of asks.
- [ ] A default the agent proposes (for example a provider) is stated above the
  section, not as a numbered ask.

## R8 — English conversation, two asks (pairs with R4)

> Help me set up sending email from my app over SMTP. I haven't picked a provider yet.

Run it in an empty folder.

- [ ] The ask heading and the items are in English.
- [ ] **[script]** The last line is the English contract line with `2️⃣`
  or the real number of asks.
- [ ] A default the agent proposes (for example a provider) is stated above the
  section, not as a numbered ask.

## R9 — Ukrainian conversation, two asks (pairs with R4)

> Допоможи налаштувати надсилання листів із мого застосунку через SMTP. Провайдера я ще не обрав.

Run it in an empty folder.

- [ ] The ask heading and the items are in Ukrainian, not Russian.
- [ ] **[script]** The last line is still the English contract line with `2️⃣`
  or the real number of asks.
- [ ] A default the agent proposes (for example a provider) is stated above the
  section, not as a numbered ask.

## R7 — Ukrainian conversation, asks _baseline_

> Допоможи налаштувати резервне копіювання бази PostgreSQL у хмару. Хмару я ще не обрав.

- [ ] The ask heading and the items are in Ukrainian, not Russian.
- [ ] **[script]** The last line is still the English contract line.
- [ ] A default the agent proposes is stated above the section, not as a numbered ask.
- [ ] One ask section, not two headings over one list.

## R10 — English conversation, asks _baseline_ (pairs with R7)

> Help me set up backups of my PostgreSQL database to the cloud. I haven't picked a cloud yet.

- [ ] The ask heading and the items are in English.
- [ ] **[script]** The last line is the English contract line.
- [ ] A default the agent proposes is stated above the section, not as a numbered ask.
- [ ] One ask section, not two headings over one list.

## R11 — Russian conversation, asks _baseline_ (pairs with R7)

> Помоги настроить резервное копирование базы PostgreSQL в облако. Облако я ещё не выбрал.

- [ ] The ask heading and the items are in Russian, not Ukrainian.
- [ ] **[script]** The last line is still the English contract line.
- [ ] A default the agent proposes is stated above the section, not as a numbered ask.
- [ ] One ask section, not two headings over one list.

## R5 — Work blocked half-way

> Create `config.json` with `{"port": 8080}` in this folder, then upload it to my S3 bucket.

Run it in a scratch folder with no cloud credentials.

- [ ] **[script, --work]** The work report comes first, then the asks, then the last line.
- [ ] Evidence shows the created file; the upload is reported as not done, with the reason.
- [ ] The ask names the missing input: the bucket name and credentials, or approval to use a tool.

## R6 — Activation through AGENTS.md, skill not named

Setup: a scratch folder whose `AGENTS.md` (or `CLAUDE.md`) contains the text
of `skills/**/reply-contract/assets/agents-md-snippet.md`; the
skill is installed. Do not name the skill in the message.

> List three common causes of a 502 error behind nginx.

- [ ] The reply ends with the contract line, so the snippet loaded the rule.
- [ ] Record whether the host loaded the skill file or applied the snippet text
  alone (from the transcript, when the host shows it).

## Grader prompt

```text
Grade the replies in <run>/ against
build/**/reply-contract/evals/cases.md.

Read completely: skills/**/reply-contract/SKILL.md, the cases
file, <run>/run.md with the script output, and every <run>/R*-skill-r*/reply.md with its tools.txt.
Read transcript.jsonl when a box needs tool results. Do not read other runs or git history. Do not edit any file except the one
you write.

Copy the [script] results from run.md; do not re-judge them. For every other
box of every case, write pass or fail and one line of evidence quoted from
the reply. A case passes only when all its boxes pass. For each baseline
reply, write one line: which promises it kept without the skill.

Write <run>/grades.md: a table (case, verdict, failed boxes), the per-case
details, then the SKILL.md sentence behind each failure. End with one
verdict: release-ready, revise, or inconclusive.
```
