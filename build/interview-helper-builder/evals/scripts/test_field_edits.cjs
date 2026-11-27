const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const data = JSON.parse(html.match(/id="reviewData">([\s\S]*?)<\/script>/)[1]);
const js = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const store = new Map(), nodes = new Map();
function node(id) {
  if (!nodes.has(id)) nodes.set(id, {
    value: '', textContent: '', innerHTML: '', hidden: false, listeners: {},
    addEventListener(name, fn) { (this.listeners[name] ||= []).push(fn); this[name] = event => { for (const f of this.listeners[name]) f(event); }; },
    focus() { ctx.document.activeElement = this; }, select() {},
    setAttribute(k, v) { this[k] = v; },
    showModal() { this.open = true; }, close() { this.open = false; },
    querySelectorAll(selector) {
      if (selector === '[data-undo]') return [...this.innerHTML.matchAll(/<button\b([^>]*)>/g)].filter(([, a]) => a.includes('data-undo=')).map(([, attrs]) => ({
        dataset: Object.fromEntries([...attrs.matchAll(/data-(undo|kind|id|field|index)="([^"]*)"/g)].map(([, k, v]) => [k, v])),
        focus() { ctx.document.activeElement = this; },
      }));
      return [];
    },
  });
  return nodes.get(id);
}
node('reviewData').textContent = JSON.stringify(data);
const ctx = {
  document: { getElementById: node, activeElement: null, addEventListener: node('document').addEventListener.bind(node('document')), dispatchEvent: event => node('document')[event.type]?.(event) },
  window: node('window'),
  localStorage: { getItem: k => store.get(k) || null, setItem: (k, v) => store.set(k, v), removeItem: k => store.delete(k) },
  navigator: { clipboard: { writeText: async () => {} } },
};
vm.createContext(ctx);
vm.runInContext(js, ctx);
const run = text => vm.runInContext(text, ctx);
run('render();bind();');
const collected = () => JSON.parse(run('JSON.stringify(collect())'));
run('draft.sections[0].questions[0].ask="Walk through one cache.";persist();render();');
assert.deepEqual(collected().edits, [{ kind: 'question', id: 'q1', field: 'ask', value: 'Walk through one cache.' }]);
assert.match(node('changeItems').innerHTML, /Edit ask on 1\.1/);
run('intents.question.q1=["Harder","More concrete"];persist();render();');
assert.equal(collected().comments[0].text, '[Harder] [More concrete]');
run('comments.question.q1="ask about eviction";persist();render();');
assert.equal(collected().comments[0].text, '[Harder] [More concrete] ask about eviction');
const before = collected();
run('undoRequest("edit","question","q1","ask");persist();render();');
assert.equal(collected().edits, undefined);
assert.equal(collected().comments[0].text, before.comments[0].text);
run('undoRequest("comment","question","q1");persist();render();');
assert.equal(collected().comments, undefined);
assert.equal(run('JSON.stringify(intents.question)'), '{}');
run('timing.section.s1=40;persist();');
assert.ok(run('copyProblems().length') > 0);
run('exportFeedback()');
assert.equal(node('copyDialog').open, true);
assert.match(node('copyProblems').innerHTML, /60m/);
run('exportFeedback(true)');
assert.equal(node('copyDialog').open, false);

// Exercise the page's bound resize and expand handlers with a reflowing field.
let fieldWidth = 400, contentHeight = 80, folded = false;
const field = {
  style: { height: 'auto' },
  get clientWidth() { return folded ? 0 : fieldWidth; },
  get clientHeight() { return folded ? 0 : Math.max(18, (parseFloat(this.style.height) || 20) - 2); },
  get offsetHeight() { return folded ? 0 : this.clientHeight + 2; },
  get scrollHeight() { return folded ? 0 : Math.max(contentHeight, this.clientHeight); },
};
node('sections').querySelectorAll = selector => selector === 'textarea[data-edit]' ? [field] : [];
run('render();');
const originalRequests = collected();
fieldWidth = 200; contentHeight = 240;
node('window').resize?.({ type: 'resize' });
assert.ok(field.clientHeight >= field.scrollHeight, 'narrowing the viewport must keep all wording visible');
fieldWidth = 400; contentHeight = 80;
node('window').resize?.({ type: 'resize' });
assert.ok(field.clientHeight <= contentHeight + 2, 'widening the viewport must remove stale blank height');

const section = { classList: { toggle(_name, value) { folded = value; } } };
const collapse = { dataset: { collapse: 's1' }, label: 'Collapse section 1',
  closest() { return section; }, setAttribute(k, v) { if (k === 'aria-label') this.label = v; },
  getAttribute() { return this.label; },
};
const toggle = () => node('sections').click({ target: { closest: s => s === '[data-collapse]' ? collapse : null } });
toggle();
assert.equal(folded, true);
run('render();');
fieldWidth = 200; contentHeight = 240;
toggle();
assert.equal(folded, false);
assert.ok(field.clientHeight >= field.scrollHeight, 'reopening after a folded render must refit wording');
assert.deepEqual(collected(), originalRequests, 'layout changes must not change review requests');
console.log('ok');
