// M14: the Background block renders opt-in candidate insights escaped, folds with persisted state, hides the insights
// without a profile, frames the sidebar flow, links "→ <index>" asks to their question cards, opens as an overlay from the
// header button, and never reaches the analysis prompt. Usage: node test_profile.cjs <generated-with-profile.html>
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const els = new Map();
const el = sel => {
  if (!els.has(sel)) {
    const cls = new Set(), attrs = {};
    els.set(sel, {
      innerHTML: '', textContent: '', value: '', hidden: false, attrs,
      classList: { add: c => cls.add(c), remove: c => cls.delete(c), toggle: (c, on) => (on ? cls.add(c) : cls.delete(c)), contains: c => cls.has(c) },
      setAttribute: (k, v) => { attrs[k] = v; },
      cloneNode: () => ({ childNodes: ['clone'], querySelectorAll: () => [] }),
      replaceChildren(...n) { this.children = n; },
      showModal() { this.open = true; },
      close() { this.open = false; },
      scrollIntoView() { this.scrolled = true; },
      getBoundingClientRect: () => ({ left: 0, right: 100, top: 0, bottom: 100 }),
    });
  }
  return els.get(sel);
};
const ctx = { document: { addEventListener() {}, querySelector: el, querySelectorAll: () => [], getElementById: id => el('#' + id) }, setTimeout() {}, clearTimeout() {} };
vm.createContext(ctx);
vm.runInContext(script + `
saveState = () => {};
globalThis.t = {
  render: () => renderProfile(),
  fold: v => { state.prepCollapsed = v; applyPrep(); },
  prompt: () => { generatePrompt(); return state.final.prompt; },
  drop: () => { delete CONFIG.candidateProfile; },
  noScope: () => { CONFIG.outOfScope = []; },
  static: () => renderStatic(),
  card: i => renderQuestion(CONFIG.sections.flatMap(s => s.questions)[i]),
};`, ctx);

