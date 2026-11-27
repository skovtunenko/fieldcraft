const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const fields = ['finalNotes', 'previousFeedback', 'transcriptInput', 'promptOutput'];
const elements = new Map();
const buttons = new Map();
let copied = '', focused = '', selected = '';
for (const id of fields) {
  assert.ok(html.includes(`data-syntax-for="${id}"`), `missing controls: ${id}`);
  assert.ok(html.includes(`id="${id}Preview"`), `missing preview: ${id}`);
  for (const suffix of ['', 'Preview', 'Count']) elements.set('#' + id + suffix, {
    value: '', innerHTML: '', textContent: '', hidden: false, placeholder: 'Empty source',
    listeners: {}, addEventListener(name, fn) { this.listeners[name] = fn; },
    focus() { focused = id; }, select() { selected = id; },
    classList: { add() {}, remove() {}, toggle() {} },
  });
  buttons.set(id, ['edit', 'preview'].map(mode => ({
    dataset: { syntaxMode: mode }, attributes: {}, listeners: {},
    setAttribute(k, v) { this.attributes[k] = v; },
    addEventListener(k, fn) { this.listeners[k] = fn; },
  })));
}
const ctx = {
  document: {
    addEventListener() {},
    querySelector: selector => elements.get(selector),
    querySelectorAll: selector => buttons.get(selector.match(/data-syntax-for="([^"]+)"/)?.[1]) || [],
    execCommand(command) { assert.equal(command, 'copy'); copied = elements.get('#promptOutput').value; },
  },
  navigator: { clipboard: { async writeText(value) { copied = value; } } },
  setTimeout() {}, clearTimeout() {},
};
vm.createContext(ctx);
vm.runInContext(script + '\nsaveState=()=>{};toast=()=>{};', ctx);
const plain = marked => marked.replace(/<span class="syn-[a-z]+">|<\/span>/g, '')
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
  .replace(/&#39;/g, "'").replace(/&amp;/g, '&');
const input = '# Summary\n**Strong** *detail*\n- Evidence\n> Quote\n`code` [link](javascript:alert(1))\n' +
  '<note owner="Alex" status=\'ok\'>A &amp; B</note>\n<!-- multi\nline -->\n<![CDATA[<raw>]]>\n' +
  '<img src=x onerror="alert(1)">\n</script>\n```xml\n<item id="1">**literal**</item>\n```\n\n';
const highlighted = ctx.highlightSyntax(input);
assert.equal(plain(highlighted), input, 'highlighting changed the source');
assert.ok(!/<(?!\/?span\b)/.test(highlighted), 'unescaped user markup reached preview');
for (const token of ['heading', 'strong', 'em', 'marker', 'code', 'link', 'tag', 'attr', 'string', 'entity', 'comment', 'fence']) {
  assert.ok(highlighted.includes(`class="syn-${token}"`), `missing token: ${token}`);
}
assert.ok(highlighted.includes('class="syn-code">**literal**'), 'Markdown emphasis styled inside a code fence');
const sections = ctx.highlightSyntax('<live_evidence>\n<title>1. A &amp; B</title>\r\n</live_evidence>');
assert.ok(sections.startsWith('<span class="syn-block">&lt;live_evidence&gt;</span>'), 'line-alone tag not emphasised');
assert.ok(sections.includes('<span class="syn-tag">&lt;title&gt;</span>'), 'inline tag emphasised as a section');
assert.ok(sections.endsWith('<span class="syn-block">&lt;/live_evidence&gt;</span>'), 'closing section tag not emphasised');
const snake = ctx.highlightSyntax('notes/interview_with_Enterprise_AI_Architect.json _real_ __bold__');
assert.ok(!snake.includes('_with_<') && !snake.includes('>_AI_<'), 'snake_case path styled as emphasis');
assert.ok(snake.includes('class="syn-em">_real_') && snake.includes('class="syn-strong">__bold__'), 'standalone underscore emphasis lost');
for (const text of ['', '<script', 'unclosed ```', '~~~~xml\n<a>\n~~~\n', '\tline\r\nnext\n', 'x'.repeat(200000)]) {
  assert.equal(plain(ctx.highlightSyntax(text)), text);
}
for (const [index, id] of fields.entries()) {
  const key = ['notes', 'previousFeedback', 'transcript', 'prompt'][index];
  ctx.source = input;
  vm.runInContext(`state.final.${key}=source;bindText('${id}','${key}');`, ctx);
  const text = elements.get('#' + id), preview = elements.get('#' + id + 'Preview');
  assert.equal(text.value, input, 'restore lost source');
  assert.equal(text.hidden, false);
  assert.equal(preview.hidden, true);
  buttons.get(id)[1].listeners.click();
  assert.equal(plain(preview.innerHTML), input);
  assert.equal(text.hidden, true);
  assert.equal(buttons.get(id)[1].attributes['aria-pressed'], 'true');
  buttons.get(id)[0].listeners.click();
  assert.equal(text.value, input);
  assert.equal(text.hidden, false);
  assert.equal(focused, id);
  text.value += '\nEdited';text.listeners.input();
  assert.equal(vm.runInContext(`state.final.${key}`, ctx), text.value, 'editing did not persist raw text');
  buttons.get(id)[1].listeners.click();
  assert.equal(plain(preview.innerHTML), text.value, 'preview did not refresh after edit');
}
// Briefing ticks: stamped like marks, rendered and restorable, never prompt evidence.
const brief = vm.runInContext('CONFIG.candidateBriefing', ctx)[0];
const briefList = { innerHTML: '', addEventListener() {} };
let briefShown;
elements.set('#briefingList', briefList);
elements.set('#briefing', { classList: { toggle(name, hidden) { briefShown = !hidden; } } });
ctx.document.querySelectorAll = selector => (selector === '[data-brief]' ? [] : buttons.get(selector.match(/data-syntax-for="([^"]+)"/)?.[1]) || []);
vm.runInContext('stampCalls=0;stampNow=()=>{stampCalls++;return{at:Date.UTC(2026,9,18,8),el:65000}};', ctx);
vm.runInContext('renderBriefing();', ctx);
assert.equal(briefShown, true, 'briefing hidden despite bullets');
assert.match(briefList.innerHTML, /type="checkbox" data-brief="Briefing\."\/>/, 'briefing bullet is not a checkbox');
ctx.onBriefTick({ target: { dataset: { brief }, checked: true } });
assert.equal(vm.runInContext('stampCalls', ctx), 1, 'tick did not stamp (and so cannot start the timer)');
assert.match(briefList.innerHTML, /class="brief-check checked"[\s\S]*checked\/>[\s\S]*01:05/, 'tick not rendered with its time');
ctx.onBriefTick({ target: { dataset: { brief }, checked: false } });
assert.equal(vm.runInContext(`Object.keys(state.briefing).length`, ctx), 0, 'untick kept the stamp');
ctx.onBriefTick({ target: { dataset: { brief }, checked: true } });
assert.equal(vm.runInContext('touched({})', ctx), false);
vm.runInContext('generatePrompt();', ctx);
assert.ok(!elements.get('#promptOutput').value.includes(brief), 'briefing tick leaked into the analysis prompt');
assert.equal(elements.get('#promptOutputPreview').hidden, false, 'generated prompt did not open Preview');
assert.equal(plain(elements.get('#promptOutputPreview').innerHTML), elements.get('#promptOutput').value);
const cloneNodes = new Map();
ctx.document.documentElement = { cloneNode() { return {
  outerHTML: '<html></html>',
  querySelector(selector) {
    if (!cloneNodes.has(selector)) cloneNodes.set(selector, { innerHTML: 'stale highlight', textContent: '' });
    return cloneNodes.get(selector);
  },
}; } };
assert.ok(ctx.buildSavedHtml().startsWith('<!DOCTYPE html>'));
const embeddedText = cloneNodes.get('#embeddedState').textContent;
assert.ok(!embeddedText.includes('<'), 'save embedded executable markup');
const savedFinal = JSON.parse(embeddedText).state.final;
assert.equal(JSON.parse(embeddedText).state.briefing[brief].el, 65000, 'Save HTML dropped the briefing tick');
for (const [index, id] of fields.entries()) {
  assert.equal(cloneNodes.get('#' + id + 'Preview').innerHTML, '', 'save kept stale derived highlights');
  assert.equal(savedFinal[['notes', 'previousFeedback', 'transcript', 'prompt'][index]], elements.get('#' + id).value, 'save changed field source');
}
(async () => {
  await ctx.copyPrompt();
  assert.equal(copied, elements.get('#promptOutput').value, 'clipboard contains highlighted HTML');
  ctx.navigator.clipboard.writeText = async () => { throw Error('blocked'); };
  await ctx.copyPrompt();
  assert.equal(elements.get('#promptOutput').hidden, false, 'fallback tried selecting a hidden textarea');
  assert.equal(selected, 'promptOutput');
  assert.equal(copied, elements.get('#promptOutput').value);
  console.log('Safe syntax preview: highlighting, four-field edit/restore/save, generation, and copy pass');
})().catch(error => { console.error(error);process.exitCode = 1; });
