---
name: go-contract-mode
description: Use when the user says "go contract mode".
metadata:
  version: "2026.11.27.1"
  credits:
    skill: show-me
    author: Dex Horthy
    organisation: Humanlayer
    url: "https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md"
---

# Go Contract Mode

Contract mode is a special way to program a Go project: you design the
contract of a feature with the user and write it as real project code. The
result compiles and its tests run, but it does no useful work yet. Write the
agreed decisions into the actual files as a compilable skeleton for IDE
review, and explain each choice as you make it. The mode ends at a contract
that is ready for implementation; implementation is outside the mode.

The user's review attention is the scarce resource: a contract is short to
review, and an implementation is not. When a situation is not covered below,
choose the action that keeps the reviewed contract small, explicit, and stable.

## Hold the mode

The mode holds for every reply and every change to the project, in any file
and for a feature of any size, until the user says "stop contract mode". A
topic shift, many turns, a finished round, passing checks, design approval, and
a request to implement all leave it active. If you are unsure whether it still
applies, it does. While it holds, new code follows the rules in Allowed
skeleton code, also when another active skill asks for the smallest working
implementation: within this mode the requested result is the contract skeleton.

The state of the mode survives a summarized or resumed conversation in two
places: the status line of your last reply, and the skeleton in the files.
When a summary, a checkpoint, or a status line says that the mode is active
and the section "Contract map and approval" of this file is not in your
context, read this file again in full before you reply. Then inspect the
changed files and continue from the last status line. Keep the mode, phase,
approval state, comment style, open decisions, edited paths, and check results
in any checkpoint or handoff.

## Mode

Contract mode is a grilling session in two phases whose answers become code.
A **phase** is one level of detail, and its name tells the user what is being
designed now:

| Phase | Designs | New bodies |
| --- | --- | --- |
| **facade** · public contract | How the feature looks from outside: packages, files, public types and fields, public functions and methods, errors, boundary interfaces to existing code and external systems, the composition root, other resources, and the test scenarios of each public operation | Stubs |
| **internals** | One level deeper: the private functions, methods, and types that each public body calls, the order and data that pass between them, and the detail these add to the test scenarios | Each public body becomes a coordinating body; each new private body is a stub |

A **decision** is a design choice that the user owns. It is open until the
user answers it. The **frontier** is the set of open decisions of the current
phase whose prerequisites are settled. A **round** is one set of frontier
questions and then the files that express the answers. Each phase runs rounds
until its frontier is empty; then the user confirms the phase. Confirmation of
the internals phase is **design approval**. When a public body needs no internal
step, say so in the internals phase and keep its intent.

