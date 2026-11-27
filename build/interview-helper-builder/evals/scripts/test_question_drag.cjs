const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const data = JSON.parse(html.match(/id="reviewData">([\s\S]*?)<\/script>/)[1]);
const js = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const match = { '[data-drag]': e => e.dataset.drag, '[data-question]': e => e.dataset.question, '[data-section]': e => e.dataset.section, '.section-head': e => e.className === 'section-head' };

class Element {
  constructor(dataset = {}, className = '') { this.dataset = dataset; this.className = className; this.children = []; this.style = {}; this.events = {}; this.parentElement = null; this.textContent = '';
    this.classes = new Set(); this.classList = { add: c => this.classes.add(c), remove: c => this.classes.delete(c) }; }
  addEventListener(name, fn) { this.events[name] = fn; }
  setAttribute() {}
  setPointerCapture(id) { this.capture = id; }
  hasPointerCapture(id) { return this.capture === id; }
  releasePointerCapture() { this.capture = null; }
  getBoundingClientRect() { return this.box || { top: 0, height: 100 }; }
  remove() { if (this.parentElement) this.parentElement.children.splice(this.parentElement.children.indexOf(this), 1); this.parentElement = null; }
  append(el) { el.remove(); el.parentElement = this; this.children.push(el); }
  prepend(el) { el.remove(); el.parentElement = this; this.children.unshift(el); }
  before(el) { this.insertAdjacentElement('beforebegin', el); }
  insertAdjacentElement(where, el) { const p = this.parentElement; el.remove(); el.parentElement = p; p.children.splice(p.children.indexOf(this) + (where === 'afterend' ? 1 : 0), 0, el); }
  get nextElementSibling() { const s = this.parentElement?.children; return s ? s[s.indexOf(this) + 1] || null : null; }
  closest(sel) { for (let e = this; e; e = e.parentElement) if (match[sel]?.(e)) return e; return null; }
  querySelector(sel) { return this.find(e => sel.startsWith('.') ? e.className === sel.slice(1) : false); }
  find(fn) { for (const c of this.children) { if (fn(c)) return c; const d = c.find(fn); if (d) return d; } return null; }
  contains() { return true; }
}

function gesture(outcome) {
  const body = new Element(), root = new Element(), docEvents = {}, windowEvents = {};
  body.append(root);
  const cards = {};
  for (const s of data.spec.sections) {
    const section = new Element({ section: s.id }), list = new Element({}, 'questions');
    section.append(new Element({}, 'section-head')); section.append(list); root.append(section);
    for (const q of s.questions) {
      const card = new Element({ question: q.id }), handle = new Element({ drag: 'question', id: q.id });
      const qid = new Element({}, 'qid'), title = new Element({}, 'q-title'); qid.textContent = '1.1'; title.textContent = q.title || '';
      [handle, qid, title].forEach(e => card.append(e)); list.append(card); cards[q.id] = { card, handle };
    }
  }
  const ids = data.spec.sections.flatMap(s => s.questions.map(q => q.id)), [first] = ids, last = ids[ids.length - 1];
  const lastSection = data.spec.sections.find(s => s.questions.some(q => q.id === last)).id;
  let pointAt = cards[last].card;
  const context = { document: { getElementById: () => ({ textContent: JSON.stringify(data) }), body,
    createElement: () => new Element(), elementFromPoint: () => pointAt, addEventListener: (n, fn) => { docEvents[n] = fn; } },
    window: { addEventListener: (n, fn) => { windowEvents[n] = fn; }, scrollBy() {}, innerHeight: 1000 } };
  vm.createContext(context); vm.runInContext(js, context); context.root = root;
  vm.runInContext('persist=()=>{};render=()=>{};bindQuestionDrag(root);', context);
  const base = { pointerId: 1, isPrimary: true, button: 0, preventDefault() {} };
  root.events.pointerdown({ ...base, target: cards[first].handle, clientX: 10, clientY: 10 });
  docEvents.pointermove({ ...base, clientX: 10, clientY: 12 });
  assert.equal(body.children.length, 1, 'a click or tiny movement does not start dragging');
  docEvents.pointermove({ ...base, clientX: 10, clientY: 80 });
  assert.equal(body.children[1].className, 'q-ghost', 'a ghost chip follows the pointer, not a native drag image');
  assert.match(body.children[1].textContent, /1\.1/);
  assert.ok(cards[first].card.classes.has('q-moving'));
  assert.equal(cards[last].card.nextElementSibling?.className, 'q-drop', 'the drop line marks the lower half of the target');
  docEvents.pointerup({ ...base, pointerId: 2 });
  assert.equal(body.children.length, 2, 'another pointer cannot finish this gesture');
  if (outcome === 'drop') docEvents.pointerup(base);
  if (outcome === 'outside') { pointAt = null; docEvents.pointerup(base); }
  if (outcome === 'escape') docEvents.keydown({ key: 'Escape', preventDefault() {} });
  if (outcome === 'cancel') docEvents.pointercancel(base);
  if (outcome === 'blur') windowEvents.blur();
  if (outcome === 'reset') docEvents.reviewreset();
  const where = vm.runInContext(`(()=>{const s=draft.sections.find(s=>s.questions.some(q=>q.id===${JSON.stringify(first)}));return s.id+':'+s.questions.map(q=>q.id).join()})()`, context);
  const moved = where.startsWith(lastSection + ':') && where.endsWith(`${last},${first}`);
  assert.equal(moved, outcome === 'drop', `${outcome}: ${where}`);
  assert.equal(body.children.length, 1, 'the ghost is cleaned up');
  assert.ok(!cards[first].card.classes.has('q-moving'));
  assert.equal(root.capture, null, 'pointer capture is released');
}
for (const outcome of ['drop', 'outside', 'escape', 'cancel', 'blur', 'reset']) gesture(outcome);
