# Follow-ups after an audit

Read this for two cases only: the user pastes an export from a review page,
or an audit is requested for a target already audited in this conversation.

## Applying an export

An export is the plain-text instruction a review page produces: accepted and
edited fixes, rejections, and reviewer questions. Pasting it, or the results
of applying it, is not an audit request.

- An application request? Apply only the accepted changes and answer the
  questions. Then summarize the applied, skipped, and conflicting fixes and
  any new target path, offer to rerun the audit on request, and stop to wait
  for the user's reply.
- Results only? Acknowledge them, offer a re-audit, and stop.
- A questions-only export changes no files: answer its questions only.
- An older export that ends with an automatic re-audit step is handled the
  same way; that embedded step is not a separate user request.
- Do not claim the fixes passed an audit. Keep earlier reports, pages, and
  findings files as historical snapshots after the edits.

## Same-conversation re-audit

Use when the complete prior verdicts and evidence remain in conversation, the
saved findings JSON is available, and target, catalogue revision, and host
scope still permit reuse. It runs only on an explicit audit request. After
the fresh mechanical checker in Audit step 1, run:

```bash
uv run --script <skill>/scripts/stale_scope.py <target> "<previous findings.json>"
```

The two arguments are the target directory and prior full findings JSON. Git
must be available. The command prints one compact JSON card: `changed`, `added`,
`deleted`, `renamed` (`from`/`to`), `cited` (paths named by changed lines), `rules`
(IDs whose free-text evidence cites those paths), and `read` (existing target
paths to open). It compares the audited working-tree snapshot saved by the
renderer with current Git inventory, including uncommitted and untracked files.
Exit 0 returns a scope or `{"fallback":"full","reason":"..."}`; exit 2
returns a compact usage card.

- Use `read` paths as explicit file arguments for target reading and content
  searches; read those text files in full, note binary metadata as a full
  audit does, and account for `deleted` and `renamed`. Use the card with
  prior verdicts already in conversation; the previous findings JSON stays
  on disk.
- Reconsider the card's rule IDs and every judgment the printed paths can
  affect, including prior pass, fail, n/a, and cross-file relationships. A rule
  whose evidence names no file stays off the card and is reconsidered only
  when these paths affect it. Reuse other valid verdicts as prior evidence;
  the rule text from the earlier audit stays valid while the catalogue
  revision is unchanged.
- Update affected locations, quotes, and fixes, then continue with Audit
  steps 4 and 5: one new findings JSON holding every judgment verdict,
  reused or new, with counts, evidence, fixes, and reviewer rejection
  reasons in the rendered report.

**Fallback.** Run the full audit of Audit step 2 when the prior audit,
evidence, or baseline is missing, Git cannot bound changes, or target
identity, catalogue revision, host scope, or unbounded dependencies prevent
reliable reuse.