| Situation | Action |
| --- | --- |
| Activation | Say that contract mode is active, restate the feature goal in one sentence, and say that only contract code is written while the mode is active. Print the current comment style (see Allowed skeleton code) verbatim. Start the facade phase. |
| User sets or replaces the comment style | Confirm the new style verbatim in one line. Apply it to every comment written or revised after that. |
| Every reply while active | Write the reply in the language of the user's chat messages, the labels of views included. Start with one status line that names the mode, phase, and stage, for example `Mode: contract · facade · stage: questions`; translate every label into the user's language. Phases: facade or internals. The stage follows the state: questions, while a decision is open; review, while the contract map or a returned change waits for confirmation; approved, after design approval while neither holds. |
| A fact the project or conversation can answer | Find it yourself; ask only decisions. |
| The frontier has decisions | Ask the frontier in one round, as text in the round format below. A round asks at most five decisions, the most blocking first; name the rest of the frontier in one line as still open. Give each decision a recommended answer with a one-line reason, worded so "yes" accepts it. A decision that depends on an open one, or belongs to a later phase, waits. A reply settles the decisions that it answers. A plain acceptance of the round, such as "yes" or "all as recommended", settles every decision of the round with its recommendation. A decision that the reply does not mention stays open and leads the next round. A reply that only asks about a decision settles nothing: answer it and keep the round open. |
| User answers a round | In the same reply, write every settled decision into the files, run the build, give the round report, then ask the next round. Write no code that depends on an open decision; an assumption is the one exception. The settled first-round decisions on packages, types, and public methods are the shape agreement. |
| The frontier is empty and no assumption waits | Run the full checks and fix their failures in one batch. Show the contract map; in the internals phase also say that the contract is ready for implementation and that "stop contract mode" ends the mode. Ask the user to confirm. Confirmation of the facade phase starts the internals phase. After design approval, ask no question while no decision is open. |
| User names a phase to switch to, in any language | Switch and confirm the new phase in one line. Entering internals before the facade is confirmed: say that public decisions can still change; the confirmation at the end of the internals phase then confirms both phases, and the contract map says so. Returning to facade: reopen the public contract; a facade change that alters a public body returns its internal stubs to review. |
| Request for behavior or implementation, including after design approval | Write settled behavior as intent in the body that will perform it; ask unresolved contract choices as decisions. State that contract mode writes intent, not implementation, and that the mode ends when the user says "stop contract mode". |
| Comment, TODO, or naming refinement during review | Apply it directly. |
| Change to packages, types, or public methods | When the user states the change, it is settled: write it, show the shape change in the round report, and ask only the decisions that it opens. When you propose the change, ask it as a decision with the shape change shown; write it after the user agrees. In the internals phase, such a change returns the public contract to review. |
| A confirmed phase or an approved contract needs a change | Return that change to review; do not rely on it before agreement. |
| User says "stop contract mode" | End the mode and confirm it in one line. The phrase requests nothing else: change no file. Stop showing the status line. |

Round format:

```text
❓ **Q1** - **<decision>**: <question>; for a material decision, each option with its trade-off

➡️ <recommended answer> - <one-line reason>
```

Shape agreement permits the first files. Confirmation of a phase fixes its
declarations, doc comments, intent, and test scenarios. Reuse consent already
given in the conversation.

Before sending each reply while the mode is active, check:

1. The reply starts with the status line.
2. Every new or revised body is a stub or a coordinating body; constructors
   only assign dependencies.
3. Changed files passed the build, and at the end of a phase the full
   checks, or the reply labels them unverified.
## Scope and existing code

Work on the selected feature in an existing Go project or a new module. Use the
conversation as the domain context; a separate prose specification is not
required. Before proposing a shape, read project instructions, build tasks, and
the code the feature touches, and map what already exists:

- Working code, such as types, interfaces, errors, helpers, and adapters, is a
  dependency of the contract. Reuse its types and declare it as a dependency
  instead of duplicating it. A call into it is behavior: name it in the intent
  of the body that will make it.
- Change existing code in contract form when the design needs it. Show the
  change in the shape as a `diff` first. Then change the declaration and update
  its callers so that everything compiles. When the behavior of an existing
  body changes, write the new behavior as intent and make the body a stub.
  A stub in working code also stops every existing test that reaches it
  through its callers. List those tests with the `diff`, so the user agrees to
  the scenarios that become pending. When a caller must keep working,
  recommend a new entry point beside the existing body instead. The listed
  tests skip on the stub, with new expectations where the behavior changes;
  all other tests keep passing. Delete removed code together with its tests.
- A skeleton left by an earlier round or session, with `TODO(contract)` markers,
  not-implemented returns, or contract skips, is the current contract. Continue
  from it. Ask which phase it is in and whether it is confirmed only when the
  conversation does not say.
- Keep existing code that the design does not change intact. Check that every
  reused symbol and import exists.

## Design with the user, then write the code

1. Before proposing a shape, read [Go contract design](references/go-design.md):
   how to shape a feature from the caller's scenario, and the conventions
   that apply when the project has none of its own.
2. Put the proposed shape in the first round: a short file tree or call tree,
   with its open choices as decisions. When the project has no
   not-implemented error, ask for it and its location in this round. Write no
   file before these answers.
3. A **material decision** is a decision that changes the public contract, a
   boundary, a failure outcome, or data that a later step relies on. In every
   phase, show at least two viable options for a material decision, each with
   its trade-off against the constraints of the conversation, and recommend
   one. When the constraints leave one viable option, name the option that
   they exclude and the reason.
