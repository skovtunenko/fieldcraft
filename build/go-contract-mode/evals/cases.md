# Go contract mode evaluation cases

Run these against the installed skill in an isolated scratch project.
Judge the resulting files and command results. Matching headings or wording
is not evidence of correct behavior.

## Agreed form in an existing project

Give the agent a Go module with a suitable not-implemented sentinel and a small
working function outside the requested change. The user requests an order
placement skeleton and has agreed to the proposed shape, but has not yet
given design approval. The feature reserves stock and records an order.

Check that the agent writes and checks actual Go files, preserves the existing
function, represents responsibilities in types, writes each new body as ordered
`TODO(contract)` intent with a stub return, comments only fields whose name and
type leave their meaning unclear, and supplies real test inputs and expectations
as Go values in the project's test form, or in a table-driven test when the
project has none. A case that is only a description string, or that skips
without calling the entry, fails this check.
Check each intent against the files alone: every settled decision that affects
the body is in it, every step that can fail states the returned error and the
state that remains, and every name in it is a declaration.
Check that it neither repeats the shape-agreement question nor implements business
rules or external effects. Record skips separately from passing assertions.

## No-error leaf

Request a scalar-returning calculation as a stub within an agreed skeleton.
Check that the signature remains useful, the zero return has a contract marker,
and a pending behavior test retains real data and expectations below its skip.

## Refinement and implementation boundary

Continue from a skeleton with a request to rename a field and update its meaning.
Check that the agent modifies files instead of returning only advice. Then
confirm that the design is approved without ending contract mode, and request
real validation logic. Check that the agent keeps the mode active, leaves behavior
stubbed, and records the agreed rule in the intent of its body. A proposed signature or
scenario change must return for review before the agent relies on it; the
status line then names the stage questions or review, not approved.

## Mode hold across turns

Run three user turns with a smaller model (Sonnet or Haiku) in a scratch module
that has a not-implemented sentinel. Turn 1: the trigger phrase "go contract mode"
and an order placement feature with reservation rollback. Turn 2: agree to the
shape and answer its open questions. Turn 3: ask it to "just implement validation".

Check that every reply starts with the mode status line, with the phase and
the stage in the user's language, turn 1 prints the
default comment style verbatim and writes no files, turn 2 writes and checks the skeleton, and turn 3 keeps validation stubbed.
It may refine the intent or agreed contract, and it names "stop contract mode"
as the phrase that ends the mode.

## Contract map, approval, and exit

Continue from a internals-phase skeleton whose last open decision the user answers.
Check that the agent runs the full checks, fixes failures in one batch, shows a
one-screen contract map made of views, not a table: a file tree of new and changed files, a call
tree of each public operation with its errors and boundaries, one line of
check results and the comment style, says that the contract is ready for implementation
without starting it, names "stop contract mode" as the phrase that ends the mode, and asks the user to check it once more. Confirm it, then ask for
production implementation without ending the mode. Check that approval
preserves the skeleton, its intent, stub errors, and disclosed skips. Repeat
with `ponytail full` active; its minimum-code rule must not unlock behavior.
Then say only "stop contract mode". Check that the agent confirms exit in one
line and changes no body.

## Resume a large existing feature

Give the agent a multi-package project with working inventory and payment code,
a partially refined order skeleton, and a checkpoint that records active contract
mode and design approval. Request the next agreed refinement after a topic shift.
Check that it reads the current code, continues the existing skeleton, lists the
public bodies that still wait for internals, and changes only the agreed contract. Existing implementations must
remain intact; new dependency calls and rollback stay in intent comments.
Passing build, vet, and tests must not end the mode or imply behavior is implemented.

## Comment style override

Activate the mode and check that the reply prints the default ASD-STE100 style.
Then say "comments in plain Russian". Check that the agent confirms the new
style verbatim, writes later godoc and intent in Russian, and shows the new
style in the contract map.

## Facade and internals phases

Run the order placement feature from activation. Check that the facade phase rounds
settle only packages, files, public declarations, errors, and boundaries, that
public bodies hold intent and a stub, that each public operation gets skipped
test scenarios before the facade contract map, and that each round runs only
the build.
Check that the facade phase ends with full checks, a contract map, and a confirmation
question. After confirmation, check that the internals phase proposes internal steps, the
public body then only calls new stubs and returns wrapped errors, and each new
stub holds intent and a stub return.

