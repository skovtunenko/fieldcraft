# Best-practices rule catalogue

The rule catalogue every audit grades against. Rules are paraphrased from
the article; IDs are stable and never reused. The **snapshot** is the dated
capture of the article the catalogue was distilled from (see Snapshot).

## Contents

- [Snapshot](#snapshot)
- [Terms](#terms)
- [Core principles (BP-01 to BP-03, BP-56)](#core-principles-bp-01-to-bp-03-bp-56)
- [Skill structure (BP-04 to BP-22)](#skill-structure-bp-04-to-bp-22)
- [Workflows and feedback loops (BP-23 to BP-25)](#workflows-and-feedback-loops-bp-23-to-bp-25)
- [Content guidelines (BP-26 to BP-27)](#content-guidelines-bp-26-to-bp-27)
- [Common patterns (BP-28 to BP-31)](#common-patterns-bp-28-to-bp-31)
- [Evaluation and iteration (BP-32 to BP-39)](#evaluation-and-iteration-bp-32-to-bp-39)
- [Anti-patterns to avoid (BP-40 to BP-41)](#anti-patterns-to-avoid-bp-40-to-bp-41)
- [Skills with executable code (BP-42 to BP-55)](#skills-with-executable-code-bp-42-to-bp-55)
- [Retired rules](#retired-rules)

## Snapshot

- Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
  (raw Markdown: the same URL with `.md` appended)
- Title: Skill authoring best practices (Anthropic)
- Snapshot date: 2026-11-10
- Version marker on the page: none
- Rules: 56 (BP-01 to BP-56); 12 mechanical, 44 judgment; levels: 11 must,
  39 should, 6 consider
- Article headings: [article-headings.md](article-headings.md) (refresh only)
- Source hash: [source-hashes.md](source-hashes.md) (refresh only)
- Mechanical rules: BP-04, BP-05, BP-06, BP-07, BP-08, BP-09, BP-10, BP-17,
  BP-21, BP-22, BP-39, BP-40. `scripts/check_mechanical.py` decides exactly
  this set, plus the mechanical rules of
  [other-official-sources.md](other-official-sources.md).

## Terms

- **Level** follows the article's wording: `must` for hard limits and
  absolute words (must, cannot, always, never); `should` for plain imperatives
  and checklist items; `consider` for options, tips, and patterns offered as
  one choice.
- **Source**: the link to each article section the rule's Section field
  names, in the same order. The anchor is the page's HTML `id`, stored as
  captured, never derived from the heading text: "Solve, don't defer" has the
  id `solve-dont-punt`.
- **Type**: `mechanical` rules are decided by the script; `judgment` rules are
  decided by reading the files, and every verdict cites a `file:line` or a
  short quote.
- **Status**, decided in this order:
  - n/a: the rule's own applicability condition (its "n/a when" clause) does
    not hold; the reason goes in Evidence. A rule that applies to evaluation
    material is also n/a when the skill has none: BP-32 alone reports that
    absence, and Evidence reads "no evaluation material (BP-32)".
  - ❌: a "Fail when" condition holds, including when material the rule
    requires is absent (no stated surface, no evaluation material for BP-32). A
    defect that a more specific rule owns is that rule's ❌ only; this rule
    is ✅ citing it (One defect, one rule).
  - ✅: "Pass when" holds.
  - Neither holds: the Rule line decides. ❌ when the files show its
    requirement unmet, ✅ when they show it met; Evidence names the line.
  - Not evaluated: the material exists but cannot be read or judged (an
    unreadable file, a script that cannot run). A rule with a confirmed
    failure in the material that was read stays ❌, with a note that some
    material could not be read. Otherwise its status is n/a and the report
    lists it under its not-evaluated heading with the reason.
- **One defect, one rule**: a defect is reported once, under the most specific
  rule that covers it (a long reference listing inlined in the body is BP-53;
  BP-18 cites it rather than repeating it). Overlapping rules cite
  that rule in Evidence and stay ✅ unless they have a defect of their own.
  Mechanical verdicts are exempt: they stay as the script reports them.
- **Location of absent material**: the folder where it was looked for,
  relative to the target, with the target root written as `./` (for example
  `./` or `./evaluations/`).
- **Body**: the lines of `SKILL.md` after the closing `---` of the frontmatter.
- **Bundled files**: every file under the skill directory except `SKILL.md`,
  hidden files, evaluation and test folders, and unit-test files.
- **Reference files**: material Claude reads on demand: every file in
  `references/` (any type, such as a `.json` schema) and every other bundled
  `.md` file outside `assets/` and `scripts/` (assets are output templates,
  scripts are run).
- **Directly linked**: named in `SKILL.md` by a Markdown link or by its
  relative path.
- **Evaluation material**: an evaluation or test folder inside the skill, or a
  location the user names.

## Core principles (BP-01 to BP-03, BP-56)

### BP-01 — Only add context Claude lacks

Type: judgment · Level: should · Applies to: body, reference files · Section: Concise is key

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#concise-is-key>

- Rule: every paragraph earns its tokens; general knowledge Claude already has
  (what a format is, how a common library works) is left out.
- Pass when: every passage carries a skill-specific fact, decision, command, or
  constraint.
- Fail when: a passage explains a widely known concept, or holds background
  prose that changes no action.
- Fix: delete the explanation and keep only the instruction it led up to.

### BP-02 — Match specificity to fragility

Type: judgment · Level: should · Applies to: body, reference files · Section: Set appropriate degrees of freedom

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#set-appropriate-degrees-of-freedom>

- Rule: give heuristics where many approaches work, a template where one
  pattern is preferred, and one exact command where an operation is fragile or
  order-critical.
- Pass when: each instruction's rigidity matches its risk.
- Fail when: a destructive, fragile, or order-critical step is described
  loosely, or an open-ended task is forced into a rigid script.
- Fix: pin the fragile step to an exact command with "run exactly this", or
  loosen the rigid one into criteria.

### BP-03 — Test with every target model

Type: judgment · Level: should · Applies to: evaluation material · Section: Test with all models you plan to use

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#test-with-all-models-you-plan-to-use>

- Rule: the skill is tested on each model it will run on (Haiku, Sonnet, Opus,
  or a stated subset).
- Pass when: test notes record results per target model, or state the model
  scope and cover it.
- Fail when: there is no evidence of testing on more than one model and no
  stated model scope, or a model in the stated scope has no recorded result.
- Fix: run the test scenarios on each target model and record results per
  model.

### BP-56 — Instructions work for every target model

Type: judgment · Level: should · Applies to: body, reference files · Section: Test with all models you plan to use

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#test-with-all-models-you-plan-to-use>

- Rule: when the skill runs on several models, its instructions give a less
  capable model (such as Haiku) enough guidance without over-explaining for a
  stronger one (such as Opus). High-freedom guidance stays valid: the
  question is whether a less capable model could act on it.
- Pass when: every instruction can be acted on by the least capable target
  model, and nothing is explained at a length the strongest one does not need.
  n/a only when the skill explicitly targets a single model.
- Fail when: an instruction leaves out what a less capable model would need to
  act (an undefined term, a decision with no criterion, such as "handle
  errors appropriately"), or explains at length what any target model already
  does.
- Fix: add the missing criterion or definition, and cut the
  over-explanation.

## Skill structure (BP-04 to BP-22)

### BP-04 — `name` present, at most 64 characters

Type: mechanical · Level: must · Applies to: frontmatter · Section: Skill structure; YAML frontmatter requirements

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#skill-structure>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#yaml-frontmatter-requirements>

- Rule: the frontmatter has a non-empty `name` of 64 characters or fewer.
- Pass when: `name` exists, is a non-empty string, and is at most 64
  characters.
- Fix: add or shorten `name`.

### BP-05 — `name` uses lowercase letters, digits, and hyphens

Type: mechanical · Level: must · Applies to: frontmatter · Section: Skill structure; Naming conventions; YAML frontmatter requirements

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#skill-structure>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#naming-conventions>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#yaml-frontmatter-requirements>

- Rule: `name` contains only `a-z`, `0-9`, and `-`.
- Pass when: every character of `name` is in that set. n/a when `name` is
  missing.
- Fix: lowercase the name and replace other characters with hyphens.

### BP-06 — `name` has no XML tags

Type: mechanical · Level: must · Applies to: frontmatter · Section: Skill structure; YAML frontmatter requirements

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#skill-structure>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#yaml-frontmatter-requirements>

- Rule: `name` contains no XML tag.
- Pass when: `name` has no element tag (`<b>`, `</b>`, `<br/>`, `<x attr>`);
  comparison text such as `<=` is not a tag. n/a when `name` is missing.
- Fix: remove the tag.

### BP-07 — `name` avoids reserved words

Type: mechanical · Level: must · Applies to: frontmatter · Section: Skill structure; Naming conventions; YAML frontmatter requirements

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#skill-structure>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#naming-conventions>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#yaml-frontmatter-requirements>

- Rule: `name` does not contain "anthropic" or "claude".
- Pass when: neither word occurs anywhere in `name`, in any case. The match
  is a substring match, as the article words it, so a name such as
  `claudette-tools` fails too. n/a when `name` is missing.
- Fix: rename without either word.

### BP-08 — `description` is non-empty

Type: mechanical · Level: must · Applies to: frontmatter · Section: Skill structure; YAML frontmatter requirements

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#skill-structure>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#yaml-frontmatter-requirements>

- Rule: the frontmatter has a non-empty `description`.
- Pass when: `description` is a string with visible characters.
- Fix: add a description stating what the skill does and when to use it.

### BP-09 — `description` at most 1024 characters

Type: mechanical · Level: must · Applies to: frontmatter · Section: Skill structure; YAML frontmatter requirements

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#skill-structure>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#yaml-frontmatter-requirements>

- Rule: the resolved description is 1024 characters or fewer.
- Pass when: the length after YAML resolution (folded or literal blocks
  joined) is at most 1024. n/a when `description` is missing.
- Fix: cut detail into the body; keep capabilities and triggers.

### BP-10 — `description` has no XML tags

Type: mechanical · Level: must · Applies to: frontmatter · Section: Skill structure; YAML frontmatter requirements

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#skill-structure>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#yaml-frontmatter-requirements>

- Rule: the description contains no XML tag.
- Pass when: `description` has no element tag (`<b>`, `</b>`, `<br/>`,
  `<skill-dir>`); comparison text such as `x <= 5` is not a tag. n/a when it
  is missing.
- Fix: write placeholders in plain words instead of angle brackets.

### BP-11 — `description` says what and when

Type: judgment · Level: should · Applies to: frontmatter · Section: Skill structure; Writing effective descriptions

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#skill-structure>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions>

- Rule: the description states what the skill does and when to use it. This
  applies whatever the invocation mode, user-invoked skills included; the
  article makes no exception.
- Pass when: it holds at least one capability statement and an explicit
  trigger clause ("Use when ...", or a named context).
- Fail when: either part is missing.
- Fix: add the missing half, for example "Use when the user mentions PDFs or
  forms."

### BP-12 — Name form: gerund preferred

Type: judgment · Level: consider · Applies to: frontmatter · Section: Naming conventions

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#naming-conventions>

- Rule: a gerund name (`processing-pdfs`) is preferred; a noun phrase
  (`pdf-processing`) or action form (`process-pdfs`) is acceptable.
- Pass when: the name follows one of the three forms.
- Fail when: the name follows none of them, for example an opaque code or a
  bare adjective.
- Fix: rename to a gerund form that names the activity.

### BP-13 — No vague or generic names

Type: judgment · Level: should · Applies to: frontmatter · Section: Naming conventions

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#naming-conventions>

- Rule: the name says what the skill does. The article's vague examples are
  helper, utils, and tools; its overly generic ones are documents, data, and
  files.
- Pass when: the name names a concrete activity or object (`processing-pdfs`,
  `analyzing-spreadsheets`). n/a when `name` is missing.
- Fail when: the name, read alone, could fit many unrelated skills: generic
  words like the article's examples, or equally empty ones (`misc`,
  `common`, `my-helper`, `general-tools`, `helper-v2`).
- Fix: name the concrete job, such as `analyzing-spreadsheets`.

### BP-14 — One naming pattern across the collection

Type: judgment · Level: should · Applies to: sibling skills · Section: Naming conventions

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#naming-conventions>

- Rule: skills in one collection share one naming form.
- Judge only the target. Siblings are the directories next to the target that
  hold a `SKILL.md`; cite their names as evidence, never as failures. A
  sibling whose name breaks BP-05 counts toward no form.
- A form dominates when at least two siblings share it and no other form has
  as many.
- Pass when: the target's name follows the dominant form. n/a when no form
  dominates, including when the target has fewer than two valid siblings.
- Fail when: the target's name deviates from the dominant form with no stated
  reason. Location: the `name` line of the target's `SKILL.md`.
- Fix: rename the target to the dominant form.

### BP-15 — Description in third person

Type: judgment · Level: must · Applies to: frontmatter · Section: Writing effective descriptions

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions>

- Rule: the description speaks about the skill, never as it ("I can ...") or
  to the reader ("you can ...").
- Pass when: no first- or second-person phrasing addresses the reader. Verb
  openings ("Processes Excel files ...", "Extract text ...") pass, and so do
  quoted user phrases used as triggers.
- Fail when: the description uses I, me, my, we, our, you, or your in its own
  voice.
- Fix: rewrite as "Processes ...; use when ...".

### BP-16 — Description is specific, with key terms

Type: judgment · Level: must · Applies to: frontmatter · Section: Writing effective descriptions

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions>

- Rule: the description gives enough detail for Claude to pick this skill
  among many: it names concrete operations and the terms a user would type.
- Pass when: it names at least two concrete operations or objects and at
  least one trigger term (file type, product, keyword) that sets it apart from
  neighbouring skills.
- Fail when: it relies on generic words only (help, process, data, files).
- Fix: list the concrete operations and file types, for example "Extracts
  text and tables from PDF files, fills forms".

### BP-17 — Body under 500 lines

Type: mechanical · Level: should · Applies to: body · Section: Progressive disclosure patterns; Token budgets

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#progressive-disclosure-patterns>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#token-budgets>

- Rule: keep the body under 500 lines.
- Pass when: the body has fewer than 500 lines.
- Fix: move detailed or rarely needed sections into linked reference files.

### BP-18 — SKILL.md is an overview; details live in files

Type: judgment · Level: should · Applies to: body, reference files · Section: Progressive disclosure patterns; Token budgets

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#progressive-disclosure-patterns>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#token-budgets>

- Rule: the body holds core instructions; long reference material sits in
  separate files, each linked with a cue saying what it holds or when to read
  it.
- Pass when: a short skill stays single-file, or detail is split with clear
  pointers.
- Fail when: the body holds long reference material needed only for some
  tasks; a linked file has no cue; or the body is approaching the 500-line
  limit (400 lines or more) while holding content that could move to a
  reference file. Over 500 lines is BP-17's.
- Fix: move the material to `references/<topic>.md` and link it with one line
  naming when to read it.

### BP-19 — Organize references by domain

Type: judgment · Level: should · Applies to: reference files · Section: Pattern 2: Domain-specific organization; Runtime environment

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#pattern-2-domain-specific-organization>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#runtime-environment>

- Rule: a skill covering several domains or tasks keeps each in its own file,
  with directories organized by domain or feature, so a task loads only what
  it needs.
- Pass when: references are split per domain or feature and SKILL.md routes to
  each. n/a for a single-domain skill.
- Fail when: one file mixes domains, or file names are generic.
- Fix: split into one file per domain (`references/finance.md`,
  `references/sales.md`) and route to each.

### BP-20 — Conditional details behind conditional links

Type: judgment · Level: consider · Applies to: body · Section: Pattern 3: Conditional details

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#pattern-3-conditional-details>

- Rule: basic content stays inline; rare-case content is linked with its
  condition.
- Pass when: rarely needed content sits behind a link whose cue names the
  condition. n/a when the skill has no rare-case content.
- Fail when: rare-case detail sits in the main path, or links lack a
  condition.
- Fix: move the rare case out and link it as "For <case>: see <file>".

### BP-21 — References one level deep

Type: mechanical · Level: should · Applies to: reference files · Section: Avoid deeply nested references

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-deeply-nested-references>

- Rule: every reference file is linked directly from SKILL.md, not reached
  only through another file.
- Pass when: every reference file, of any type, is directly linked. n/a when
  there are no reference files.
- Fix: link the file from SKILL.md with a line saying when to read it.

### BP-22 — Table of contents in long reference files

Type: mechanical · Level: should · Applies to: reference files · Section: Structure longer reference files with a table of contents

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#structure-longer-reference-files-with-table-of-contents>

- Rule: a reference file over 100 lines opens with a table of contents.
  Markdown and plain-text reference files are checked; data files such as
  JSON cannot carry a table of contents.
- Pass when: each such file has a "Contents" or "Table of contents" line
  (a heading in Markdown) in its first 30 lines, or at least three in-page
  anchor links before its second heading. n/a when no such file exceeds 100
  lines.
- Fix: add a contents list of anchor links right after the title.

## Workflows and feedback loops (BP-23 to BP-25)

### BP-23 — Complex tasks as ordered steps

Type: judgment · Level: should · Applies to: body, reference files · Section: Use workflows for complex tasks

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-workflows-for-complex-tasks>

- Rule: a procedure of three or more dependent actions is a numbered sequence.
  A step is an action the agent performs (run a command, write or edit a file,
  ask the user, decide a branch). Reading input counts as a step only when the
  instructions name it as one.
- Pass when: each such procedure is numbered, one action per step. n/a when
  the skill has no multi-step procedure.
- Fail when: the procedure is running prose, or the next step is ambiguous.
- Fix: rewrite it as numbered steps.

### BP-24 — Copyable checklist for long workflows

Type: judgment · Level: should · Applies to: body, reference files · Section: Use workflows for complex tasks

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-workflows-for-complex-tasks>

- Rule: a particularly complex workflow comes with a checklist Claude copies
  and ticks off as it works (in its response or its task list).
- Particularly complex: a workflow whose steps depend on each other (a later
  step uses an earlier step's output or result) and that either has five or
  more steps or has a validation gate that sends work back to an earlier
  step. Five independent steps with no branching or gate are not
  particularly complex; a step that repeats itself until its own check passes
  is BP-25's feedback loop, not a gate.
- Pass when: every particularly complex workflow has a `- [ ]` checklist and
  an instruction to copy and tick it. n/a when no workflow is particularly
  complex.
- Fail when: a particularly complex workflow has no checklist.
- Fix: add a fenced checklist and "Copy this checklist and tick items off".

### BP-25 — Feedback loop for quality-critical output

Type: judgment · Level: should · Applies to: body, scripts · Section: Implement feedback loops

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#implement-feedback-loops>

- Rule: run a validator, fix, and repeat; proceed only once validation passes.
- Pass when: the workflow names a validator (script or checklist), says to fix
  and re-run on failure, and gates progress on passing. n/a when output
  quality is not at stake.
- Fail when: output is produced with no check, or the check has no retry.
- Fix: add "Run <validator>; if it fails, fix and re-run; continue only when
  it passes."

## Content guidelines (BP-26 to BP-27)

### BP-26 — No time-sensitive information

Type: judgment · Level: should · Applies to: body, reference files · Section: Avoid time-sensitive information

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-time-sensitive-information>

- Rule: no instruction depends on today's date; legacy approaches live in a
  marked old-patterns section.
- Pass when: dates appear only as historical labels or in an old-patterns
  section.
- Fail when: behaviour switches on a calendar date ("before <month year> use
  X"), or deprecated material sits in the main path.
- Fix: state the current method and move the old one into a collapsed
  old-patterns section.

### BP-27 — Consistent terminology

Type: judgment · Level: should · Applies to: whole skill · Section: Use consistent terminology

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-consistent-terminology>

- Rule: one term per concept everywhere in the skill, including comments and
  text in `assets/` files.
- Pass when: each key concept has one name.
- Fail when: one concept goes by two or more interchangeable terms (field,
  box, control).
- Fix: pick one term and replace the others.

## Common patterns (BP-28 to BP-31)

### BP-28 — Output templates with stated strictness

Type: judgment · Level: should · Applies to: body, reference files · Section: Template pattern

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#template-pattern>

- Rule: when output format matters, give a template and say whether it is
  exact or adaptable.
- Pass when: a template exists and its strictness fits the need (exact for
  data formats). n/a when the skill sets no output format.
- Fail when: a required format is described only in prose, or strictness is
  unstated.
- Fix: add a template and mark it "use exactly" or "adapt as needed".

### BP-29 — Concrete examples

Type: judgment · Level: should · Applies to: body, reference files · Section: Examples pattern

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#examples-pattern>

- Rule: every example is concrete, not abstract; output whose quality
  depends on style also gets input/output example pairs.
- Pass when: every example uses realistic values, and style-dependent output
  has example pairs. n/a when the skill has no examples and no style-dependent
  output.
- Fail when: an example is placeholders only (`<thing>`, "some value"), or a
  stylistic output has no example pair.
- Fix: add one or two input/output pairs with realistic values.

### BP-30 — Explicit decision points

Type: judgment · Level: should · Applies to: body, reference files · Section: Conditional workflow pattern

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#conditional-workflow-pattern>

- Rule: a branching workflow names each condition and its target.
- Pass when: each branch reads like "Editing existing content? Go to Editing".
  n/a when the workflow does not branch.
- Fail when: the reader must infer which path applies.
- Fix: state each branch's condition and the section it leads to.

### BP-31 — Large workflows in their own files

Type: judgment · Level: consider · Applies to: body · Section: Conditional workflow pattern

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#conditional-workflow-pattern>

- Rule: a large or complicated workflow moves to its own file, and SKILL.md
  says which file to read for which task. One such workflow is enough.
- Pass when: every workflow of about 20 or more lines, or with many steps, is
  in its own file and routed by task, or every workflow is short. n/a when the
  skill has no workflow.
- Fail when: a large workflow sits inline in the body.
- Fix: move it into its own reference file and route to it by task.

## Evaluation and iteration (BP-32 to BP-39)

### BP-32 — Evaluations first, with a baseline

Type: judgment · Level: should · Applies to: evaluation material · Section: Build evaluations first

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#build-evaluations-first>

- Rule: evaluations come before extensive instructions, measured against a
  no-skill baseline; the instructions are the minimum that closes the observed
  gaps and passes the evaluations.
- Pass when: evaluation material records baseline results (or gaps seen
  without the skill) and runs that compare against them, and the instructions
  map to recorded gaps or scenarios.
- Fail when: evaluations are absent, exist with no baseline or gap evidence,
  or the skill carries sizeable instruction sections that no recorded gap or
  scenario calls for.
- Fix: run the scenarios without the skill, record the gaps, and compare
  later runs against them.

### BP-33 — At least three evaluations

Type: judgment · Level: should · Applies to: evaluation material · Section: Build evaluations first

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#build-evaluations-first>

- Rule: there are at least three evaluation scenarios.
- Pass when: three or more distinct scenarios exist, in any format.
- Fail when: fewer than three scenarios exist.
- Fix: add scenarios until there are three, covering distinct branches.

### BP-34 — Evaluation case structure

Type: judgment · Level: consider · Applies to: evaluation material · Section: Build evaluations first

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#build-evaluations-first>

- Rule: each scenario names the skill, the query, any input files, and the
  expected behaviours that grade it.
- Pass when: every scenario has a query and a list of expected behaviours.
  n/a when there are no scenarios (BP-33 reports that).
- Fail when: a scenario lacks the query or the expected behaviours.
- Fix: add the missing field to each scenario.

### BP-35 — Author with one instance, test with another

Type: judgment · Level: should · Applies to: evaluation material · Section: Develop Skills iteratively with Claude

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#develop-skills-iteratively-with-claude>

- Rule: one Claude instance refines the skill; a fresh instance tests it on
  real tasks; observations flow back.
- Pass when: notes show fresh-instance test sessions and changes traced to
  observed behaviour.
- Fail when: there is no record of testing by an instance that did not write
  the skill.
- Fix: test with a fresh session that has only the skill loaded and log what
  it did.

### BP-36 — Test with real usage scenarios

Type: judgment · Level: should · Applies to: evaluation material · Section: Develop Skills iteratively with Claude

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#develop-skills-iteratively-with-claude>

- Rule: tests include actual tasks, not only synthetic prompts.
- Pass when: at least one scenario or run note comes from a real task with
  real inputs.
- Fail when: every test is a toy prompt.
- Fix: add a scenario taken from a real request.

### BP-37 — Incorporate team feedback

Type: judgment · Level: should · Applies to: evaluation material · Section: Develop Skills iteratively with Claude

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#develop-skills-iteratively-with-claude>

- Rule: a shared skill folds in teammates' observations.
- Pass when: feedback notes exist and changes reflect them. n/a when nothing
  shows the skill is shared: it ships in no plugin, marketplace, or team
  repository, and the user has not said others use it.
- Fail when: a shared skill has no feedback record.
- Fix: collect teammates' notes on triggering and clarity, and record the
  resulting changes.

### BP-38 — Observe how Claude navigates the skill

Type: judgment · Level: should · Applies to: evaluation material, whole skill · Section: Observe how Claude navigates Skills

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#observe-how-claude-navigates-skills>

- Rule: watch real runs for reading order, missed links, and files read every
  time or never; restructure from what you see.
- Pass when: run notes record navigation observations and resulting changes.
- Fail when: no run notes cover navigation, or notes show a missed link that
  was never made more prominent.
- Fix: log which files each test run opened, then promote or cut accordingly.

### BP-39 — Every bundled file is reachable

Type: mechanical · Level: consider · Applies to: bundled files · Section: Observe how Claude navigates Skills

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#observe-how-claude-navigates-skills>

- Rule: a file nothing points to is unnecessary or badly signposted.
- Pass when: every bundled file (except `agents/` and licence files) is named,
  by path, file name, module name, or a containing folder at least two levels
  deep, in SKILL.md or in a file reachable from it. n/a when there are no such
  files.
- Fix: name the file in SKILL.md with the condition for using it, or delete
  it.

## Anti-patterns to avoid (BP-40 to BP-41)

### BP-40 — Forward-slash paths only

Type: mechanical · Level: must · Applies to: whole skill · Section: Avoid Windows-style paths; Runtime environment

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-windows-style-paths>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#runtime-environment>

- Rule: every file path uses forward slashes.
- Pass when: no text file contains a drive-letter path or a backslash path to
  a file with a common extension.
- Fix: replace backslashes in the path with forward slashes.

### BP-41 — One default, not a menu

Type: judgment · Level: should · Applies to: body, reference files · Section: Avoid offering too many options

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-offering-too-many-options>

- Rule: recommend one default and name an alternative only for a stated
  exception.
- Pass when: each choice has one default, and any alternative is tied to a
  condition.
- Fail when: two or more interchangeable options appear with no default.
- Fix: keep one default and turn the rest into "for <case>, use <tool>
  instead".

## Skills with executable code (BP-42 to BP-55)

Rules BP-42 to BP-51 are n/a for a skill that bundles no scripts, unless the
rule also covers the body and the body runs code.

### BP-42 — Scripts handle errors

Type: judgment · Level: should · Applies to: scripts · Section: Solve, don't defer

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#solve-dont-punt>

- Rule: scripts catch foreseeable failures (missing file, permissions, bad
  input) and recover or exit with a helpful message.
- Pass when: each file, network, or subprocess error path has a clear message
  or a stated fallback.
- Fail when: a foreseeable error ends in a raw traceback or a silent wrong
  result.
- Fix: catch the error and print what failed and what to do.

### BP-43 — No unexplained constants

Type: judgment · Level: should · Applies to: executable code · Section: Solve, don't defer

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#solve-dont-punt>

- Rule: every configuration value carries its reason. This covers all
  executable code the skill ships, in `scripts/` or elsewhere (for example an
  executable shim in `assets/`), but not values in document or data
  templates.
- Pass when: each tunable number (timeout, retry count, limit, threshold) has
  a comment or nearby text explaining it.
- Fail when: a tunable number has no explanation.
- Fix: add a one-line comment giving the reason for the value.

### BP-44 — Bundled scripts for deterministic work

Type: judgment · Level: should · Applies to: body, scripts · Section: Provide utility scripts; Runtime environment

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#provide-utility-scripts>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#runtime-environment>

- Rule: deterministic, repeated operations ship as scripts instead of code
  Claude writes each time.
- Pass when: validation, parsing, and conversion steps call bundled scripts.
  n/a when the skill has no deterministic operation.
- Fail when: the instructions ask Claude to write a non-trivial validator,
  parser, or converter that runs the same way every time.
- Fix: bundle that code in `scripts/` and tell Claude to run it.

### BP-45 — Run or read, stated per script

Type: judgment · Level: should · Applies to: body, reference files · Section: Provide utility scripts; Runtime environment

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#provide-utility-scripts>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#runtime-environment>

- Rule: each script mention makes clear whether to execute it or read it,
  and utility scripts are executed by default; reading a script as reference
  is for an algorithm Claude must adapt.
- Pass when: each mention has a run verb or a command line, or an explicit
  read cue with a reason to read rather than run.
- Fail when: a mention leaves the intent ambiguous, or tells Claude to read a
  utility script whose job running it would do.
- Fix: write "Run `scripts/x.py <args>`" or "Read `scripts/x.py` for the
  algorithm".

### BP-46 — Scripts are documented

Type: judgment · Level: should · Applies to: scripts, body · Section: Provide utility scripts

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#provide-utility-scripts>

- Rule: each script's purpose, invocation, and output format are stated.
- Pass when: SKILL.md, a reference, or the script header states all three.
- Fail when: the invocation or the output shape can only be learned from the
  code, or an instruction tells Claude to use a script for something it cannot
  do (wrong arguments, a capability the code lacks). Report that mismatch here
  only, not under BP-02 or BP-45.
- Fix: add a usage line and the output shape to SKILL.md or the docstring, or
  make the instruction match what the script does.

### BP-47 — Visual analysis for visual inputs

Type: judgment · Level: should · Applies to: body, scripts · Section: Use visual analysis

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-visual-analysis>

- Rule: when layout matters, render the input to an image and inspect it.
- Pass when: a render-and-inspect step exists. n/a when the skill handles no
  visual-layout input.
- Fail when: layout is inferred only from extracted text.
- Fix: add a step that renders pages to images and inspects them.

### BP-48 — Plan, validate, then apply risky changes

Type: judgment · Level: should · Applies to: body, scripts · Section: Create verifiable intermediate outputs

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#create-verifiable-intermediate-outputs>

- Rule: batch, destructive, complex-validation-rule, or high-stakes
  operations go through a plan file that a script validates before anything
  is applied.
- Pass when: such an operation writes a machine-checkable plan and validates
  it first. n/a when the skill has no such operation.
- Fail when: changes are applied directly with no pre-apply check.
- Fix: write the plan (for example `changes.json`), validate it with a
  script, apply, then verify.

### BP-49 — Specific validator errors

Type: judgment · Level: consider · Applies to: scripts · Section: Create verifiable intermediate outputs

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#create-verifiable-intermediate-outputs>

- Rule: validators name what failed and the valid options.
- Pass when: each error names the offending item and, where useful, the
  accepted values. n/a when the skill has no validator.
- Fail when: a validator emits only pass or fail, a bare exception, or a
  generic message.
- Fix: include the bad value and the allowed values in the message.

### BP-50 — Required packages listed

Type: judgment · Level: should · Applies to: body, scripts · Section: Package dependencies; Avoid assuming tools are installed

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#package-dependencies>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-assuming-tools-are-installed>

- Rule: SKILL.md names every required package and tool, with an install or
  run step; nothing is assumed installed. This covers what the bundled scripts
  need, including the runner a shebang names (for example `node` in
  `#!/usr/bin/env node`), and what the body tells Claude to use.
  BP-50 is about naming; availability on each surface is BP-51's.
- Pass when: each third-party import, external command, shebang runner, and
  body-named package appears in SKILL.md with its install or run step. A
  script's inline dependency block alone does not count. n/a when the skill
  needs nothing beyond the standard library and preinstalled shell tools.
- Fail when: a script relies on a package, tool, or runner SKILL.md never
  names, or the body says to use a package ("use the pdf library") with no
  install step.
- Fix: name the package or runner in SKILL.md with its install or run
  command.

### BP-51 — Packages fit the target surface

Type: judgment · Level: should · Applies to: body, scripts · Section: Package dependencies

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#package-dependencies>

- Rule: dependencies suit each runtime the skill targets. A target surface is
  a platform the skill runs on. The article names two: claude.ai, which can
  install packages from npm, PyPI, and GitHub, and the Claude API, which has
  no network and no runtime installation. A stated local agent environment
  with a shell (such as Claude Code) also counts, limited by what that host
  provides.
- Scope: every package and tool the skill needs, from scripts and from the
  body, checked against the stated surfaces. Naming them is BP-50's.
- Pass when: each package and tool is available on every stated surface (for
  example, no PyPI install on the no-network API surface), or the skill needs
  nothing beyond what every surface provides. n/a when the skill needs
  nothing beyond the standard library.
- Fail when: the skill needs runtime installation or network access while
  targeting a surface without them, or it depends on packages, network, or
  tools whose availability differs by surface and states no surface. A skill
  whose needs are available on every surface passes without stating one.
- Fix: state the target surfaces, or remove the dependency.

### BP-52 — Descriptive file names

Type: judgment · Level: should · Applies to: bundled files · Section: Runtime environment

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#runtime-environment>

- Rule: file names say what the file holds. The article applies this to
  every file Claude navigates, `assets/` included; its example is
  `form_validation_rules.md`, not `doc2.md`.
- Pass when: each file name, with its folder, tells what the file holds. n/a
  when there are no bundled files.
- Fail when: a name says nothing about the content: a generic or numbered
  stem (`doc2.md`, `file1.md`, `page1.md`, `notes.md`, `misc.py`,
  `output.md`) or a bare letter (`a.md`, `x.py`).
- Fix: rename after the content, such as `form_validation_rules.md`.

### BP-53 — Large resources as bundled files

Type: judgment · Level: should · Applies to: whole skill · Section: Runtime environment

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#runtime-environment>

- Rule: bundle the comprehensive resources the skill needs (complete API
  docs, extensive examples, datasets) as files; they cost nothing until read.
  Do not inline them in SKILL.md.
- Pass when: the resources the instructions rely on sit in bundled files.
- Fail when: large reference data is inlined in SKILL.md, or the instructions
  rely on documentation or data the skill neither bundles nor names a way to
  obtain (for example, only an external link to needed API docs).
- Fix: move the material into a bundled file, or bundle the missing docs, and
  link it.

### BP-54 — Test file access patterns

Type: judgment · Level: should · Applies to: evaluation material · Section: Runtime environment

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#runtime-environment>

- Rule: real requests confirm Claude finds the right bundled file.
- Pass when: a test exercises a request that needs a non-SKILL.md file and
  records that the right file was opened. n/a when the skill has no bundled
  files.
- Fail when: no test touches the bundled files.
- Fix: add a scenario that needs a reference file and record which file was
  read.

### BP-55 — Fully qualified MCP tool names

Type: judgment · Level: must · Applies to: body, reference files · Section: MCP tool references

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#mcp-tool-references>

- Rule: MCP tools are named with their server prefix.
- Pass when: every MCP tool reference is `Server:tool_name` (the article's
  form) or `mcp__server__tool_name` (a host format some agents use; accepted
  as an extension because it is equally fully qualified). n/a when the skill
  uses no MCP tools.
- Fail when: an MCP tool is named bare (`create_issue`).
- Fix: prefix the server, for example `GitHub:create_issue`.

## Retired rules

None. A rule the article drops stays listed here with its ID, the snapshot
date it was retired, and the reason; its ID is never reused.