4. From the first answered round on, a round writes every settled decision
   whose code depends on no open decision, then runs the build. An
   explanation or a plan alone is not a round. When an answer settles nothing
   that can be written yet, say that no file changed and ask the missing
   decisions first.
5. In the internals phase, take each public body and propose the internal steps it calls:
   their signatures, the data passed between them, and where each rule,
   dependency call, and compensation lives.

### Features of any size

Design a large feature top-down. The facade phase fixes the top level: packages
and their responsibilities, public entry points, and the boundaries to existing
code and external systems. In the internals phase of a large feature, a round asks
the frontier of one public body. Every round report lists the public bodies
that still wait for internals.

### Keep the contract minimal

- Every public declaration, field, option, and interface serves a scenario from
  the conversation. Name what you leave out in one line instead of adding it
  for later. When the user asks for an element no scenario needs, ask it as a
  decision that recommends leaving it out.
- When an answer makes a declaration unnecessary, delete it from the skeleton.
- In the internals phase, a step becomes a stub when it owns one responsibility,
  such as a rule, a dependency call, or a compensation; a step that does not
  stays a line of intent.
- A new dependency is a decision for the user.

## Allowed skeleton code

The **skeleton** is the whole code artifact under design. Its bodies express
structure and intended flow; they do not perform the feature's useful work.

| Part | Write while contract mode is active |
| --- | --- |
| Structure | Packages, files, types, interfaces, and the functions and methods the design declares |
| Models | Fields, with a comment where the name and type leave meaning, unit, identity, optionality, or lifecycle unclear |
| API | Signatures, result types, domain errors, and godoc |
| Connections | Constructor assignment of dependencies; in the internals phase, coordinating bodies |
| Composition root | Construction of the feature's types, passing of dependencies, and registration of routes and handlers. The program builds and starts as before |
| Other resources | Declarative files in full, such as schema migrations and API definitions. A statement that changes data is an intent comment, in a file that the migration runner does not apply yet |
| Bodies | Stubs |
| Tests | Test scenarios, compile-time interface checks, and disclosed stub skips |

Ask each new resource and each change to the composition root as a facade
decision; [Go skeleton patterns](references/go-skeleton.md) has their rules.

A **stub** is a body that holds its intent as `TODO(contract)` comments and
then a stub return: the project's not-implemented error, a marked zero value
when there is no error result, or, in a transport adapter, the not-implemented response of the transport, such as HTTP status 501. Business validation, calculations, algorithms,
storage queries, calls to dependencies or existing code, compensation, retries,
rollback, and result assembly live in the intent of a stub. Keep signatures
useful for the intended design; do not add an error result just to make
stubbing easier.

A **coordinating body** is a internals-phase body that shows the flow of an
operation as code and does none of its work. It contains only:

- calls to this feature's stubs;
- `if err != nil` branches that return the error, wrapped with `fmt.Errorf`
  or joined with `errors.Join`;
- branches, loops, and early returns whose condition is the result of a stub
  call, a nil check of an error that a stub returned, or an `errors.Is` or
  `errors.As` check of a declared error, and `range` loops over a declared
  field or a stub result;
- a lock on an existing receiver mutex around them;
- for a value that several steps share, such as a derived context: one stub
  call that returns the value and its release function, and a `defer` of that
  function. The rule for the value then lives in one intent.

Every condition and every action is a stub call. A comparison of domain
values, a calculation, a call to a dependency, and result assembly stay in the
intent of a stub; a rule that decides a branch becomes a stub that returns
`bool`.

The **intent** is a body's planned behavior, written so that the file alone
states it: a reader of the body needs no part of the conversation.

- One `TODO(contract):` block per body, as ordered steps, one action per step.
- Each step names the declared dependency, field, or error it uses.
- State every rule, order, failure outcome, compensation, idempotency rule,
  and invariant that the conversation settled for this body.
- Describe what happens and in which order, in domain terms rather than Go code.
- Write settled decisions and assumptions only. Ask every other open decision
  in the round; write the step that waits for it after the answer.
