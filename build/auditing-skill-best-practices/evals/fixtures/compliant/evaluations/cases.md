# filling-pdf-forms scenarios

Models: Haiku, Sonnet, and Opus. Baseline: each query run once without the
skill on 2026-10-01; gaps noted per case. Runs use a fresh session with only
this skill loaded; each run logs the files it opened.

## Case 1: fill a W-9

- Query: "Fill w9.pdf with the values in w9.json"
- Files: w9.pdf, w9.json (real form from a user request)
- Baseline gap: filled an unknown field silently
- Expected: runs the check first; reports `unknown field 'tin'`; fills only after exit 0

## Case 2: checkbox values

- Query: "Tick the 'US person' box on w9.pdf"
- Files: w9.pdf
- Baseline gap: wrote `true` instead of `/Yes`
- Expected: reads references/field-types.md; writes `/Yes`

## Case 3: validate only

- Query: "Is my values.json valid for form.pdf?"
- Files: form.pdf, values.json
- Baseline gap: guessed field names
- Expected: runs the check and reports problems; writes no file

Haiku, Sonnet, Opus: all three cases passed on 2026-10-02.
