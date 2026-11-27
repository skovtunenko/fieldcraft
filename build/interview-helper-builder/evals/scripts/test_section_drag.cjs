const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const data = JSON.parse(html.match(/id="reviewData">([\s\S]*?)<\/script>/)[1]);
const js = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');

class Element {
  constructor(id = '') { this.dataset = id ? { navSection: id } : {}; this.children = []; this.style = {}; this.events = {}; this.classList = { add() {} }; }
  addEventListener(name, fn) { this.events[name] = fn; }
  setAttribute() {}
  setPointerCapture(id) { this.capture = id; }
  hasPointerCapture(id) { return this.capture === id; }
  releasePointerCapture() { this.capture = null; }
  getBoundingClientRect() { return this.box || { left: 0, right: 200, top: 0, bottom: 200, width: 200, height: 40 }; }
  remove() { if (this.parentElement) this.parentElement.children.splice(this.parentElement.children.indexOf(this), 1); this.parentElement = null; }
  append(el) { el.remove(); el.parentElement = this; this.children.push(el); }
  before(el) { this.insertAdjacentElement('beforebegin', el); }
  insertAdjacentElement(where, el) { const parent = this.parentElement; el.remove(); el.parentElement = parent; parent.children.splice(parent.children.indexOf(this) + (where === 'afterend' ? 1 : 0), 0, el); }
  closest(selector) { return selector === '[data-nav-section]' && this.dataset.navSection ? this : null; }
  contains(el) { return this.children.includes(el); }
  querySelectorAll() { return this.children.filter(el => el.dataset.navSection); }
}

function gesture(outcome) {
  const root = new Element(), body = new Element(), sidebar = new Element(), docEvents = {}, windowEvents = {};
  body.append(sidebar); sidebar.append(root); sidebar.scrollTop = 0;
  const rows = data.spec.sections.map(s => new Element(s.id)); rows.forEach(r => root.append(r));
  rows[1].box = { left: 0, right: 200, top: 50, bottom: 90, width: 200, height: 40 };
  const context = { document: { getElementById: () => ({ textContent: JSON.stringify(data) }), body,
    createElement: () => new Element(), elementFromPoint: () => rows[1], addEventListener: (name, fn) => { docEvents[name] = fn; } },
    window: { addEventListener: (name, fn) => { windowEvents[name] = fn; } } };
  vm.createContext(context); vm.runInContext(js, context); context.root = root;
  vm.runInContext('persist=()=>{};render=()=>{};bindSectionDrag(root);', context);
  const base = { pointerId: 1, isPrimary: true, button: 0, pointerType: 'mouse', preventDefault() {} };
  root.events.pointerdown({ ...base, target: rows[0], clientX: 20, clientY: 20 });
  docEvents.pointermove({ ...base, clientX: 20, clientY: 22 });
  assert.equal(body.children.length, 1, 'a click or tiny movement does not start dragging');
  docEvents.pointermove({ ...base, clientX: 20, clientY: 85 });
  assert.equal(body.children[1], rows[0], 'the original row moves, rather than a clone or drag image');
  assert.match(rows[0].style.transform, /translate/);
  assert.equal(root.children[1].className, 'nav-placeholder');
  docEvents.pointerup({ ...base, pointerId: 2, clientX: 20, clientY: 85 });
  assert.equal(body.children[1], rows[0], 'another pointer cannot finish this gesture');
  if (outcome === 'drop') docEvents.pointerup({ ...base, clientX: 20, clientY: 85 });
  if (outcome === 'outside') docEvents.pointerup({ ...base, clientX: 300, clientY: 85 });
  if (outcome === 'escape') docEvents.keydown({ key: 'Escape', preventDefault() {} });
  if (outcome === 'cancel') docEvents.pointercancel(base);
  if (outcome === 'blur') windowEvents.blur();
  if (outcome === 'reset') docEvents.reviewreset();
  const order = vm.runInContext('draft.sections.map(s=>s.id).join()', context);
  assert.equal(order, outcome === 'drop' ? 's2,s1' : 's1,s2');
  assert.equal(body.children.length, 1, 'the moving row is cleaned up');
  assert.equal(root.capture, null, 'pointer capture is released');
}
for (const outcome of ['drop', 'outside', 'escape', 'cancel', 'blur', 'reset']) gesture(outcome);
