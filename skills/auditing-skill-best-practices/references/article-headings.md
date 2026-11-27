# Article headings

The drift baseline for refresh: the article's H2 to H4 headings in order, as
captured on the snapshot date in
[best-practices-rules.md](best-practices-rules.md#snapshot). Headings inside
the article's example code blocks are excluded. Anchor is the heading's HTML
`id` on the live page, as captured; it is not always the heading text's slug.
The Rules column lists every rule whose Section field cites the heading; a
dash means none does. The checklist rows (44 to 47) are the exception: they
map the checklist's items to the rules that cover them. Only refresh needs
this file. The table writes the apostrophe as `'`; the live page's `’` is
not drift.

| # | Level | Heading | Anchor | Rules |
| --- | --- | --- | --- | --- |
| 1 | H2 | Core principles | `core-principles` | — |
| 2 | H3 | Concise is key | `concise-is-key` | BP-01 |
| 3 | H3 | Set appropriate degrees of freedom | `set-appropriate-degrees-of-freedom` | BP-02 |
| 4 | H3 | Test with all models you plan to use | `test-with-all-models-you-plan-to-use` | BP-03, BP-56 |
| 5 | H2 | Skill structure | `skill-structure` | BP-04 to BP-11 |
| 6 | H3 | Naming conventions | `naming-conventions` | BP-05, BP-07, BP-12, BP-13, BP-14 |
| 7 | H3 | Writing effective descriptions | `writing-effective-descriptions` | BP-11, BP-15, BP-16 |
| 8 | H3 | Progressive disclosure patterns | `progressive-disclosure-patterns` | BP-17, BP-18 |
| 9 | H4 | Visual overview: From simple to complex | `visual-overview-from-simple-to-complex` | — |
| 10 | H4 | Pattern 1: High-level guide with references | `pattern-1-high-level-guide-with-references` | — |
| 11 | H4 | Pattern 2: Domain-specific organization | `pattern-2-domain-specific-organization` | BP-19 |
| 12 | H4 | Pattern 3: Conditional details | `pattern-3-conditional-details` | BP-20 |
| 13 | H3 | Avoid deeply nested references | `avoid-deeply-nested-references` | BP-21 |
| 14 | H3 | Structure longer reference files with a table of contents | `structure-longer-reference-files-with-table-of-contents` | BP-22 |
| 15 | H2 | Workflows and feedback loops | `workflows-and-feedback-loops` | — |
| 16 | H3 | Use workflows for complex tasks | `use-workflows-for-complex-tasks` | BP-23, BP-24 |
| 17 | H3 | Implement feedback loops | `implement-feedback-loops` | BP-25 |
| 18 | H2 | Content guidelines | `content-guidelines` | — |
| 19 | H3 | Avoid time-sensitive information | `avoid-time-sensitive-information` | BP-26 |
| 20 | H3 | Use consistent terminology | `use-consistent-terminology` | BP-27 |
| 21 | H2 | Common patterns | `common-patterns` | — |
| 22 | H3 | Template pattern | `template-pattern` | BP-28 |
| 23 | H3 | Examples pattern | `examples-pattern` | BP-29 |
| 24 | H3 | Conditional workflow pattern | `conditional-workflow-pattern` | BP-30, BP-31 |
| 25 | H2 | Evaluation and iteration | `evaluation-and-iteration` | — |
| 26 | H3 | Build evaluations first | `build-evaluations-first` | BP-32, BP-33, BP-34 |
| 27 | H3 | Develop Skills iteratively with Claude | `develop-skills-iteratively-with-claude` | BP-35, BP-36, BP-37 |
| 28 | H3 | Observe how Claude navigates Skills | `observe-how-claude-navigates-skills` | BP-38, BP-39 |
| 29 | H2 | Anti-patterns to avoid | `anti-patterns-to-avoid` | — |
| 30 | H3 | Avoid Windows-style paths | `avoid-windows-style-paths` | BP-40 |
| 31 | H3 | Avoid offering too many options | `avoid-offering-too-many-options` | BP-41 |
| 32 | H2 | Advanced: Skills with executable code | `advanced-skills-with-executable-code` | — |
| 33 | H3 | Solve, don't defer | `solve-dont-punt` | BP-42, BP-43 |
| 34 | H3 | Provide utility scripts | `provide-utility-scripts` | BP-44, BP-45, BP-46 |
| 35 | H3 | Use visual analysis | `use-visual-analysis` | BP-47 |
| 36 | H3 | Create verifiable intermediate outputs | `create-verifiable-intermediate-outputs` | BP-48, BP-49 |
| 37 | H3 | Package dependencies | `package-dependencies` | BP-50, BP-51 |
| 38 | H3 | Runtime environment | `runtime-environment` | BP-19, BP-40, BP-44, BP-45, BP-52, BP-53, BP-54 |
| 39 | H3 | MCP tool references | `mcp-tool-references` | BP-55 |
| 40 | H3 | Avoid assuming tools are installed | `avoid-assuming-tools-are-installed` | BP-50 |
| 41 | H2 | Technical notes | `technical-notes` | — |
| 42 | H3 | YAML frontmatter requirements | `yaml-frontmatter-requirements` | BP-04 to BP-10 |
| 43 | H3 | Token budgets | `token-budgets` | BP-17, BP-18 |
| 44 | H2 | Checklist for effective Skills | `checklist-for-effective-skills` | restates rules |
| 45 | H3 | Core quality | `core-quality` | BP-11, BP-16 to BP-21, BP-23, BP-26, BP-27, BP-29 |
| 46 | H3 | Code and scripts | `code-and-scripts` | BP-25, BP-40, BP-42, BP-43, BP-46, BP-48 to BP-51 |
| 47 | H3 | Testing | `testing` | BP-03, BP-33, BP-36, BP-37 |
| 48 | H2 | Next steps | `next-steps` | — |
