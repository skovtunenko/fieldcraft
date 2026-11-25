---
name: reply-contract
description: Ends every reply with a numbered "What I need from you" section and a fixed status line, and adds Evidence, How I check it and Decided without me after work. Use on every reply.
metadata:
  version: "2026.11.25.1"
  kind: rule
---

# Reply contract

## When work is done

After a task that changed files or ran commands, end the reply with these, in the chat:

- **Evidence**: the result itself. Visible work: a screenshot or the file through the host's file-sharing tool (rendered, if the tool can), one line on what each shows; with no such tool, the file path. Other work: the check you ran and its output. Not captured: say so and why.
- **How I check it**: the command to run, the file to open or the place to look, and what the user should see there.
- **Decided without me**: each decision or assumption you or a subagent made alone, with its basis. Only those that change the result or that the user could have decided differently.

Without such work, leave these three out and do not mention them.

## What you need from the user

- Ask only for what you cannot decide or do yourself, or what needs the user's approval. Before you ask, check what you can check (files, installed tools, config); where a sensible default exists, use it and say so instead of asking.
- Whenever you need the user (any turn, Q&A included), put every ask in one numbered section near the end. Its heading is "What I need from you" translated into the conversation's language (Russian: «Что мне нужно от вас»); only the last line stays in English. With no asks, write no section. One concrete action per item: what to do, where (site, app, file or person), what to send back. E.g. "In the vendor dashboard → API Keys, create a key, put it in `.env` as `VENDOR_KEY`, reply 'done'", not "I need a key". Most blocking or quickest first. After the last item, one line on what you do meanwhile; if nothing happens until the user answers, say that.
- Number those items with keycap digits: 1️⃣, 2️⃣ … 9️⃣; multi-digit numbers digit by digit (1️⃣0️⃣, 1️⃣1️⃣). Each item is its own paragraph: put an empty line before every item. A single newline renders as a space in Markdown and merges the items into one paragraph.
- The very last line of every reply, after any other closing notes, is verbatim English:
  `⏸️ Nothing needed from you right now.` or `⏩ Needed from you: N ⤴️` (N = items in that section, in keycap digits like the items: 2️⃣, 1️⃣0️⃣). The line always ends with `⤴️`, e.g. `⏩ Needed from you: 2️⃣ ⤴️`.

## Order

Work report, then "What I need from you", then the last line.