ctx.t.render();
const body = el('#candidateProfile').innerHTML;
assert.equal(el('#candidateProfile').classList.contains('hidden'), false, 'block hidden with a profile');
assert.match(body, /<p class="portrait">/, 'portrait missing');
assert.match(body, /class="insight standouts"/, 'standouts column missing');
assert.match(body, /class="insight inconsistencies"/, 'inconsistencies column missing');
assert.doesNotMatch(body, /class="insight probes"/, 'empty probes list rendered a column');
assert.match(body, /<q class="insight-ask">How did the two roles overlap\?<\/q>/, 'ask not rendered as a quotation');
assert.match(body, /<span class="insight-src">CV · dates<\/span>/, 'source missing');
assert.match(body, /<a class="q-ref" href="#q1" title="Go to question 1.1">→ 1.1<\/a>/, '→ 1.1 not a link to its question');
// The entry pointing at 1.1 repeats on that card, numbered as in its column, its ask without the arrow; other cards stay clean.
const card = ctx.t.card(0);
assert.match(card, /<div class="q-preps"><div class="insight q-prep inconsistencies"><ul style="counter-reset:item 0"><li><span class="q-prep-tag">/, 'linked entry missing on the question card');
assert.match(card, /Doesn't add up<\/span><span>Overlapping roles<\/span><q class="insight-ask">How did the two roles overlap\?<\/q>/, 'card entry text or ask wrong');
assert.doesNotMatch(card, /q-ref/, 'question card links to itself');
assert.ok(card.indexOf('q-preps') < card.indexOf('signal-grid'), 'card entry not above the signals');
assert.doesNotMatch(ctx.t.card(1), /q-preps/, 'unlinked question shows insights');
assert.doesNotMatch(body, /<img/, 'hostile text not escaped');
assert.match(body, /&lt;img src=x onerror=alert\(1\)&gt;/, 'escaped hostile text missing');
// Career timeline: escaped org, computed tenure, parallel rows hatched, bars placed on a shared axis.
assert.match(body, /class="insight timeline"/, 'timeline missing');
assert.match(body, /<b>Citi &lt;b&gt;<\/b> · Architect/, 'timeline org not escaped');
assert.match(body, /Aug 2020 – Jul 2022 · 2y</, 'Citi tenure not computed as 2y');
assert.match(body, /Jul 2020 – Feb 2025 · 4y 8m</, 'PwC tenure not computed as 4y 8m');
assert.match(body, /class="tl-row parallel"><div class="tl-label"><span><b>PwC/, 'parallel entry not marked');
assert.match(body, /<span class="tl-scale">650 apps<\/span>/, 'scale line missing');
const bars = [...body.matchAll(/class="tl-bar" style="left:([\d.]+)%;width:([\d.]+)%"/g)].map(m => [+m[1], +m[2]]);
assert.equal(bars.length, 2, 'one bar per entry');
assert.ok(bars.every(([l, w]) => l >= 0 && l + w <= 100.01), 'bar outside the axis');
assert.ok(bars[1][0] < bars[0][0] && bars[1][0] + bars[1][1] > bars[0][0] + bars[0][1], 'PwC bar does not span the Citi bar');
assert.equal(ctx.dateLabel('now'), 'now');
assert.equal(ctx.tenure(0), '<1m');

// The sidebar link scrolls to the block like a section link; the header button opens a copy over the page without scrolling;
// a "→" link inside closes it and scrolls to the question; a click outside the box closes it, a click on its own padding does not.
const link = href => ({ getAttribute: () => href, classList: { contains: () => false } });
const click = (target, x = 5) => ({ target, preventDefault() {}, clientX: x, clientY: 5 });
ctx.navTo(click({ closest: () => link('#prep') }));
assert.equal(el('#prep').scrolled, true, 'Background link did not scroll to the block');
assert.ok(!el('#prepPeek').open, 'Background link opened the overlay');
el('#prep').scrolled = false;
ctx.openPeek();
assert.equal(el('#prepPeek').open, true, 'header button did not open the overlay');
assert.deepEqual(el('#prepPeekBody').children, ['clone'], 'overlay not filled from Background');
assert.ok(!el('#prep').scrolled, 'opening the overlay scrolled the page');
assert.match(script, /\$\('#openPrep'\)\.addEventListener\('click',openPeek\)/, 'header Background button not bound to the overlay');
assert.match(html, /<span class="tcap">Sections<\/span>[\s\S]*?<div class="tg-row">[\s\S]*?id="openPrep" aria-haspopup="dialog"/, 'Background button not in the header Sections group');
ctx.onPeekClick(click({ closest: s => (s === 'a[href^="#"]' ? link('#q1') : null) }));
assert.equal(el('#prepPeek').open, false, 'question link left the overlay open');
assert.equal(el('#q1').scrolled, true, 'question link did not scroll to the question');
el('#prepPeek').showModal();
const self = Object.assign(el('#prepPeek'), { closest: () => null });
ctx.onPeekClick(click(self, 5));
assert.equal(el('#prepPeek').open, true, 'click inside the overlay closed it');
ctx.onPeekClick(click(self, 500));
assert.equal(el('#prepPeek').open, false, 'click outside the overlay left it open');

ctx.t.fold(true);
assert.equal(el('#prepBody').classList.contains('hidden'), true, 'fold did not hide the body');
assert.equal(el('#prepToggle').attrs['aria-expanded'], 'false');
assert.equal(el('#prepToggle').attrs['aria-label'], 'Expand candidate background');
ctx.t.fold(false);
assert.equal(el('#prepBody').classList.contains('hidden'), false, 'unfold did not show the body');

const prompt = ctx.t.prompt();
assert.ok(prompt.includes('<analysis_task>'), 'prompt not generated');
assert.ok(!prompt.includes('Overlapping roles') && !prompt.includes('Rare mix'), 'profile text leaked into the prompt');

assert.match(script, /class="nav-link nav-special nav-prep" href="#prep"/, 'Background link does not head the sidebar flow');
assert.match(script, /class="nav-link nav-special nav-final" href="#final-section"/, 'Final assessment link not marked special');
assert.match(script, /'briefingList','candidateProfile'/, 'saved HTML keeps rendered profile markup');
assert.match(script, /\$\('#prepToggle'\)\.addEventListener\('click'/, 'fold toggle not bound');
// Out-of-scope topics sit inside Background; the redirect-phrases card is gone (question cues carry redirects).
const prep = html.slice(html.indexOf('<section class="overview prep"'), html.indexOf('<div class="overview" id="briefing"'));
for (const id of ['candidateProfile', 'outOfScopeList']) assert.ok(prep.includes(`id="${id}"`), `${id} not inside Background`);
assert.doesNotMatch(html, /id="redirectList"|Redirect phrases/, 'redirect-phrases card is back');
assert.doesNotMatch(html, /Markdown · XML|English only/, 'removed field labels are back');
assert.match(html, /class="next-step"/, 'paste-into-assistant hint missing');

ctx.t.drop();
ctx.t.render();
assert.equal(el('#candidateProfile').classList.contains('hidden'), true, 'insights visible without a profile');
assert.equal(el('#candidateProfile').innerHTML, '', 'insights not emptied without a profile');
// Without a profile but with out-of-scope topics Background stays; with neither, the block, its link, and its button hide.
ctx.t.static();
assert.equal(el('#prep').classList.contains('hidden'), false, 'Background hidden while it holds out-of-scope topics');
assert.match(el('#navList').innerHTML, /nav-prep/, 'Background link missing while the block has content');
ctx.t.noScope();
ctx.t.static();
assert.equal(el('#prep').classList.contains('hidden'), true, 'empty Background block still shown');
assert.equal(el('#openPrep').classList.contains('hidden'), true, 'header button shown for an empty Background');
assert.doesNotMatch(el('#navList').innerHTML, /nav-prep/, 'sidebar links to an empty Background');
console.log('Background: escaped insights, linked question cards, overlay, fold state, hidden without a profile, hidden when empty, no redirect card, out of the prompt pass');
