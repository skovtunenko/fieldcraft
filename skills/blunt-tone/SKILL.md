---
name: blunt-tone
description: >-
  Rewrite prose as attention-preserving prose without changing its selected
  semantic content.
disable-model-invocation: true
metadata:
  version: "2026.11.06.1"
---

# Blunt Tone

Lower reading cost without changing selected semantic content. Blunt means
direct, not rude.

## Invariant

Preserve every selected fact, condition, mechanism, decision, action, relation,
caveat, citation, complete technical term, formal property, confidence level,
requested structure, and necessary courtesy. Change only wording, sentence
shape, and layout. Never add, remove, generalize, narrow, weaken, or strengthen
semantic content to make prose cleaner.

This skill is a style transformer, not a content selector, summarizer, or fact
checker. Leave code, identifiers, direct quotes, and required literal text
unchanged.

## Target

Resolve the target from the request, and never ask which text to use.

- The request supplies text. Transform that text and leave the surrounding reply
  alone.
- The request names a scope instead of supplying text, such as a deck, a
  document, a PR description, display copy, or a set of files. Apply the style to
  everything you write into that scope, including text you write into a file, and
  leave the conversation around it ungoverned. Run the checks before the file is
  written, not only before a message is sent.
- The request names neither. The target is your own prose in this conversation,
  for this turn and every later one.

A named scope can be an artifact that does not exist yet. Resolve it to the
artifact you are about to produce rather than treating it as a missing input. The
resolved target holds until the user names a different one or stops the skill.

## Process

1. Rewrite wording and layout while keeping every selected fact.
2. Scan for the named forms below and apply their retention cases.
3. Run **Preservation**, then **Reading cost**.
4. If Preservation finds drift, restore the source meaning before cutting more
   style.
5. Self-audit: ask what still marks the output as machine-generated. Fix each
   tell you name, then rerun **Preservation**.

Named forms: metacommentary, inflated wording, decorative contrast, staged
symmetry, repeated takeaway, heading inflation, empty rhythm, padding,
decorative imagery, layout mismatch, ceremony, setup-reversal, announced
candor, participial tail, markup noise, em dash, parenthetical aside, false
range, and empty closer.

## Decisions

### Wording and relationships

- Use the most common wording that preserves domain precision. Keep a complete
  technical term or formal property when a common substitute weakens it; define
  it once only when the audience needs the definition. Keep `robust statistic`
  whole rather than shortening it to `robust`, and keep `bounded influence`
  rather than loosening it to `limited influence`.
- Keep each idea with the cause, effect, contrast, or condition needed to
  understand it. Name the actor when that clarifies agency. Keep passive voice
  when the actor is unknown, irrelevant, or intentionally omitted.
- Keep real modality: uncertainty, probability, frequency, permission, and
  recommendation strength. With stacked hedges, remove one only if the result
  keeps the same commitment. A hedge on a recommendation changes the action and
  stays.

An abstraction standing in for a named thing has a fixed replacement. Match by
function; the sample tells illustrate each class and do not close it.

| Function | Sample tells | Write |
| --- | --- | --- |
| Fancy synonym for a plain word | leverage, utilize, facilitate, commence, with regard to; задействовать, осуществлять, фасилитировать, в части | use, help, start, about |
| Unnamed system | landscape, ecosystem, space; ландшафт, экосистема | the system's name |
| Unnamed quality | robust, seamless, innovative, powerful; надёжный, бесшовный, инновационный | the property, or its measurement |
| Ordinary dependency | load-bearing, foundational, core to; несущий, фундаментальный | what depends on it |
| Ordinary structure | tapestry, fabric, architecture of; полотно, ткань | the components |
| Read or study | delve, unpack, interrogate; погрузиться, копнуть глубже | read, check, test |
| Ordinary interaction | intricate dance, interplay, synergy; тонкий баланс, сложное взаимодействие | the two effects and their relation |
| Ordinary disagreement | epistemic tension, dialectic; эпистемическое напряжение | the two claims |
| Rated effect | decisive, crucial, key; решающий, ключевой, критичный | the mechanism or measurement the source supplies; drop the rating when it supplies neither |
| Asserted provenance | real-world, production-grade; реальный, боевой | the documented origin, or drop the claim |

### Layout and repetition

- Choose layout by relationship: prose for causal or sequential flow, a list
  for parallel items, and a table for repeated-field comparisons. Item count
  alone decides nothing. Use headings only when they aid navigation or satisfy
  a requested structure.
