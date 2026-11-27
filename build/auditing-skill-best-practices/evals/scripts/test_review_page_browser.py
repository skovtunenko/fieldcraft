#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Browser test of the review page: edit -> accept -> reload -> export.

Usage: uv run --script evals/scripts/test_review_page_browser.py

Renders evals/fixtures/review/findings-violating.json plus a second BP-55
failure and an OS-15 failure at SKILL.md:15 sharing BP-15's edit, opens it in headless Chrome (CDP over --remote-debugging-pipe,
standard library only) with a fresh profile, and asserts: both BP-55 titles
name their location; accept on BP-07 and edit on BP-15 (new After, a comment)
show in the live instruction, and Resolves names OS-15's location; a reject with a comment shows as a reason not to
apply, a reject without one goes in with no reason given; marks, edit, comment, and instruction survive a
reload; a folded card, Collapse all, Expand all, and a sidebar unfold survive a reload, and Reset review unfolds; the sidebar nests a
shared edit's findings under its owner, and the owner's toggle hides them across a reload;
a failure with reviewer_reason starts rejected with that reason, Accept and Edit off, and
exports as rejected; the export stops without another audit; a hand-edited instruction survives a reload and Rebuild restores the
built one; no console error or exception. Chrome comes from CHROME_BIN, else
the macOS default install, else google-chrome / chromium on PATH. Exit 1 when
a check failed, 2 when no browser could run (never a silent pass).
Chrome must create a socket for its profile, so an agent runs this test outside
its command sandbox.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "skills").is_dir())
SKILL = next(ROOT.glob("skills/**/auditing-skill-best-practices/SKILL.md")).parent
SCRIPT = SKILL / "scripts" / "render_review_page.py"
SAMPLE = Path(__file__).resolve().parents[1] / "fixtures" / "review" / "findings-violating.json"
MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
NEW_AFTER = "Fills PDF forms from a JSON mapping. Use when a PDF form must be filled."
HAND = "Hand-written instruction.\n"
REASON = "Constants here are self-explanatory."
NESTED = "Filing to the tracker is the documented purpose."
QUESTION = "Why does this date line matter?"

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def chrome_bin() -> str | None:
    for candidate in (os.environ.get("CHROME_BIN"), MAC_CHROME if Path(MAC_CHROME).exists() else None,
                      shutil.which("google-chrome"), shutil.which("chromium")):
        if candidate:
            return candidate
    return None