- A complete intent can need a detail that no answer settled. An
  **existing-code detail** is such a detail that existing code of the project
  already settles for the same case: follow that code. An **assumption** is
  such a detail that existing code does not settle: write your choice and
  name it in the round report. An assumption is the one open decision that you
  write before its answer: it leads the next round, and the frontier is not empty while one waits. Ask a change to a settled decision before you
  write it.

The intent is complete when all three conditions hold:

1. Every settled decision that affects the body appears in it.
2. Every step that can fail states its outcome: the returned error and the
   state that remains.
3. Every name in it is a declaration in the files.

A **test scenario** is the stub of a test. It records one agreement about
behavior, discussed or clear from the conversation, as a named case, and it
skips while the behavior is pending. The mode sets the boundary of a scenario;
the project sets its form. Boundary: a case holds its inputs and its expected
outcome as Go values, and the test calls the entry and skips on the stub
result, so that the case runs when the stub is gone. When the entry cannot
return a stub result while a body that it calls is a stub, its test holds an
explicit skip that names the pending bodies: for a body without an error
result, and for an internals-phase coordinating body that returns success
without reaching a stub, such as a loop over an empty stub result. A scenario
asserts the agreed effects and the agreed absence of effects, not only the
returned values. Form: follow the
project's test conventions and libraries; when the project has none, write
table-driven tests. Write the scenarios of each public operation in the facade phase, and
refine them in the internals phase as decisions add detail.

The **comment style** controls the language of godoc and intent comments.
Unless the user sets another style, use this default:

```text
"Write documents in ASD-STE100 with given-new flow: topic sentence first, every term defined before use, every logical link written as a word."
```

A style the user states replaces the default for the rest of the mode.

Godoc states what the name and signature do not say: purpose when it is not
obvious, errors, invariants, effects, and ordering. Where the project's linter
or conventions require a comment, write one line that starts with the name.

Before writing bodies or test scenarios, read
[Go skeleton patterns](references/go-skeleton.md) for error reuse, intent
bodies, internals-phase calls, zero-return stubs, and tests that skip pending behavior.

## Check and present each round

After each answered round, run the project's build command, or
`go build ./...` when it has none. At the end of each phase, before the
contract map, run the project's full build, static-check, and test commands,
or `go vet ./...` and `go test ./...` in the feature's module when it has none,
and fix all their failures in one batch. If the environment or an existing failure
blocks a check, name the command and the limitation and label the round
unverified.

The **round report** lets the user see whether you understood their intent
before it settles in the contract. In chat, give:

- One line for each decision whose answer was not a plain acceptance, or whose
  code differs from the recommendation: what you understood, the choice, and
  the trade-off.
- One line that lists the decisions written as recommended. The question
  already gave their reasons; do not repeat them.
- One line for each assumption, and one line that lists the existing-code
  details.
- File links in the order the user should read them in the IDE.
- One line of check results with the number of skipped tests; give detail
  only for a failure.

The code stays in project files; the chat explains its meaning. When a round
changed the shape or the call flow, show that change with one view, the
smallest that makes it clear: a shallow file tree, a call tree, a `diff` of
the tree or signature, the intent steps as pseudocode, or a Mermaid
sequence or state diagram ([Views](references/views.md)). Do not paste full files into the chat.

## Contract map and approval

The **contract** consists of the confirmed public and private declarations,
their doc comments, the intent in their bodies, and the confirmed test inputs
and expected outcomes.

At the end of each phase, show the **contract map** before asking for
confirmation. It shows on one screen what the user confirms, as views and
not as a table; the user reads the code itself in the IDE:

1. A shallow file tree of the new (`+`) and changed (`~`) files, resources and
   the composition root included, each with its role in a few words.
2. For each public operation, its signature with its errors and boundaries.
   In the internals phase, a call tree of its steps instead, with the error
   or the boundary next to the step that uses it.
3. One line of check results with the number of
   skipped tests, and one line that names the comment style.

[Views](references/views.md) has the form of each view and a complete map.

Passing checks prove structural validity, not implemented behavior.
