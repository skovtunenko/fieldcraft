# Catalogue refresh

Read this only when the user asks to refresh the catalogue, or to check it
against the live article. Refresh downloads every source document, compares
each with its stored hash, and reads only the documents that changed. It
reports drift and proposes catalogue edits; it edits no file in either skill.
Every reply, including a failure, is in the conversation language.

The best-practices article is the primary source. The other official pages
are secondary: they add hard requirements, and where one disagrees with the
article, the article wins (the OS catalogue's Settled divergences).

The [bundled-script execution boundary](../SKILL.md#bundled-script-execution-boundary)
and the interpreter fallback in SKILL.md's Rules apply to every command here.

## Contents

- [Steps](#steps)
- [Report template](#report-template)
- [Proposed edits](#proposed-edits)

## Steps

Copy this checklist into your task list and tick items off. It is your own
tracking; the final reply is the drift report alone. Steps 2 to 6 each run
only for a changed source, as step 1 decides.

```text
- [ ] 1. Sources fetched and hashes compared
- [ ] 2. Article: live headings listed
- [ ] 3. Article: headings and anchors compared
- [ ] 4. Article: rules compared
- [ ] 5. Skills page: OS-04 fields compared
- [ ] 6. Other changed pages: OS rules compared
- [ ] 7. Drift report assembled
- [ ] 8. Drift report checked
```

1. Fetch every source and compare it with [source-hashes.md](source-hashes.md):

   ```bash
   uv run --script <skill>/scripts/source_hashes.py "$TMPDIR/skill-sources"
   ```

   It creates the folder, saves each source under its File name, and prints
   JSON: `all_unchanged`, the file lists `changed`, `unreachable`,
   `unchanged`, and per source `status`, live `sha256`, and `error`. Status
   `fetched` marks a file saved for a later step and never compared; leave
   it out of every count. Exit 2 is a usage or table error, explained on
   stderr. Then:

   - `all_unchanged` is true? Nothing differs. Skip steps 2 to 6 and go to
     step 7 for the no-drift report.
   - A file is `unreachable`? Run the command once more. Still unreachable:
     download that URL into the same folder under the same File name with
     any tool that saves the raw bytes, then rerun the command with
     `--offline` added. A web fetch tool that summarises or reformats a page
     does not give raw bytes; do not use it here. A source that stays
     unreachable is reported as not checked, with its error, never as
     unchanged. When `best-practices.md` stays unreachable, report that and
     stop.
   - `best-practices.md` is `changed`? Do steps 2 to 4.
   - `claude-code-skills.md` is `changed`? Do steps 5 and 6 for it.
   - Any other file is `changed`? Do step 6 for it.
2. List the article's headings and their anchors:

   ```bash
   uv run --script <skill>/scripts/headings.py "$TMPDIR/skill-sources/best-practices.md"
   uv run --script <skill>/scripts/headings.py --ids "$TMPDIR/skill-sources/best-practices.html"
   ```

   The first prints `H<level> <heading>` per H2 to H4 heading outside code
   fences; the second, `H<level> <id>` per H2 to H4 element with a slug id,
   in page order. Exit 0 means success; exit 2 reports usage or
   unreadable-input details on stderr. If the helper stays unavailable, list
   the headings and ids by hand in the same format. When
   `best-practices.html` is unreachable, report the anchors as not checked,
   with the error, and continue.
3. Compare the headings with the table in
   [article-headings.md](article-headings.md). Classify each difference as
   **added**, **removed**, **renamed** (same position and substance, new
   wording), or **moved**. Then check anchors: every value in the table's
   Anchor column and every `#<anchor>` in the Source lines of
   [best-practices-rules.md](best-practices-rules.md) must appear in the live
   id list. Report each one that does not as **anchor changed**, with the
   live id of the same heading when there is one.
4. For every section, compare its recommendations, limits, and wording
   strength (must, should, consider) with the catalogue rules that cite that
   section. Classify each difference as a **new rule**, a **changed rule** (new
   limit, level, or scope), or a **dropped rule**. The skill keeps no copy
   of the earlier article, only its hash: an article that changed without
   touching a heading, anchor, or rule is reported as changed with no rule
   difference.
5. In `claude-code-skills.md`, list the Field column of the table under the
   "Frontmatter reference" heading. Each field missing from OS-04's Rule
   line, or listed there but gone from the table, makes OS-04 a **changed
   rule**. When the file is unreachable, report OS-04 as not checked, with
   the error.
6. For each other changed page, find the rules in
   [other-official-sources.md](other-official-sources.md) whose Source lines
   name it. For each such rule:

   - check that every cited `#<anchor>` still matches a heading of the page
     (list a Markdown page's headings with `headings.py`), and that a cited
     `#L<line>` still holds the check the rule describes;
   - compare the rule's Rule, Why, Pass when, and Fail when lines with what
     the page now states. A different limit, scope, or host behaviour makes
     it a **changed rule**; a requirement the page no longer states makes it
     a **dropped rule**.

   Propose a **new rule** only for a hard requirement that the page states
   and no rule covers; advice stays out, as the catalogue's Snapshot section
   defines. Where the changed page disagrees with the article, propose no
   rule against the article; add the case to Settled divergences instead. A
   page that changed without touching any cited rule is reported as changed
   with no rule difference.
7. Assemble the report in the user's conversation language, using the
   [Report template](#report-template) (headings and prose translated; rule
   IDs and heading quotes unchanged). When any source changed, print the
   table for the report's last section:

   ```bash
   uv run --script <skill>/scripts/source_hashes.py "$TMPDIR/skill-sources" --offline --print-table
   ```

8. Check the report: each count equals the rows of its table; every new ID is
   unused, including by retired rules, and above the highest ID of its
   catalogue; every changed rule keeps its ID; every proposal carries all the
   fields and updates listed below. Fix any mismatch and check again before
   sending.

## Report template

```markdown
# Snapshot drift: <snapshot date> vs live (<fetch date>)

Sources: <n> unchanged, <n> changed, <n> not checked
Headings: <n> added, <n> removed, <n> renamed, <n> moved, <n> anchors changed
Rules: <n> new, <n> changed, <n> dropped

## Source changes
| Source | Status | Rules that cite it |

## Heading changes
| Change | Snapshot heading | Live heading | Position |

## Rule changes
| Change | Rule | What changed | Proposed catalogue edit |

## Source hashes
<the printed table>
```

Position is the heading's row number in the live order. `<snapshot date>` is the Snapshot date line of
[best-practices-rules.md](best-practices-rules.md#snapshot); `<fetch date>`
is today's date.

When nothing differs, keep the title and the three count lines with zeros,
replace the sections with one line, "No drift since <snapshot date>"
(translated), and propose nothing. When a source was not checked, list it
under Source changes with its error even if nothing else differs.

## Proposed edits

Proposed edits follow the catalogue's own conventions:

- A new rule takes the next unused ID, with type, level, applies-to, Section
  or Hosts, Source (the live anchor of each cited section), pass condition,
  fail condition, and fix. Make it mechanical only when a script can decide
  it without false positives; otherwise judgment.
- A changed rule keeps its ID; show the old and new text of the changed line.
- A dropped rule moves to **Retired rules** with the date and reason; its ID
  is never reused.
- Every report with a changed source, even one with no heading or rule
  difference, also proposes an update of each place that holds a snapshot
  value:
  - the table in `source-hashes.md`, replaced by the printed table, and the
    snapshot date of both catalogues, set to the fetch date;
  - the changed catalogue's Snapshot section: rule count, type and level
    counts, and the mechanical-rule list;
  - the catalogue's contents list and section headings, which carry ID ranges;
  - the heading table, its Anchor column, and its rule column in
    `article-headings.md`;
  - every Source line that holds a changed anchor;
  - the rule set in `scripts/check_mechanical.py`, for any new or retired
    mechanical rule, and its `EVALUATION_RULES` list, for any new or retired
    rule that applies to evaluation material;
  - for a changed OS-04, its Rule line in `other-official-sources.md` and
    `KNOWN_KEYS` in `scripts/check_mechanical.py`, with the same fields.

  `SKILL.md` and its report template hold no rule count, ID range, or date;
  they read these from the catalogue at run time. A proposal keeps it that
  way. Script locations above name follow-up maintenance work only; derive
  the proposals from the catalogues and the fetched documents.