class Browser:
    """One headless Chrome, one page session, CDP messages NUL-delimited on fds 3 (in) and 4 (out)."""

    def __init__(self, binary: str, profile: Path) -> None:
        to_chrome_r, self.to_chrome = os.pipe()
        self.from_chrome, from_chrome_w = os.pipe()

        def fds() -> None:  # Chrome reads commands on fd 3 and writes replies on fd 4
            high = os.dup(to_chrome_r), os.dup(from_chrome_w)  # a pipe may already sit on 3 or 4; dup2 onto itself keeps close-on-exec
            os.dup2(high[0], 3)
            os.dup2(high[1], 4)

        self.proc = subprocess.Popen(
            [binary, "--headless=new", "--remote-debugging-pipe", f"--user-data-dir={profile}", "--no-first-run",
             "--no-default-browser-check", "--disable-extensions", "--disable-gpu", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=fds, close_fds=False)  # close_fds would shut fds 3 and 4 after preexec_fn
        os.close(to_chrome_r)
        os.close(from_chrome_w)
        self.reader = os.fdopen(self.from_chrome, "rb")
        self.next_id = 0
        self.events: list[dict] = []
        self.session: str | None = None

    def send(self, method: str, params: dict | None = None, session: bool = True) -> dict:
        self.next_id += 1
        message = {"id": self.next_id, "method": method, "params": params or {}}
        if session and self.session:
            message["sessionId"] = self.session
        os.write(self.to_chrome, json.dumps(message).encode() + b"\0")
        buffer = b""
        while True:
            chunk = self.reader.read1(65536)
            if not chunk:
                raise RuntimeError(f"Chrome closed the pipe during {method}")
            buffer += chunk
            while b"\0" in buffer:
                raw, buffer = buffer.split(b"\0", 1)
                reply = json.loads(raw)
                if reply.get("id") == self.next_id:
                    if "error" in reply:
                        raise RuntimeError(f"{method}: {reply['error']}")
                    return reply.get("result", {})
                self.events.append(reply)

    def js(self, expression: str) -> object:
        result = self.send("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
        if "exceptionDetails" in result:
            raise RuntimeError(f"page script failed: {result['exceptionDetails'].get('exception', {}).get('description')}: {expression[:80]}")
        return result["result"].get("value")

    def wait_loaded(self) -> None:
        for _ in range(100):  # 10 s
            if self.js("document.readyState === 'complete' && !!document.querySelector('.question')"):
                return
            time.sleep(0.1)
        raise RuntimeError("the page did not finish loading in 10 s")

    def close(self) -> None:
        self.proc.kill()
        self.proc.wait()


CARD = "Array.from(document.querySelectorAll('article.question')).find(c => c.querySelector('.qid').textContent === {rid!r})"


def click(browser: Browser, rid: str, action: str) -> None:
    browser.js(f"({CARD.format(rid=rid)}).querySelector('button.act-{action}').click()")


def type_into(browser: Browser, element: str, value: str) -> None:
    """Set a textarea, given as a JS expression, and fire input as typing would."""
    browser.js(f"(() => {{ const box = {element}; box.value = {json.dumps(value)};"
               " box.dispatchEvent(new Event('input', {bubbles: true})); })()")


def snapshot(browser: Browser) -> dict:
    return browser.js(f"""(() => {{
      const find = rid => Array.from(document.querySelectorAll('article.question')).find(c => c.querySelector('.qid').textContent === rid);
      const pressed = rid => Array.from(find(rid).querySelectorAll('.q-actions button[aria-pressed="true"]')).map(b => b.dataset.value);
      const bp15 = find('BP-15');
      return {{bp07: pressed('BP-07'), bp15: pressed('BP-15'), bp26: pressed('BP-26'),
              edit: bp15.querySelector('.inline-edit-text')?.value ?? bp15.querySelector('.q-source p.step')?.textContent ?? '', editHidden: !bp15.querySelector('.inline-editor'),
              comment: bp15.querySelector('textarea[id^="comment-"]').value,
              instruction: document.getElementById('exportText').value,
              notice: !document.getElementById('exportEdited').hidden,
              count: document.getElementById('exportCount').textContent}};
    }})()""")


def main() -> int:
    binary = chrome_bin()
    if not binary:
        print("no browser: set CHROME_BIN; the browser test cannot run", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw).resolve()
        page = tmp / "review.html"
        findings = json.loads(SAMPLE.read_text(encoding="utf-8"))
        second = next(f for f in findings["failures"] if f["rule"] == "BP-55")
        findings["failures"].append({**second, "location": "references/api.md:40"})  # a rule failing in two places
        next(r for r in findings["rules"] if r["id"] == "OS-15")["status"] = "fail"
        findings["failures"].append({"rule": "OS-15", "location": "SKILL.md:15", "why": "Undisclosed actions surprise the user.",
                                     "evidence": "SKILL.md:15 files to a tracker the description never names.", "fix_ref": "BP-15"})
        sample = tmp / "findings.json"
        sample.write_text(json.dumps(findings), encoding="utf-8")
        result = subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPT), str(sample), str(page)],
                                capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"render failed: {result.stderr}", file=sys.stderr)
            return 1
        browser = Browser(binary, tmp / "profile")
        try:
            try:
                targets = browser.send("Target.getTargets", session=False)["targetInfos"]
                target = next(t["targetId"] for t in targets if t["type"] == "page")
                browser.session = browser.send("Target.attachToTarget", {"targetId": target, "flatten": True}, session=False)["sessionId"]
                browser.send("Runtime.enable")
                browser.send("Page.enable")
                browser.send("Page.navigate", {"url": page.as_uri()})
                browser.wait_loaded()
            except (RuntimeError, OSError, StopIteration) as error:
                print(f"browser did not start: {error}; the browser test cannot run", file=sys.stderr)
                return 2

            titles = browser.js("""(() => ({
              cards: Array.from(document.querySelectorAll('article.question')).map(c => c.querySelector('.qid').textContent + ' ' + c.querySelector('.q-title').textContent),
              nav: Array.from(document.querySelectorAll('.nav-text')).map(n => n.textContent)}))()""")
            check("BP-55 Fully qualified MCP tool names · SKILL.md:15" in titles["cards"]
                  and "BP-55 Fully qualified MCP tool names · references/api.md:40" in titles["cards"]
                  and any(t.endswith("BP-55 Fully qualified MCP tool names · api.md:40") for t in titles["nav"])
                  and "BP-07 `name` avoids reserved words" in titles["cards"],
                  f"a rule failing twice shows each location in its card and sidebar titles, a single failure shows none (got {titles})")

            click(browser, "BP-07", "accept")
            click(browser, "BP-15", "edit")
            type_into(browser, f"({CARD.format(rid='BP-15')}).querySelector('.inline-edit-text')", NEW_AFTER)
            browser.js(f"({CARD.format(rid='BP-15')}).querySelector('.save-edit').click()")
            type_into(browser, f"({CARD.format(rid='BP-15')}).querySelector('textarea[id^=\"comment-\"]')", "Keep it short.")
            click(browser, "BP-43", "reject")
            type_into(browser, f"({CARD.format(rid='BP-43')}).querySelector('textarea[id^=\"comment-\"]')", REASON)
            click(browser, "BP-21", "accept")
            check(browser.js(f"({CARD.format(rid='BP-21')}).dataset.mark") == "accept", "a decision switches straight to another one, here Accept")
            click(browser, "BP-21", "reject")
            before = snapshot(browser)
            text = before["instruction"]
            check(before["bp07"] == ["accept"] and before["bp15"] == ["edit"] and before["count"] == "4",
                  f"BP-07 accepted, BP-15 edited, BP-43 rejected with a reason, BP-21 without: export count 4 (got {before['bp07']}, {before['bp15']}, {before['count']})")
            check("BP-07" in text and "BP-15" in text and "[edited by the reviewer]" in text and NEW_AFTER in text
                  and "Keep it short." in text and "BP-26" not in text,
                  "live instruction lists the accepted and edited fixes, with the new After and the comment, and not the unreviewed BP-26")
            check("Resolves: BP-15, OS-03, OS-15 (SKILL.md:15)" in text,
                  "Resolves names the location of a resolved failure found elsewhere, not of one at the same place")
            rejected = text.split("Do not apply them.")[-1]
            check("BP-43" in rejected and "[rejected by the reviewer]" in rejected and REASON in rejected
                  and "BP-21" in rejected and "   Reviewer reason: none given" in rejected,
                  "a rejected fix goes in as one not to apply, with its comment as the reason or with none given")
            check("Stop after this summary and offer," in text.rstrip().splitlines()[-1]
                  and "Offer to rerun the audit on request." in text and "Do not run an audit, mechanical checker" in text,
                  "instruction ends with application summary, optional re-audit offer, and stop")

            browser.send("Page.reload")
            browser.wait_loaded()
            after = snapshot(browser)
            check(after == before, f"marks, edit, comment, and instruction survive a reload (diff: "
                  f"{ {k: after[k] for k in after if after[k] != before[k]} })")

            browser.js("document.querySelector('[data-syntax-mode=\"edit\"]').click()")
            type_into(browser, "document.getElementById('exportText')", HAND)
            click(browser, "BP-26", "accept")
            edited = snapshot(browser)
            check(edited["instruction"] == HAND and edited["notice"] and edited["count"] == "5",
                  "a hand-edited instruction is kept when another fix is accepted, with the edited notice")
            browser.send("Page.reload")
            browser.wait_loaded()
            reloaded = snapshot(browser)
            check(reloaded["instruction"] == HAND and reloaded["notice"] and reloaded["bp26"] == ["accept"],
                  "the hand-edited instruction and the new mark survive a reload")
            browser.js("document.getElementById('exportRebuild').click()")
            rebuilt = snapshot(browser)
            check(rebuilt["instruction"] != HAND and "BP-26" in rebuilt["instruction"] and not rebuilt["notice"],
                  "Rebuild restores the built instruction, now with BP-26")
            browser.send("Page.reload")
            browser.wait_loaded()
            check(snapshot(browser)["instruction"] == rebuilt["instruction"], "after Rebuild a reload shows the built instruction")

            browser.js(f"({CARD.format(rid='BP-07')}).querySelector('button.fold-card').click()")
            check(browser.js(f"({CARD.format(rid='BP-07')}).classList.contains('folded')"), "the footer Fold button folds a handled card")
            colours = browser.js(f"[getComputedStyle({CARD.format(rid='BP-07')}).backgroundColor,"
                                 f" getComputedStyle({CARD.format(rid='BP-43')}).backgroundColor,"
                                 f" getComputedStyle({CARD.format(rid='BP-52')}).backgroundColor]")
            check(len(set(colours)) == 3, f"accepted, rejected, and open cards each have their own background (got {colours})")

            def reload() -> None:
                browser.send("Page.reload")
                browser.wait_loaded()

            bp07_folded = f"({CARD.format(rid='BP-07')}).classList.contains('folded')"
            folds = "Array.from(document.querySelectorAll('article.question')).map(c => c.classList.contains('folded'))"
            reload()
            check(browser.js(bp07_folded), "a folded card stays folded after a reload")
            browser.js("document.getElementById('collapseAll').click()")
            reload()
            check(all(browser.js(folds)), "Collapse all survives a reload")
            browser.js("document.getElementById('expandAll').click()")
            reload()
            check(not any(browser.js(folds)), "Expand all survives a reload")
            browser.js(f"({CARD.format(rid='BP-07')}).querySelector('button.fold-card').click()")
            browser.js("Array.from(document.querySelectorAll('.nav-item')).find(b => b.querySelector('.nav-text').textContent.includes('BP-07 ')).click()")
            reload()
            check(not browser.js(bp07_folded), "a sidebar click unfolds a folded card, and that survives a reload")
            groups = """Object.fromEntries(Array.from(document.querySelectorAll('.nav-group')).map(g =>
              [g.querySelector('.nav-row .nav-text').textContent.split(' ')[1],
               Array.from(g.querySelectorAll('.nav-refs .nav-text')).map(t => t.textContent.split(' ')[0])]))"""
            toggle = "Array.from(document.querySelectorAll('.nav-group')).find(g => g.querySelector('.nav-row .nav-text').textContent.includes('BP-07 ')).querySelector('.nav-toggle')"
            nested = browser.js(groups)
            check(nested.get("BP-07") == ["BP-05"] and nested.get("BP-15") == ["OS-03", "OS-15"]
                  and not browser.js("Array.from(document.querySelectorAll('#nav > .nav-item.is-ref')).length"),
                  f"the sidebar lists each finding a shared edit fixes indented under its owner (got {nested})")
            browser.js(f"{toggle}.click()")
            reload()
            check(browser.js(groups).get("BP-07") == [] and browser.js(f"{toggle}.getAttribute('aria-expanded')") == "false",
                  "the owner's toggle hides its nested findings, and that survives a reload")
            browser.js(f"{toggle}.click()")
            check(browser.js(groups).get("BP-07") == ["BP-05"], "the toggle shows them again")
            browser.js(f"{toggle}.click()")
            browser.js(f"({CARD.format(rid='BP-07')}).querySelector('button.fold-card').click()")

            ref = "Array.from(document.querySelectorAll('.also-item')).find(d => d.querySelector('.qid').textContent === 'OS-15')"
            browser.js(f"{ref}.querySelector('button.act-reject').click()")
            type_into(browser, f"{ref}.querySelector('textarea')", NESTED)
            text = snapshot(browser)["instruction"]
            check("Resolves: BP-15, OS-03\n" in text and "OS-15 No hidden" in text.split("Do not apply them.")[-1] and NESTED in text,
                  "a nested finding rejected with a reason leaves Resolves and joins the rejected list with its reason")
            browser.send("Page.reload")
            browser.wait_loaded()
            check(browser.js(f"{ref}.dataset.mark") == "reject" and NESTED in snapshot(browser)["instruction"],
                  "the nested rejection and its reason survive a reload")

            first = browser.js("(() => { let t = ''; window.confirm = m => { t = m; return false; }; document.getElementById('resetReview').click(); return t; })()")
            check("earlier round" not in first, f"a first-round page's Reset says nothing about earlier rejections (got {first!r})")
            check(snapshot(browser)["bp07"] == ["accept"], "Reset review asks first; cancelling keeps every decision")
            browser.js("window.confirm = () => true; document.getElementById('resetReview').click()")
            cleared = snapshot(browser)
            check(cleared["bp07"] == [] and cleared["bp15"] == [] and cleared["count"] == "0" and not cleared["instruction"]
                  and not cleared["notice"], f"confirmed Reset review clears decisions, edits, comments, and the instruction (got {cleared})")
            browser.send("Page.reload")
            browser.wait_loaded()
            check(snapshot(browser)["count"] == "0" and browser.js(f"{ref}.dataset.mark") == "" and not any(browser.js(folds))
                  and browser.js(groups).get("BP-07") == ["BP-05"],
                  "the reset, folded BP-07 and its folded sidebar group opened again included, survives a reload")

            type_into(browser, f"({CARD.format(rid='BP-26')}).querySelector('textarea[id^=\"comment-\"]')", QUESTION)
            asked = snapshot(browser)
            lines = asked["instruction"].rstrip().splitlines()
            check(asked["count"] == "1" and asked["bp26"] == [] and lines[2].startswith("1. BP-26 ") and "[question from the reviewer]" in asked["instruction"]
                  and QUESTION in asked["instruction"] and "Do not apply their fixes." in asked["instruction"]
                  and "Proposed After" in asked["instruction"] and lines[-1].endswith("exports again.") and "Change no files." in lines[-1],
                  f"a comment on an undecided fix exports as a question with its finding, and a questions-only export changes no files (got {asked})")
            click(browser, "BP-07", "accept")
            mixed = snapshot(browser)["instruction"]
            check("answer any question it asks" in mixed and QUESTION in mixed and "Do not run an audit, mechanical checker" in mixed.rstrip().splitlines()[-1]
                  and "Answer the reviewer's questions, if any, then briefly report" in mixed,
                  "with a fix to apply, the question stays and answers precede the completion summary without an audit")
            browser.js("window.confirm = () => true; document.getElementById('resetReview').click()")

            prior = json.loads(SAMPLE.read_text(encoding="utf-8"))  # the next round's page: BP-43 was rejected with a reason
            next(f for f in prior["failures"] if f["rule"] == "BP-43")["reviewer_reason"] = REASON  # it keeps its fix
            (tmp / "prior.json").write_text(json.dumps(prior), encoding="utf-8")
            result = subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPT), str(tmp / "prior.json"), str(tmp / "prior.html")],
                                    capture_output=True, text=True, check=False)
            check(result.returncode == 0, f"a page with reviewer_reason renders (stderr: {result.stderr.strip()})")
            browser.send("Page.navigate", {"url": (tmp / "prior.html").as_uri()})
            browser.wait_loaded()
            card43 = CARD.format(rid="BP-43")
            seen = browser.js(f"""(() => {{ const c = {card43};
              return {{mark: c.dataset.mark, comment: c.querySelector('textarea[id^="comment-"]').value,
                      accept: c.querySelector('button.act-accept').disabled, edit: c.querySelector('button.act-edit').disabled,
                      reject: c.querySelector('button.act-reject').disabled, shown: c.textContent.includes({json.dumps(REASON)}),
                      instruction: document.getElementById('exportText').value}}; }})()""")
            check(seen["mark"] == "reject" and seen["comment"] == REASON and not seen["accept"] and not seen["edit"] and not seen["reject"]
                  and seen["shown"], f"a reviewer_reason card starts rejected with the reason, Accept and Edit still on (got {seen})")
            check("BP-43" in seen["instruction"] and REASON in seen["instruction"] and "Do not apply them." in seen["instruction"],
                  "the export carries the earlier rejection and its reason on to the next round")
            check("Stop after this summary and offer," in seen["instruction"].rstrip().splitlines()[-1]
                  and "Offer to rerun the audit on request." in seen["instruction"],
                  "the rejection-only export stops without an audit")
            asked_text = browser.js("(() => { let t = ''; window.confirm = m => { t = m; return false; }; document.getElementById('resetReview').click(); return t; })()")
            check("Rejections from an earlier round stay rejected." in asked_text,
                  f"on a page with earlier rejections, Reset says they stay (got {asked_text!r})")
            click(browser, "BP-43", "accept")
            flipped = browser.js(f"""(() => ({{mark: ({card43}).dataset.mark, comment: ({card43}).querySelector('textarea[id^="comment-"]').value,
              instruction: document.getElementById('exportText').value}}))()""")
            check(flipped["mark"] == "accept" and flipped["comment"] == "" and "1. BP-43 " in flipped["instruction"]
                  and "[rejected by the reviewer]" not in flipped["instruction"] and REASON not in flipped["instruction"],
                  f"Accept switches an earlier rejection straight to a fix to apply, and the old reason does not travel along (got {flipped})")
            click(browser, "BP-43", "accept")
            check("BP-43" not in snapshot(browser)["instruction"], "un-accepting leaves it undecided and out of the export")
            browser.js("window.confirm = () => true; document.getElementById('resetReview').click()")
            click(browser, "BP-43", "reject")
            check("BP-43" not in snapshot(browser)["instruction"], "un-rejecting drops it from the export")
            browser.js("window.confirm = () => true; document.getElementById('resetReview').click()")
            check(browser.js(f"({card43}).dataset.mark") == "reject", "Reset review restores the earlier rejection")

            errors = [e for e in browser.events if e.get("method") == "Runtime.exceptionThrown"
                      or (e.get("method") == "Runtime.consoleAPICalled" and e["params"].get("type") == "error")]
            check(not errors, f"no console error or exception (got {[e['method'] for e in errors]})")
        finally:
            browser.close()

    print(f"\n{'FAILED' if FAILURES else 'PASSED'}: {len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