## Large frontier

Activate the mode for a feature whose first shape has eight open decisions
with settled prerequisites. Check that the round asks five of them, the most
blocking first, and names the other three in one line as still open. Answer
the round. Check that the next round asks those three and the decisions the
answers opened.

## Change to existing code

Request a feature that changes the signature and behavior of an existing
working function with callers and tests. Check that the agent shows the change
as a shape `diff` first, keeps every caller compiling, writes the new behavior
as intent with a stub, gives the changed tests new expectations with a skip on
the stub, and keeps all other tests passing.

Then request a behavior change in a shared helper that another working
operation calls, such as `Catalog.Quote` under `Checkout.Place`. Check that the
agent lists the existing tests that reach the helper through its callers
before it writes the stub, or recommends a new entry point that keeps the
caller working, and that no unlisted test fails or skips.

## Partial answers

In a round of several decisions, reply only "Q2: what does this option mean?".
Check that the agent answers, writes no file, and keeps every decision open.
Then reply "Q2: use the other type". Check that the agent writes Q2 as
answered, writes no code that depends on the other decisions, and asks them
first in the next round. Then reply "yes". Check that the agent writes every
decision of that round as recommended and lists them in one line of the round
report without repeating their reasons.

## Lean round report

Answer a round of four decisions with "Q1-Q3: yes. Q4: return the order, not
only an error". Check that the round report gives one line for Q4 with what
the agent understood, one line that lists Q1-Q3, the file links in reading
order, one line of check results, and at most one view. The next round follows
in the same reply.

## Assumption in a written round

Answer a facade round so that one failure outcome of the public body stays
unsettled. Check that the agent writes the outcome as its assumption, names it
in one line of the round report, and asks it first in the next round. Check
that a detail that existing code already settles, such as the lock of a
sibling method, is written without a question and listed in one line. Then
check that the agent asks before it writes a step that differs from an
accepted recommendation.

## Mode recovery after compaction

Run the mode until the internals phase, then continue in a context that holds
only a summary with the last status line and the first 5,000 tokens of
`SKILL.md`. Request a change of the call flow. Check that the agent reads
`SKILL.md` again before it replies, starts the reply with the status line,
and writes the change as contract code.

## Branch in a coordinating body

In the internals phase, agree that a repeated request returns the earlier result
and that a failed record step releases the reservation. Check that the public
body shows the early return and the release as code, that each condition is a
stub result or a declared-error check, and that the body holds no calculation,
dependency call, or result assembly. Then agree that the effects run under one
derived context. Check that one stub returns the context and its release
function, that the body defers the release, and that the rule for the context
is in one intent.

## Composition root and resources

Request a feature that stores a new model in a database with schema migrations
and must be reachable from `main`. Check that the agent asks the migration and
the change to `main` as facade decisions, writes the schema statements in
full, writes a data backfill only as an intent comment, registers the handler
in the composition root, shows both in the file tree of the contract map,
and that the program builds and starts.
Use the `fixtures/notes/` module and `scenarios/notes-tags.md`.

## Phase switch

Run this case in English, Russian, and Ukrainian. During the facade phase,
say "let's go to the internals" (Russian "давай к устройству", Ukrainian
"переходимо до внутрішньої будови"). Check that the agent switches
to the internals phase, confirms it in one line, says that public decisions can
still change, and names the internals phase in the status line. Finish the internals
phase without confirming the facade; check that the contract map says that the
confirmation covers both phases. Then say
"back to the facade" (Russian "вернёмся к фасаду", Ukrainian "повернімося до
фасаду") and change a public signature. Check that the agent reopens
the public contract, writes the stated change without asking it again, and
returns the affected internal stubs to review.

## Options for a material decision

Run the order cancellation scenario from activation. Check that the round that
decides how a cancellation releases stock shows at least two viable options,
each with its trade-off against the stated constraints, and recommends one with
the reason that the others lose. Then state a constraint that leaves one viable
option, and check that the next such decision names the excluded option and the
reason instead of a list of one.

## Effects and explicit skips

Continue from an agreed order placement facade. Check that the out-of-stock
scenario asserts that no order is stored, not only the returned error. In the
internals phase, make a public `ProcessAll() error` range over a collection
stub that returns an empty result. Check that its test holds an explicit skip
that names the pending bodies, and that the full checks run `go vet ./...` and
`go test ./...` when the module defines no check commands.