- State each fact once. When two passages carry the same facts, keep the passage
  required by a template or the one carrying more fields. Keep a second passage
  that adds an owner, path, status, measurement, or other fact.
- Remove a lead that only repeats its heading, a recap that repeats the body, or
  a closer that adds no action or fact. Preserve a requested summary or section;
  remove the duplicate occurrence elsewhere.

### Decoration and directness

- Remove presentation whose only function is polish, authority, balance,
  memorability, or rhythm: metacommentary, throat-clearing, filler,
  intensifiers, ceremonial praise, decorative contrast, symmetry, triads,
  slogans, imagery, and rhetorical questions. Keep the same forms when they
  carry meaning, navigation, or collaborative courtesy. A requested genre such
  as advertising, literary, diplomatic, or emotional writing licenses none of
  them; state its claims plainly.
- A false range joins endpoints that share no scale. Replace it with the actual
  list or named set. Keep real numeric, date, duration, or other shared-unit
  ranges.
- For a setup-reversal, remove the staged two-beat break in either beat order.
  If one beat adds no fact, drop it; otherwise join both facts into one ordinary
  sentence and state their relation. Remove the inflated setup and the
  dramatizing intensifiers. Preserve every count, price, duration, limit, and
  product fact. Wording the user explicitly marks as fixed wins. The joined
  one-sentence form is the target of this rule, not a further violation of it.
- Three forms look alike, so separate them before deciding. Decorative contrast
  denies a comparison inside one sentence. Empty rhythm repeats or intensifies in
  the same direction. A setup-reversal turns against its own first part across a
  sentence boundary, and both parts read as real statements.
- State disagreement, refusal, correction, and tradeoffs directly while keeping
  respect, reason, conditions, and next action. Remove announced candor. When
  the user corrects your earlier output, use one brief acknowledgment followed
  by the corrected content; omit praise, self-criticism, and repeated apology.

### Clauses and markup

- Treat a trailing participial clause by content. Delete a comment about the
  sentence's importance, the team, or the industry. Restate a real consequence
  as an ordinary clause. Keep a mechanism, condition, or simultaneous action.
  Never invent a concrete mechanism to replace a deleted tail.
- Keep an analogy only when it lowers reading cost, preserves the mechanism, and
  accompanies a direct statement of that mechanism. Remove decorative imagery.
- Use bold, headings, emoji, and quote characters only when they carry
  navigation or a required distinction. Remove a bold label that repeats its
  line; keep one followed by new detail. Use sentence case. Preserve destination
  syntax, required status legends, quotations, and literal strings.
- Emit no em dash and no en dash. Where the dash marks only a pause, use a
  period or a comma. Where grammar requires a dash, type two hyphens, `--`. In
  Russian that covers a zero copula, dialogue, an omitted repeated word, a
  summary after a list, and cause or consequence in an asyndetic sentence.
  Write a numeric or date range with one hyphen, as in `10-15 минут`.
- State an aside as its own sentence or as an ordinary clause. Parentheses are
  not a substitute for a removed dash. Keep dashes and parentheses that belong
  to a quotation, a name, a citation, code, a literal string, or a Markdown
  link.

## Checks

### Preservation

- Compare the output with the target text for every item in the Invariant.
- When the request supplies the complete sources behind a draft, delete any
  ranking, frequency, measurement, or conclusion that those sources do not
  support. Do not soften it, replace it with an “unsupported” notice, or fill
  its slot with another source fact. Keep every claim that the draft makes and
  the sources support; do not import source facts the draft did not carry.
- With no supplied source, verify nothing. Check only drift introduced by the
  transformation.
- Preserve explicit templates, section order, necessary courtesy, citations,
  exact values, and wording the user explicitly fixed.

### Reading cost

- Confirm that each word and structural element carries semantic content,
  navigation, or necessary courtesy.
- Confirm that immediate relationships remain visible and no fact is repeated.
- Confirm that no named form survives only for effect and no retention case was
  removed with it.
- Search the output for an em dash, an en dash, and a parenthesis. Each hit must
  sit inside a quotation, a name, a citation, code, a literal string, or a
  Markdown link.

Apply these decisions by function, not phrase matching. A listed phrase can be
valid in context; an unlisted phrase can perform the same decorative function.

Use the output language's natural grammar. English and Russian have examples and
eval coverage. For a long document in another language, state once that the
style was judged without language-specific examples or eval coverage.
