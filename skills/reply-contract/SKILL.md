---
name: reply-contract
description: Ends every reply with a numbered "What I need from you" section and a fixed status line, and adds Evidence, How I check it and Decided without me after work. Use on every reply.
metadata:
  version: "2026.11.20.1"
  kind: rule
---

# Reply contract

## When work is done

After a task that changed files or ran commands, end the reply with these, in the chat:

- **Evidence**: the result itself. Visible work: a screenshot or the file through the host's file-sharing tool (rendered, if the tool can), one line on what each shows; with no such tool, the file path. Other work: the check you ran and its output. Not captured: say so and why.
- **How I check it**: the command to run, the file to open or the place to look, and what the user should see there.
- **Decided without me**: each decision or assumption you or a subagent made alone, with its basis. Only those that change the result or that the user could have decided differently.

## What you need from the user

- Ask only for what you cannot decide or do yourself, or what needs the user's approval.
- Whenever you need the user (any turn, Q&A included), put every ask in a numbered section near the end, headed "What I need from you" in the conversation's language. One concrete action per item: what to do, where (site, app, file or person), what to send back. E.g. "In the vendor dashboard → API Keys, create a key, put it in `.env` as `VENDOR_KEY`, reply 'done'", not "I need a key". Most blocking or quickest first; one line on what you'll do meanwhile.
- Number those items with keycap digits: 1️⃣, 2️⃣ … 9️⃣; multi-digit numbers digit by digit (1️⃣0️⃣, 1️⃣1️⃣). Each item is its own paragraph: put an empty line before every item. A single newline renders as a space in Markdown and merges the items into one paragraph.
- The very last line of every reply, after any other closing notes, is verbatim English:
  `⏸️ Nothing needed from you right now.` or `⏩ Needed from you: N ⤴️` (N = items in that section, in keycap digits like the items: 2️⃣, 1️⃣0️⃣).

## Order

Work report, then "What I need from you", then the last line.
