---
name: ambition-lens
description: "Finds where the current task could aim higher, from evidence in the conversation, and ranks at most three bigger versions. Use when the user asks how a task could be more ambitious, before, during, or after the work."
disable-model-invocation: true
argument-hint: "[task]"
metadata:
  version: "2026.11.11.1"
---

# Ambition Lens

The user wants to know where this task could aim higher. Suggest bigger
versions of the **task itself**; improving the agent's environment is the
`retro` skill's job. This skill proposes; the user picks.

## Steps

1. Read the current conversation, or the task passed as the argument. When the
   user asks about another conversation, ask which one and wait for a yes in
   chat before reading its transcript or log. With no task at all, ask for it
   in one question and stop.
2. Collect the **evidence**: the goal, finished work with its numbers,
   decisions and constraints, dead ends. Every candidate starts from one piece
   of evidence; a file name alone is not evidence.
3. Check each lens against its _Use when_. A lens **fires** when the
   conversation holds evidence for its trigger. The output names a lens only
   as the tag of a candidate it produced, in English: Speed, Altitude, Depth,
   Range.
   - **Speed** — _Use when_ a step was repeated by hand, independent work ran
     in series, an existing tool or skill was rebuilt, or work the goal does
     not need was done. Propose the same outcome sooner, including dropping
     the unneeded work.
   - **Altitude** — _Use when_ the result feeds a decision or a meeting, or
     the task will recur. Propose the standing outcome behind the task and the
     access, data, or environment the agent needs to own it.
   - **Depth** — _Use when_ a result or a plan rests on an assumption nobody
     checked, or on digested material instead of raw data. Name the assumption, the
     raw data that would test it, and the **outside judge** (a tool, test,
     dataset, or person other than the model).
   - **Range** — _Use when_ the same kind of approach was tried twice and
     stalled, or the result must convince a sceptical or hostile audience.
     Name the field that solves this problem routinely and the method its
     practitioner applies.
4. Present at most three candidates, ranked by value for effort, best first,
   in plain words in the language of the user's recent messages. Each
   candidate is a short paragraph tagged with its lens name: what you saw in
   the conversation, the bigger version, and the first step with rough effort.
   Add a ready prompt only when that step belongs in a separate session; it
   names the files, data, and tools it needs. A candidate that departs from a
   decision in the conversation says so and why. When no lens fired, the
   whole output is one line naming the evidence that would make one fire,
   then the question in step 6.
5. When the task is finished, every first step targets the next run of the
   task; a check of the finished result is a side note in the paragraph,
   never the first step. When a skill
   drove the session, name the change to that skill that would make the best
   candidate the default.
6. End the turn with one question: which candidate, if any, to start. The
   candidates, and any next step the conversation had already announced,
   start only after the user picks; when such a step was announced, the
   question says that it waits too.
