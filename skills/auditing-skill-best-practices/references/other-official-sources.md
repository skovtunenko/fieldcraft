# Other official sources catalogue

The second rule catalogue every audit grades against: hard requirements from
official Anthropic pages other than the best-practices article. A rule enters
only when breaking it makes a skill fail to upload, load, trigger, or run, or
creates a security risk. Rules are paraphrased; IDs (`OS-NN`) are stable and
never reused. No OS rule contradicts an article rule; where another official
page disagrees with the article, the catalogue follows the article (see
[Settled divergences](#settled-divergences)).

## Contents

- [Snapshot](#snapshot)
- [Terms](#terms)
- [Frontmatter and naming (OS-01 to OS-08)](#frontmatter-and-naming-os-01-to-os-08)
- [Body and runtime behaviour (OS-09 to OS-11)](#body-and-runtime-behaviour-os-09-to-os-11)
- [Security (OS-12 to OS-17)](#security-os-12-to-os-17)
- [Packaging (OS-18)](#packaging-os-18)
- [Settled divergences](#settled-divergences)
- [Retired rules](#retired-rules)

## Snapshot

- Snapshot date: 2026-11-10. Every source was fetched that day.
- Sources:
  - <https://code.claude.com/docs/en/skills> (Claude Code skills reference)
  - <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview>
  - <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise>
  - <https://platform.claude.com/docs/en/build-with-claude/skills-guide>
    (Skills API)
  - <https://platform.claude.com/docs/en/manage-claude/plugins-api>
  - <https://support.claude.com/en/articles/12512180-using-skills-in-claude>
  - <https://github.com/anthropics/skills> (`skill-creator` and its
    validator `scripts/quick_validate.py`)
  - <https://agentskills.io> (the Agent Skills open standard that the Claude
    Code docs link as the specification)
- Anchors are the heading's HTML `id` on the fetched page; GitHub links use
  the rendered heading slug or an `#L<line>` anchor on the file view.
- Excluded: advice (style, structure, evaluation process), and pages that
  contradict current docs, such as support article 12512198, which caps
  `description` at 200 characters. Refresh compares every source with its
  hash in [source-hashes.md](source-hashes.md) and re-checks the rules that
  cite a changed page.
- Rules: 18 (OS-01 to OS-18); 7 mechanical, 11 judgment; levels: 13 must,
  5 should, 0 consider
- Mechanical rules: OS-01, OS-02, OS-03, OS-04, OS-06, OS-08, OS-11.
  `scripts/check_mechanical.py` decides exactly this set.

## Terms

Every term of [best-practices-rules.md](best-practices-rules.md#terms)
applies unchanged (Level, Source, Type, Status, one defect one rule, Body,
Bundled files, Reference files). Additions:

- **Hosts**: where the requirement is enforced or the failure occurs: `all`,
  `Claude Code`, `API` (Skills API and the Messages API container),
  `claude.ai` (upload, including Cowork), `plugins` (plugin store upload on
  claude.ai or through the Plugins API). `all` on a rule from the Agent
  Skills specification means the rule is part of the format, even where
  Claude Code tolerates the violation.
- **Target hosts**: a host is targeted when the user names it, the skill
  states it (for example "runs in Claude Code"), or the layout shows it: a
  skill in the `skills` folder under `.claude/` or inside a plugin with
  `.claude-plugin/plugin.json` targets Claude Code (and `plugins` when it
  ships in a marketplace); a packaged ZIP, a Skills API call, or an upload
  instruction targets the API or claude.ai. With no signal, the target is
  `all` only: every rule whose Hosts lists specific hosts is n/a, and the
  report header states the assumption.
- **Host-scoped status**: a judgment rule whose Hosts includes no target host
  is n/a, with the reason in Evidence. Each mechanical rule decides its own
  applicability, stated in its n/a clause.
- **Portable skill**: a skill whose target hosts include claude.ai or the API,
  or that is packaged with `package_skill.py`.
- **Injected command**: a `` !`command` `` placeholder or a ` ```! ` block in
  the body (Claude Code dynamic context injection).

## Frontmatter and naming (OS-01 to OS-08)

### OS-01 — `name` has no leading, trailing, or doubled hyphen

Type: mechanical · Level: must · Applies to: frontmatter · Hosts: all

Source: <https://agentskills.io/specification#name-field>; <https://github.com/anthropics/skills/blob/main/skills/skill-creator/scripts/quick_validate.py#L67>

- Rule: `name` does not start or end with `-` and contains no `--`. Extends
  BP-05, which checks only the character set.
- Why: the specification and the packaging validator reject such names, so
  the skill cannot be packaged or uploaded.
- Pass when: none of the three holds. n/a when `name` is missing (BP-04
  reports it).
- Fail when: `name` starts with `-`, ends with `-`, or contains `--`.
- Fix: drop the edge hyphen or collapse `--` to `-`, and rename the folder to
  match (OS-02).

### OS-02 — `name` equals the skill folder name

Type: mechanical · Level: must · Applies to: frontmatter · Hosts: all

Source: <https://agentskills.io/specification#name-field>; <https://support.claude.com/en/articles/12512180-using-skills-in-claude#h_5499f1b465>

- Rule: the frontmatter `name` is identical (case-sensitive) to the name of
  the directory that holds `SKILL.md`.
- Why: claude.ai lists a folder-name mismatch as an upload error, and the
  specification requires the match. Claude Code accepts a mismatch: `name`
  sets the command and the folder name also invokes the skill.
- Pass when: the two are equal. n/a when `name` is missing (BP-04), or when
  `SKILL.md` sits at a plugin root (the directory holds
  `.claude-plugin/plugin.json`; it is the plugin, not a skill folder).
- Fail when: the two differ.
- Fix: rename the folder or the `name` so they match.

### OS-03 — Frontmatter starts on line 1 and parses

Type: mechanical · Level: must · Applies to: frontmatter · Hosts: all

Source: <https://code.claude.com/docs/en/skills#frontmatter-reference>; <https://code.claude.com/docs/en/skills#skill-not-triggering>

- Rule: the first line of `SKILL.md` is exactly `---`, a closing `---`
  follows, and the text between parses as a YAML mapping. Extends BP-04,
  which reports a missing block; OS-03 reports the silent cases.
- Why: in Claude Code an opening `---` after line 1 turns the frontmatter
  into body text, and YAML that does not parse loads the skill with no
  fields, so it never triggers; uploaders reject both.
- Pass when: none of the failures below is found. n/a when `SKILL.md` has no
  `---` block at all (BP-04 reports it).
- Fail when: only blank lines or a byte-order mark precede the opening
  `---`; the block is empty; or the block holds an error every YAML parser
  rejects: a top-level line that is not a `key: value` entry (a non-mapping
  document included), a duplicate top-level key, a line indented with a tab,
  a quoted value that is not closed or has text after its closing quote, a
  plain (unquoted) value that starts with a backtick, `@`, `%`, `,`, or a
  `-` or `?` followed by a space, or a plain value that contains a colon
  followed by a space or ends with `:`. Flow values
  (`[...]`, `{...}`) are not parsed; judge them by reading.
- Fix: move the block to line 1, and quote a value that holds a colon and a
  space or starts with a reserved character (`description: "Use when: ..."`).

### OS-04 — Every frontmatter key is a recognised field

Type: mechanical · Level: must · Applies to: frontmatter · Hosts: all

Source: <https://code.claude.com/docs/en/skills#frontmatter-reference>; <https://code.claude.com/docs/en/skills#using-skill-frontmatter-outside-claude-code>

- Rule: every top-level key is one of the Claude Code frontmatter fields as
  of the snapshot: `name`, `description`, `when_to_use`, `argument-hint`,
  `arguments`, `disable-model-invocation`, `user-invocable`,
  `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context`,
  `agent`, `background`, `hooks`, `paths`, `shell`, `metadata`, `license`,
  `compatibility`.
- Why: Claude Code ignores an unknown key without an error, so a misspelled
  field silently loses its effect, and every other host rejects the file.
- Pass when: every top-level key is in the set. n/a when there is no
  frontmatter block.
- Fail when: any other top-level key appears, for example
  `disable_model_invocation`, `allowed_tools`, a top-level `version`, or
  `dependencies`.
- Fix: correct the spelling, or move custom data under `metadata`.

### OS-05 — Portable skills use only specification fields and features

Type: judgment · Level: must · Applies to: frontmatter, body · Hosts: claude.ai, API

Source: <https://code.claude.com/docs/en/skills#using-skill-frontmatter-outside-claude-code>; <https://github.com/anthropics/skills/blob/main/skills/skill-creator/scripts/quick_validate.py#L42>

- Rule: a portable skill's frontmatter uses only `name`, `description`,
  `license`, `compatibility`, `metadata`, and `allowed-tools`, and its body
  relies on no Claude Code-only feature: injected commands, `$ARGUMENTS` or
  `$name` substitution, `${CLAUDE_SKILL_DIR}` and other `${CLAUDE_*}`
  variables.
- Why: outside Claude Code, packaging or upload fails on any other key, and
  Claude Code-only body features do nothing.
- Pass when: no other key and no such feature appears, or each feature sits
  in a section marked Claude Code-only with a portable fallback. n/a when the
  target hosts are Claude Code only.
- Fail when: a portable skill has another key, or its instructions depend on
  a Claude Code-only feature.
- Fix: drop the Claude Code-only keys and replace injected context with an
  explicit instruction to run the command, or state Claude Code as the only
  target.

### OS-06 — `metadata` and `compatibility` are well-formed

Type: mechanical · Level: must · Applies to: frontmatter · Hosts: all

Source: <https://agentskills.io/specification#metadata-field>; <https://agentskills.io/specification#compatibility-field>; <https://code.claude.com/docs/en/skills#frontmatter-reference>

- Rule: `metadata`, when present, maps string keys to string values;
  `compatibility`, when present, is a string of 1 to 500 characters.
- Why: the specification types both fields; Claude Code drops a `metadata`
  value that is not a map, and an unquoted `version: 0.1` is a number, not a
  string.
- Pass when: every `metadata` entry is `key: value` with a string key and a
  string value, and `compatibility` is a string of 1 to 500 characters. A
  value counts as a string when it is quoted, a block scalar, or a plain
  value that no YAML parser types as a number, boolean, null, or date. n/a
  when both fields are absent. A flow-style `metadata` (`{...}`) is not
  evaluated; judge it by reading.
- Fail when: `metadata` is empty, a scalar, or a list; a value is a number,
  boolean (`true`, `yes`, `on`), null, date, list, or nested map; or
  `compatibility` is not a string or is longer than 500 characters.
- Fix: quote the value (`version: "0.1"`), flatten nested data, shorten
  `compatibility`.

Scope note: this rule checks metadata types, not a version numbering policy.
Both `version: "0.1"` and `version: "2026.11.06.1"` are string entries and
pass this type check. A version entry is optional under the specification;
its presence, numbering scheme, and raise policy are repository conventions.
Do not recommend changing a quoted version solely because it uses either form.

### OS-07 — `description` has no angle brackets

Type: judgment · Level: must · Applies to: frontmatter · Hosts: claude.ai

Source: <https://github.com/anthropics/skills/blob/main/skills/skill-creator/scripts/quick_validate.py#L79-L81>; <https://support.claude.com/en/articles/12512180-using-skills-in-claude#h_5499f1b465>

- Rule: the resolved `description` contains no `<` and no `>`. Stricter than
  BP-10, which allows comparison text such as `<=`; both can pass together.
- Why: the packaging validator rejects any angle bracket, and claude.ai lists
  invalid description characters as an upload error.
- Pass when: neither character occurs. n/a when `description` is missing, or
  the target hosts do not include claude.ai. The check is exact; only the
  host decision is judgment.
- Fail when: a portable skill's `description` contains `<` or `>`.
- Fix: write "at most", "greater than", or a placeholder in plain words.

### OS-08 — `description` plus `when_to_use` within 1,536 characters

Type: mechanical · Level: must · Applies to: frontmatter · Hosts: Claude Code

Source: <https://code.claude.com/docs/en/skills#frontmatter-reference>; <https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short>

- Rule: the resolved `description` and `when_to_use` together are at most
  1,536 characters. Applies with BP-09 (1,024 on `description` alone).
- Why: Claude Code appends `when_to_use` to `description` in the skill
  listing and truncates the combined text, so trigger words past the cap
  never reach the model. 1,536 is the default listing cap; a user can change
  it, the skill cannot.
- Pass when: the sum is at most 1,536. n/a when `when_to_use` is absent; its
  presence shows that the skill targets Claude Code.
- Fail when: the sum exceeds 1,536.
- Fix: cut `when_to_use` and put the key use case first in `description`.

## Body and runtime behaviour (OS-09 to OS-11)

### OS-09 — Must-hold instructions sit in the first 5,000 tokens

Type: judgment · Level: should · Applies to: body · Hosts: Claude Code

Source: <https://code.claude.com/docs/en/skills#skill-content-lifecycle>; <https://code.claude.com/docs/en/skills#claude-stops-following-a-skill>

- Rule: the rules that must survive a long session come first in `SKILL.md`.
- Why: after auto-compaction Claude Code re-attaches only the first 5,000
  tokens of each invoked skill (25,000 across skills, newest first).
- Pass when: the body is under about 20,000 characters (5,000 tokens at four
  characters per token), or every must-hold rule, gate, and safety
  constraint appears before that point. n/a when the target hosts exclude
  Claude Code.
- Fail when: the body exceeds the estimate and a must-hold rule (a safety
  constraint, a validation gate, an output contract) appears only after it.
- Fix: move the must-hold rules to the top, or move later material into
  reference files.

### OS-10 — Injected commands cannot abort the skill

Type: judgment · Level: must · Applies to: body · Hosts: Claude Code

Source: <https://code.claude.com/docs/en/skills#when-an-injected-command-fails>; <https://code.claude.com/docs/en/skills#how-injected-commands-run>; <https://code.claude.com/docs/en/skills#permission-checks-on-injected-commands>

- Rule: each injected command (a) reaches bundled files through
  `${CLAUDE_SKILL_DIR}`, (b) ends in `|| true` when a non-zero exit is an
  expected result (exit 1 of search and comparison commands is already
  tolerated; 2 or higher is not), and (c) is pre-approved by a scoped
  `allowed-tools` rule.
- Why: a failing injected command aborts the whole invocation, so Claude
  never sees the skill; outside auto mode a command whose permission check
  returns anything other than allow aborts instead of prompting. The user's
  own permission rules can also allow it, but the skill text does not show
  them, and deny and ask rules still override `allowed-tools`.
- Pass when: every injected command meets (a) to (c). n/a when the body has
  no injected command.
- Fail when: an injected command uses a relative path to a bundled file, can
  exit non-zero in normal use without `|| true`, or has no matching
  `allowed-tools` entry.
- Fix: prefix bundled paths with `${CLAUDE_SKILL_DIR}/`, append `|| true`,
  and add a scoped `allowed-tools` rule such as `Bash(git status *)`.

### OS-11 — Every linked file exists

Type: mechanical · Level: must · Applies to: body, reference files · Hosts: all

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise#what-to-evaluate>; <https://agentskills.io/specification#file-references>

- Rule: every relative Markdown link in `SKILL.md` and in Markdown reference
  files, inline or reference-style (`[ref]: path`), resolves to an existing file or folder inside the skill directory.
  Complements BP-21 and BP-39, which check that files are linked.
- Why: the enterprise evaluation guide counts a reference to a missing file
  as an isolation failure; the skill breaks wherever it is installed.
- Pass when: each link target with no URL scheme and not a pure `#anchor`,
  with any `#fragment` removed and resolved against the linking file's
  folder, exists inside the skill root after symlinks are followed. A skill
  folder that is itself a symlink is fine. Links inside code fences and inline
  code are examples, not links. n/a when there are no such links.
- Fail when: a target is missing or resolves outside the skill root.
- Fix: correct the path, add the file, or remove the link; replace a symlink
  that leaves the skill with the real file.

## Security (OS-12 to OS-17)

### OS-12 — File access stays inside the skill and the user's inputs

Type: judgment · Level: should · Applies to: body, reference files, scripts · Hosts: all

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise#risk-tier-assessment>; <https://agentskills.io/specification#file-references>

- Rule: bundled files are referenced relative to the skill root;
  instructions and scripts reach outside the skill directory only for the
  user's named inputs, the working tree, or a location the stated purpose
  requires and names.
- Why: the enterprise risk assessment flags paths outside the skill, broad
  globs, and `../` traversal as a security risk.
- Pass when: every path is skill-relative, a user-supplied input, or a named
  outside location the purpose requires. n/a when the skill touches no files.
- Fail when: a path traverses out of the skill with `../`, an absolute path
  points into user or system locations (`~/.ssh`, `~/.aws`, `/etc`) without a
  stated need, or a glob scans from `/` or `~`.
- Fix: use skill-relative paths, take outside locations as arguments, narrow
  the glob.

### OS-13 — No hardcoded credentials

Type: judgment · Level: must · Applies to: whole skill · Hosts: all

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise#review-checklist>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise#risk-tier-assessment>

- Rule: no API key, token, password, private key, or connection string with a
  secret appears in any skill file, examples included.
- Why: the enterprise review checklist requires credentials to come from
  environment variables or a secret store; a shipped secret leaks to every
  user of the skill.
- Pass when: secrets are referenced by variable or store name only, and
  examples use obvious placeholders (`$API_KEY`, `YOUR_TOKEN`). Never n/a.
- Fail when: a literal that looks like a live secret (provider key prefixes
  such as `sk-`, `ghp_`, `AKIA`; a PEM block; `password=` with a value)
  appears in any file.
- Fix: delete the secret, rotate it, and read it from an environment
  variable.

### OS-14 — Network access is stated and its destinations named

Type: judgment · Level: should · Applies to: body, reference files, scripts · Hosts: all

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise#review-checklist>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#security-considerations>

- Rule: every network call the skill makes or instructs (URLs, `curl`,
  `wget`, `fetch`, `requests`, `urllib`, HTTP clients, `git clone`) is stated
  in `SKILL.md` with its destination and purpose, and fetched content is
  treated as data, never as instructions. BP-51 covers whether the network
  is available; this rule covers disclosure and trust.
- Why: the overview warns that fetched content may carry malicious
  instructions, and the enterprise checklist asks for every external call.
- Pass when: each call is listed with destination and purpose, and no
  instruction tells Claude to obey fetched content. n/a when the skill makes
  no network call.
- Fail when: a script or instruction contacts a host the body never names, a
  destination is built from untrusted input, or fetched text is executed or
  followed as instructions.
- Fix: list each destination and purpose in `SKILL.md`; treat fetched
  content as data to parse.

### OS-15 — No hidden, adversarial, or off-purpose behaviour

Type: judgment · Level: must · Applies to: whole skill · Hosts: all

Source: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise#review-checklist>; <https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md#principle-of-lack-of-surprise>; <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise#skill-content-scanning>

- Rule: the skill holds no directive to ignore safety rules, hide actions
  from the user, behave differently for specific inputs, or move sensitive
  data out (including by encoding it into replies), and what its scripts and
  instructions do matches its description.
- Why: skill content scanning on claude.ai and Cowork Enterprise blocks such
  skills, and skill-creator requires that a skill never surprise the user.
- Pass when: every action the skill takes is visible to the user and covered
  by the description. Never n/a.
- Fail when: such a directive exists, or a script or step does something the
  description does not state (an undisclosed upload, a deletion, a
  persistence mechanism, obfuscated or encoded code).
- Fix: remove the directive or the off-purpose code, or state the behaviour
  in the description and body.

### OS-16 — Scripts never wait for interactive input

Type: judgment · Level: must · Applies to: scripts, body · Hosts: all

Source: <https://agentskills.io/skill-creation/using-scripts#avoid-interactive-prompts>

- Rule: all input reaches scripts and instructed commands through flags,
  environment variables, or stdin.
- Why: agents run in non-interactive shells, so a command that waits for a
  prompt, password, or confirmation hangs.
- Pass when: no bundled script or instructed command reads from the terminal
  without a non-interactive path. n/a when the skill runs no code or
  commands.
- Fail when: a script calls `input()`, `getpass`, `read -p`, `select`, or a
  confirmation menu, or the body runs a tool that prompts by default without
  its non-interactive flag (`npm init` without `-y`, `apt-get install`
  without `-y`), and no flag, variable, or `isatty` guard bypasses it.
- Fix: replace the prompt with a flag or variable, and add `--yes` or
  `--force` where confirmation guards a destructive action.

### OS-17 — `allowed-tools` grants only what the steps need

Type: judgment · Level: should · Applies to: frontmatter · Hosts: Claude Code, plugins

Source: <https://code.claude.com/docs/en/skills#pre-approve-tools-for-a-skill>; <https://platform.claude.com/docs/en/manage-claude/plugins-api#reach>

- Rule: each `allowed-tools` entry is scoped to commands the skill's steps
  run.
- Why: `allowed-tools` pre-approves tools without a prompt, workspace trust
  does not gate it, it restricts nothing, and it raises a plugin version's
  reach to privileged.
- Pass when: every entry names a tool the body uses, and shell entries are
  command-scoped (`Bash(git status *)`). n/a when `allowed-tools` is absent.
- Fail when: an entry is unscoped (`Bash`, `Bash(*)`, `Write`, `Edit`) or
  grants a tool the body never uses.
- Fix: narrow each entry to the commands the steps run, and remove unused
  ones.

## Packaging (OS-18)

### OS-18 — Skill folder passes upload limits

Type: judgment · Level: should · Applies to: bundled files · Hosts: API, plugins

Source: <https://platform.claude.com/docs/en/build-with-claude/skills-guide#creating-a-skill>; <https://platform.claude.com/docs/en/manage-claude/plugins-api#upload-requirements>

- Rule: the skill folder can be uploaded where it is distributed: under 30 MB
  uncompressed for the Skills API; for the plugin store, no symbolic links,
  no nested `.zip`, file paths made only of letters, digits, spaces, and
  `_ . - / ( ) ,`, at most 12 levels deep and 472 characters long, and file
  or folder names of at most 255 characters.
- Why: the Skills API and the plugin store reject an upload that breaks these
  limits.
- Pass when: every check for a target host passes: total size of regular
  files under 30 MB; no symbolic link; no file ending `.zip`; every path
  character a letter, digit, or one of the listed characters; path depth,
  path length, and name length within the limits, counted from the skill
  folder. n/a when the target hosts include neither the API nor the plugin
  store. The checks are exact; only the host decision is judgment. The
  plugin store also limits the whole upload (200 MB, 5,000 files, no
  top-level `bin/`); one skill folder cannot show those, so they are not
  graded.
- Fail when: a check for a target host fails.
- Fix: move large data out or compress it, replace symlinks with real files,
  unpack nested archives, rename files with other characters, shorten or
  flatten long paths.

## Settled divergences

Where another official page and the article cannot both pass for the same
text, this catalogue follows the article: no OS rule encodes the other page's
position. An audit grades by the article rule and reports nothing about the
other page. The list below is a record for catalogue refreshes, not audit
output. A refresh that finds a new divergence settles it here and changes no
report; an OS rule that would contradict an article rule is narrowed or
retired. A stricter rule that the text can meet together with the article
rule (OS-01, OS-07, OS-08) is not a divergence and is reported on its own.

1. **Description voice.** The article requires third person (BP-15,
   <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions>).
   agentskills.io frames the description as an instruction ("Use this skill
   when ...")
   (<https://agentskills.io/skill-creation/optimizing-descriptions#writing-effective-descriptions>).
   A third-person capability clause followed by "Use when ..." meets both.
2. **Table-of-contents threshold.** The article asks for one in reference
   files over 100 lines (BP-22,
   <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#structure-longer-reference-files-with-table-of-contents>);
   skill-creator sets 300 lines
   (<https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md#progressive-disclosure>).
3. **Emphasis wording.** The article's iteration example accepts stronger
   wording such as "MUST filter"
   (<https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#develop-skills-iteratively-with-claude>);
   skill-creator treats all-caps ALWAYS or NEVER as a warning sign and asks
   for the reason instead
   (<https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md#how-to-think-about-improvements>).
4. **Package installs.** The article's good example is an unpinned
   install of the `pypdf` package
   (<https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-assuming-tools-are-installed>);
   the overview discourages global installs in Claude Code
   (<https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#runtime-environment-constraints>),
   and agentskills.io asks to pin one-off tool versions
   (<https://agentskills.io/skill-creation/using-scripts#one-off-commands>).
5. **`name` required.** The article requires `name` (BP-04,
   <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#yaml-frontmatter-requirements>);
   Claude Code makes every field optional and defaults `name` to the folder
   name (<https://code.claude.com/docs/en/skills#frontmatter-reference>).
   BP-04 stands.

## Retired rules

None. A rule dropped from this catalogue stays listed here with its ID, the
date it was retired, and the reason; its ID is never reused.
