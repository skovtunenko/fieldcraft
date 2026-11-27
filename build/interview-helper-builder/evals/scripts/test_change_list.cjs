const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const data = JSON.parse(html.match(/id="reviewData">([\s\S]*?)<\/script>/)[1]);
const js = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const store = new Map(), nodes = new Map();
const decode = s => s.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
function buttonsFrom(source) {
  return [...source.matchAll(/<button\b([^>]*)>/g)].map(([, attrs]) => {
    const attr = name => (attrs.match(new RegExp(`\\b${name}="([^"]*)"`)) || [])[1] || '';
    const btn = {
      dataset: { undo: attr('data-undo'), kind: attr('data-kind'), id: attr('data-id'), index: attr('data-index') },
      label: decode(attr('aria-label')),
      type: attr('type'),
      focus(opts) { btn.focused = true; btn.focusOpts = opts || null; ctx.document.activeElement = btn; },
    };
    return btn;
  });
}
function node(id) {
  if (!nodes.has(id)) nodes.set(id, {
    value: '', textContent: '', innerHTML: '', hidden: false, listeners: {},
    addEventListener(name, fn, capture) {
      const list = this.listeners[name] ||= [];
      capture === true ? list.unshift(fn) : list.push(fn);
      if (name !== 'close') this[name] = event => { for (const f of list) f(event); };
    },
    focus(opts) { this.focused = true; this.focusOpts = opts || null; ctx.document.activeElement = this; },
    select() {}, setAttribute(k, v) { this[k] = v; }, reset() {},
    showModal() {}, close() {},
    querySelectorAll(selector) {
      if (selector === '[data-undo]') return buttonsFrom(this.innerHTML);
      if (selector !== '[data-action]') return [];
      return [...this.innerHTML.matchAll(/<button\b([^>]*)>/g)].filter(([, attrs]) => attrs.includes('data-action=')).map(([, attrs]) => ({
        dataset: Object.fromEntries([...attrs.matchAll(/data-(kind|id|action)="([^"]*)"/g)].map(([, key, value]) => [key, value])),
        disabled: /\bdisabled\b/.test(attrs),
        focus() {},
      }));
    },
  });
  return nodes.get(id);
}
node('reviewData').textContent = JSON.stringify(data);
const ctx = {
  document: {
    getElementById: node, activeElement: null,
    addEventListener: node('document').addEventListener.bind(node('document')),
    dispatchEvent: event => node('document')[event.type]?.(event),
  },
  window: node('window'),
  localStorage: { getItem: k => store.get(k) || null, setItem: (k, v) => store.set(k, v), removeItem: k => store.delete(k) },
};
vm.createContext(ctx);
vm.runInContext(js, ctx);
const run = text => vm.runInContext(text, ctx);
const listRows = () => [...node('changeItems').innerHTML.matchAll(/<li>([\s\S]*?)<\/li>/g)].map(m => ({
  kind: (m[1].match(/class="change-kind">([^<]*)</) || [])[1],
  text: decode((m[1].match(/class="change-text">([^<]*)</) || [])[1] || ''),
  undo: (m[1].match(/data-undo="([^"]*)"/) || [])[1],
  type: (m[1].match(/type="([^"]*)"/) || [])[1],
  label: decode((m[1].match(/aria-label="([^"]*)"/) || [])[1] || ''),
}));
const clickUndo = index => {
  const btn = buttonsFrom(node('changeItems').innerHTML)[index];
  assert.ok(btn, `no undo button at ${index}`);
  node('changeList').click({ target: { closest: sel => sel === '[data-undo]' ? btn : null } });
  return ctx.document.activeElement;
};
const collected = () => JSON.parse(run('JSON.stringify(collect())'));
const promptOf = () => run('buildPrompt()');
const payloadOf = prompt => JSON.parse(prompt.match(/<interview_review>\n([\s\S]*?)\n<\/interview_review>/)[1]);
function assertLabels(rows) {
  for (const row of rows) {
    assert.equal(row.type, 'button');
    assert.equal(row.label, `Undo: ${row.text}`);
  }
}
const reset = () => run('draft=clone(BASE.spec);excluded=new Set();excludedSections=new Set();comments=emptyComments();timing=emptyTiming();collapsed=new Set();persist();render();');

assert.match(html, /<ul id="changeItems"[^>]*aria-labelledby="changeHeading"/);
assert.match(html, /id="changeEmpty">No changes yet\./);
assert.ok(html.indexOf('id="changeList"') < html.indexOf('Your review prompt'));
assert.match(html, /\.change-list li\{[^}]*flex-wrap:wrap/);
assert.match(html, /\.change-text\{[^}]*overflow-wrap:anywhere/);
assert.match(html, /\.export \.change-list button\{margin-top:0\}/);

run('render();bind();');
assert.equal(node('changeHeading').textContent, 'Your changes (0)');
assert.equal(node('changeEmpty').hidden, false);
assert.equal(node('changeItems').hidden, true);
assert.deepEqual(listRows(), []);
assert.equal(node('output').value, promptOf());

run('addSection("Culture fit","5m","")');
assert.deepEqual(listRows().map(r => r.undo), ['add-section']);
assert.ok(collected().layout, 'an addition still changes the saved layout');
assert.equal(listRows()[0].text, 'Add section 3 "Culture fit"');

reset();
run('comments.section.s2="Probe <trade-offs>"');
run('excluded.add("q2")');
run('excludedSections.add("s2")');
run('timing.section.s1=15');
run('addSection("Culture fit","5m","")');
run('addQuestion("s1")');
run('items(draft).question.get("review-question-1").request="How do you handle conflict"');
run('moveQuestion("q1","s2");persist();render();');
const expected = [
  'Add section 3 "Culture fit"',
  'Add question "How do you handle conflict" in section 1 "Runtime"',
  'Reordered sections/questions',
  'Remove question 1.1 "Recovery"',
  'Remove section 2 "Judgment"',
  'Section 1 "Runtime" timebox 10 → 15 min',
  'Comment on section 2 "Judgment": "Probe <trade-offs>"',
];
let rows = listRows();
assert.deepEqual(rows.map(r => r.text), expected, JSON.stringify(rows.map(r => r.text), null, 2));
assert.deepEqual(rows.map(r => r.undo), ['add-section', 'add-question', 'layout', 'exclude', 'exclude-section', 'timing', 'comment']);
assert.deepEqual(rows.map(r => r.kind), ['Add', 'Add', 'Move', 'Remove', 'Remove', 'Time', 'Comment']);
assert.equal(node('changeHeading').textContent, 'Your changes (7)');
assert.equal(node('changeEmpty').hidden, true);
assertLabels(rows);
assert.match(node('changeItems').innerHTML, /Probe &lt;trade-offs&gt;/);
assert.doesNotMatch(node('changeItems').innerHTML, /Probe <trade/);
const prompt = promptOf();
assert.equal(node('output').value, prompt);
assert.deepEqual(payloadOf(prompt), collected());
assert.equal(prompt.includes('Probe <trade-offs>'), false);
assert.ok(prompt.includes('Probe \\u003ctrade-offs>'));
assert.equal(run('buildPrompt.toString().includes("changeItems")'), false);
assert.equal(run('buildPrompt.toString().includes("renderChanges")'), false);
run('window.__renderChanges=renderChanges;renderChanges=function(){};render();');
assert.equal(promptOf(), prompt, 'drawing the list changed the prompt');
run('renderChanges=window.__renderChanges;render();');
assert.equal(node('output').value, prompt);
assert.equal(promptOf(), prompt);

const beforeUndo = collected();
const focusedTiming = clickUndo(6);
rows = listRows();
assert.equal(focusedTiming.label, `Undo: ${expected[5]}`);
assert.equal(focusedTiming.focusOpts.preventScroll, true);
assert.deepEqual(rows.map(r => r.text), expected.slice(0, 6));
const afterUndo = collected();
const withoutComment = { ...beforeUndo };
delete withoutComment.comments;
assert.deepEqual(afterUndo, withoutComment);
assert.equal(store.get(run('storageKey')), JSON.stringify(afterUndo));
assert.equal(node('output').value, promptOf());
assert.equal(payloadOf(node('output').value).comments, undefined);
assert.ok(node('output').value.includes('Culture fit'));
assert.equal(node('output').value.includes('trade-offs'), false);

reset();
run('comments.section.s1="Keep me";moveSection("s2",-1);moveQuestion("q1","s2");persist();render();');
const moved = collected();
assert.ok(moved.layout);
assert.deepEqual(moved.comments, [{ kind: 'section', id: 's1', text: 'Keep me' }]);
const focusedComment = clickUndo(0);
assert.equal(focusedComment.label, 'Undo: Comment on section 1 "Runtime": "Keep me"');
const restored = collected();
assert.equal(restored.layout, undefined);
assert.deepEqual(restored.comments, moved.comments);
assert.equal(run('JSON.stringify(layout(draft))'), run('JSON.stringify(layout(BASE.spec))'));
assert.equal(listRows()[0].text, 'Comment on section 1 "Runtime": "Keep me"');
assert.equal(node('output').value, promptOf());
assert.equal(payloadOf(node('output').value).layout, undefined);
assert.ok(node('output').value.includes('Keep me'));

reset();
run('addQuestion("s2")');
run('items(draft).question.get("review-question-1").request="On call"');
run('moveQuestion("q1","s2");persist();render();');
assert.deepEqual(listRows().map(r => r.undo), ['add-question', 'layout']);
clickUndo(1);
assert.equal(run('draft.sections.map(s=>s.questions.map(q=>q.id).join()).join("|")'), 'q1,q2|q3,review-question-1');
assert.deepEqual(collected().addedQuestions, [{ id: 'review-question-1', text: 'On call' }]);
assert.ok(collected().layout, 'the added question still belongs in the saved layout');
assert.deepEqual(listRows().map(r => r.text), ['Add question "On call" in section 2 "Judgment"']);

reset();
run('addSection("Culture fit","","Scope for culture")');
run('moveQuestion("q1","review-section-1");persist();render();');
assert.ok(listRows().some(r => r.undo === 'add-section'));
assert.ok(listRows().some(r => r.text.startsWith('Comment on section')));
clickUndo(listRows().findIndex(r => r.undo === 'add-section'));
assert.equal(collected().addedSections, undefined);
assert.equal(run('comments.section["review-section-1"]'), undefined);
assert.equal(run('draft.sections.some(s=>s.questions.some(q=>q.id==="q1"))'), true);
assert.equal(run('items(draft).question.get("q1").title'), 'A real system');

reset();
run('comments.question.q1="One";comments.question.q2="Two";persist();render();');
const focusedPrev = clickUndo(1);
assert.equal(focusedPrev.label, 'Undo: Comment on 1.1 "A real system": "One"');
assert.deepEqual(collected().comments, [{ kind: 'question', id: 'q1', text: 'One' }]);
assert.equal(listRows().map(r => r.text).join('|'), 'Comment on 1.1 "A real system": "One"');

reset();
run('excludedSections.add("s1");collapsed.add("s1");persist();render();');
assert.match(node('meta').innerHTML, /1 \/ 3 questions kept/);
assert.equal(String(node('copyCount').textContent), '1');
assert.match(node('coverage').innerHTML, /No longer tested/);
assert.doesNotMatch(node('timeline').innerHTML, /data-resize="s1"/);
assert.equal(listRows()[0].text, 'Remove section 1 "Runtime"');
assert.equal(clickUndo(0), node('changeHeading'));
assert.equal(node('changeHeading').focusOpts.preventScroll, true);
assert.equal(node('changeHeading').textContent, 'Your changes (0)');
assert.equal(node('changeEmpty').hidden, false);
assert.match(node('meta').innerHTML, /3 \/ 3 questions kept/);
assert.equal(node('copyCount').hidden, true);
assert.match(node('timeline').innerHTML, /data-resize="s1"/);
assert.match(node('coverage').innerHTML, /Section 1/);
assert.doesNotMatch(node('coverage').innerHTML, /No longer tested/);
assert.equal(run('collapsed.has("s1")'), false);
assert.equal(run('excludedSections.size'), 0);
assert.equal(store.get(run('storageKey')), run('JSON.stringify(collect())'));
assert.equal(node('output').value, promptOf());

reset();
run('timing.question.q2=5;persist();render();');
assert.equal(listRows()[0].text, 'Question 1.2 "Recovery" no estimate → 5 min');
clickUndo(0);
assert.equal(run('collect().timing'), undefined);
assert.equal(promptOf().includes('Keep the reviewer timing values'), false);

reset();
node('sections').input({ target: { dataset: { comment: 'section', id: 's1' }, value: 'Shorter opening' } });
assert.equal(listRows()[0].text, 'Comment on section 1 "Runtime": "Shorter opening"');
assert.equal(node('changeHeading').textContent, 'Your changes (1)');
assert.equal(node('output').value, promptOf());
node('sections').input({ target: { dataset: { comment: 'section', id: 's1' }, value: '   ' } });
assert.deepEqual(listRows(), []);
assert.equal(node('changeEmpty').hidden, false);
assert.equal(node('changeHeading').textContent, 'Your changes (0)');

reset();
run('addQuestion("s1")');
assert.equal(listRows().length, 1);
assert.equal(node('changeHeading').textContent, 'Your changes (1)');
assert.equal(String(node('copyCount').textContent), '1');
assert.equal(node('copyCount').hidden, false);
assert.equal(node('copyReview')['aria-label'], 'Copy review prompt, 1 change');
assert.equal(collected().addedQuestions.length, 1);
assert.ok(collected().layout, 'the prompt still carries layout for an added question');
assert.equal(node('output').value, promptOf());
reset();
run('moveSection("s2",-1);comments.section.s1="A note";persist();render();');
assert.equal(listRows().length, 2);
assert.equal(node('changeHeading').textContent, 'Your changes (2)');
assert.equal(String(node('copyCount').textContent), '2');
assert.equal(node('copyCount').hidden, false);
assert.equal(node('copyReview')['aria-label'], 'Copy review prompt, 2 changes');
clickUndo(0);
clickUndo(0);
assert.equal(node('changeHeading').textContent, 'Your changes (0)');
assert.equal(node('copyCount').hidden, true);
assert.equal(node('copyCount').textContent, '');
assert.equal(node('copyReview')['aria-label'], 'Copy review prompt');
assert.equal(node('changeEmpty').hidden, false);
assert.deepEqual(listRows(), []);
assert.match(html, /id="changeEmpty">No changes yet\./);
assert.equal(node('output').value, promptOf());

reset();
const long = `${'ask about eviction '.repeat(4)}tail`;
run(`comments.question.q1=${JSON.stringify(long)};persist();render();`);
const quoted = listRows()[0].text.match(/: "(.+)"$/)[1];
assert.ok(quoted.length <= 60, quoted);
assert.ok(quoted.endsWith('…'));
assert.ok(long.startsWith(quoted.slice(0, -1)));
assert.equal(listRows()[0].text, 'Comment on 1.1 "A real system": "' + quoted + '"');
