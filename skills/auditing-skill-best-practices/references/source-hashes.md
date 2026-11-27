# Source hashes

The stored fingerprint of every document the two catalogues were distilled
from, as fetched on the catalogues' snapshot date. Refresh compares the live
documents with these hashes first and reads only the documents that changed.
`scripts/source_hashes.py` reads this table; keep its columns. Only refresh
needs this file.

The article is the primary source: the first two rows feed the article
catalogue. Every other row feeds the other official sources catalogue.

Mode `bytes` hashes the file as served. Mode `text` hashes an HTML page's
visible article text and element ids, because its markup differs between
fetches. Mode `none` is fetched for a later step and never compared.

| File | URL | Mode | sha256 |
| --- | --- | --- | --- |
| `best-practices.md` | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md> | bytes | cb3f49125d6716342b369145655ec8a129a2baeaff3dd56b3087758f9674bd54 |
| `best-practices.html` | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> | none | — |
| `claude-code-skills.md` | <https://code.claude.com/docs/en/skills.md> | bytes | 50c0f7621b93db9b7d7d4db4bb079341354915aa5f33533950d3dbad8b124ff9 |
| `overview.md` | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview.md> | bytes | 2828b43872578b136b274f63e45ab58d3b8f2926abf553a47b9ae6cf714ad2c1 |
| `enterprise.md` | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise.md> | bytes | f5bc4c3e5113169ef5e1b2aad69040d77ea3c2d2a6df16b79f46de7907a8876d |
| `skills-guide.md` | <https://platform.claude.com/docs/en/build-with-claude/skills-guide.md> | bytes | a81a42e063e6b7c57c9b15d687d666be81b6c950425bcef7ce990cfa07c6f42d |
| `plugins-api.md` | <https://platform.claude.com/docs/en/manage-claude/plugins-api.md> | bytes | 5a49823d4cf35aa284028150714a0ba06db4222f91262cd35b050e3a3ef209fc |
| `using-skills-in-claude.html` | <https://support.claude.com/en/articles/12512180-using-skills-in-claude> | text | 6340a5f99c34b3ef10087b58c4f68bd31df09136e7c733a96f0ca4eb634955ec |
| `quick_validate.py` | <https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/scripts/quick_validate.py> | bytes | 67cf5703402013936c8fb75ad6a1afecd8841d45cc5e606b634eb05825fde365 |
| `skill-creator.md` | <https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md> | bytes | dcd4803e61e913e6fc27294184cd3a71f09f5e924ff20c8a9a20173e7b3c2bcf |
| `specification.md` | <https://agentskills.io/specification.md> | bytes | bf4137a702014f82a022de532e597c5f92ea86fb53fe29ea27bee3bbc1d19738 |
| `using-scripts.md` | <https://agentskills.io/skill-creation/using-scripts.md> | bytes | c8a0792d224d8bdc98741cf741c2cd9e0cd36457cb3930df791f18e81fca31d0 |
| `optimizing-descriptions.md` | <https://agentskills.io/skill-creation/optimizing-descriptions.md> | bytes | 7cc54fbb6abbcf08c33e7b320fd01a1fb9696426270da3b588a398d243bfd837 |
