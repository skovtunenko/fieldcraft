const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const data = JSON.parse(html.match(/id="reviewData">([\s\S]*?)<\/script>/)[1]);
data.spec.sections.push({ id: 's3', title: 'Reserve', minutes: 'if time', questions: [] });
const js = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');

function setup() {
  let ctx, captured = null, renders = 0, saves = 0, frameId = 0;
  const frames = new Map(), scrolls = [], nodes = new Map();
  class Element {
    constructor(dataset = {}, parent = null) {
      this.dataset = dataset; this.parentElement = parent; this.children = []; this.style = {}; this.events = {}; this.attrs = {};
      const classes = new Set();
      this.classList = { add: c => classes.add(c), remove: c => classes.delete(c), contains: c => classes.has(c) };
    }
    addEventListener(name, fn, capture) { const all = this.events[name] ||= []; capture === true ? all.unshift(fn) : all.push(fn); }
    emit(name, props = {}) {
      const event = { detail: 1, preventDefault() { this.prevented = true; }, stopImmediatePropagation() { this.stopped = true; }, ...props };
      for (const fn of this.events[name] || []) { fn(event); if (event.stopped) break; }
      return event;
    }
    setAttribute(k, v) { this.attrs[k] = v; }
    append(...els) { for (const el of els) { el.parentElement = this; this.children.push(el); } }
    remove() { if (this.parentElement) this.parentElement.children.splice(this.parentElement.children.indexOf(this), 1); this.parentElement = null; }
    contains(el) { for (; el; el = el.parentElement) if (el === this) return true; return false; }
    closest(selector) {
      for (let el = this; el; el = el.parentElement) {
        if (selector === '[data-drag="section"]' && el.dataset.drag === 'section') return el;
        if (selector === '[data-section]' && el.dataset.section) return el;
      }
      return null;
    }
    querySelectorAll(selector) { return selector === '[data-section]' ? this.children : handles; }
    getBoundingClientRect() {
      const top = (this.top || 100) - ctx.window.scrollY, height = this.height || 106;
      return { left: 300, right: 1100, top, bottom: top + height, width: this.className === 'section-ghost' ? 370 : 800, height };
    }
    setPointerCapture(id) { captured = id; }
    hasPointerCapture(id) { return captured === id; }
    releasePointerCapture() { captured = null; this.emit('lostpointercapture'); }
    focus() { ctx.document.activeElement = this; }
    scrollIntoView() { this.scrolled = true; }
  }
  const root = new Element(), body = new Element(), doc = new Element(), win = new Element();
  root.height = 900;
  const rows = data.spec.sections.map((s, i) => { const row = new Element({ section: s.id }, root); row.top = [100, 440, 680][i]; row.height = [300, 200, 160][i]; return row; });
  root.children = rows;
  const handles = rows.map(row => new Element({ drag: 'section', id: row.dataset.section }, row));
  const icons = handles.map(h => new Element({}, h));
  const header = { getBoundingClientRect: () => ({ bottom: 80 }) };
  const node = id => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
  node('reviewData').textContent = JSON.stringify(data);
  Object.assign(doc, { body, getElementById: node, querySelector: () => header, createElement: () => new Element(),
    elementFromPoint: (x, y) => {
      if (x < 300 || x > 1100 || y < 100 || y > 900) return null;
      return rows.find(row => { const r = row.getBoundingClientRect(); return y >= r.top && y <= r.bottom; }) || root;
    } });
  Object.assign(win, { innerWidth: 1200, innerHeight: 900, scrollY: 0,
    scrollBy: (_, dy) => { scrolls.push(dy); win.scrollY = Math.max(0, win.scrollY + dy); },
    scrollTo: (_, y) => { win.scrollY = y; } });
  ctx = { document: doc, window: win, requestAnimationFrame: fn => { frames.set(++frameId, fn); return frameId; }, cancelAnimationFrame: id => frames.delete(id),
    save: () => { saves++; }, draw: () => { renders++; } };
  vm.createContext(ctx); vm.runInContext(js, ctx);
  const run = code => vm.runInContext(code, ctx);
  run('persist=()=>{saved=JSON.stringify(collect());save();};render=()=>draw();comments.section.s1="Keep my note";comments.question.q1="Keep question note";timing.section.s1=15;excludedSections.add("s3");collapsed.add("s1");');
  ctx.bindMainSectionDrag(root);
  const base = { pointerId: 1, isPrimary: true, button: 0, pointerType: 'mouse' };
  const down = (index = 0, props = {}) => root.emit('pointerdown', { ...base, target: icons[index], clientX: 320, clientY: rows[index].top + 20, ...props });
  const move = (y, props = {}) => doc.emit('pointermove', { ...base, clientX: 320, clientY: y, ...props });
  const up = (y, props = {}) => doc.emit('pointerup', { ...base, clientX: 320, clientY: y, ...props });
  const order = () => run('draft.sections.map(s=>s.id).join()');
  const flush = time => { const [id, fn] = frames.entries().next().value; frames.delete(id); fn(time); };
  const clean = () => {
    assert.equal(body.children.length, 0, 'drag overlays leaked');
    assert.equal(frames.size, 0, 'autoscroll frame leaked');
    assert.equal(captured, null, 'pointer capture leaked');
    assert.equal(body.classList.contains('section-dragging'), false);
    assert(rows.every(row => !row.classList.contains('section-drag-source')));
    assert.equal(run('comments.section.s1'), 'Keep my note');
    assert.equal(run('comments.question.q1'), 'Keep question note');
    assert.equal(run('timing.section.s1'), 15);
    assert.equal(run('excludedSections.has("s3")'), true);
    assert.equal(run('collapsed.has("s1")'), true, 'drag changed fold state');
  };
  return { root, body, doc, win, rows, icons, handles, frames, scrolls, down, move, up, run, order, flush, clean,
    saves: () => saves, renders: () => renders, captured: () => captured, status: () => node('status').textContent };
}

for (const [index, y, expected] of [[0, 650, 's2,s1,s3'], [2, 120, 's3,s1,s2'], [0, 850, 's2,s3,s1']]) {
  const t = setup(), content = t.run('JSON.stringify(draft.sections.slice().sort((a,b)=>a.id.localeCompare(b.id)))');
  t.down(index); t.move(y);
  assert.equal(t.body.children.length, 2, 'ghost and insertion line missing');
  assert.equal(t.body.children[1].hidden, false);
  t.up(y, { pointerId: 2 }); assert.equal(t.captured(), 1, 'foreign pointer finished a drag');
  t.up(y);
  assert.equal(t.order(), expected);
  assert.equal(t.saves(), 1); assert.equal(t.renders(), 1);
  assert.equal(t.run('JSON.stringify(draft.sections.slice().sort((a,b)=>a.id.localeCompare(b.id)))'), content, 'section or question content changed');
  assert.equal(t.run('JSON.parse(saved).layout.map(s=>s.id).join()'), expected, 'stored and exported order differs');
  assert.match(t.status(), /moved to position/);
  assert.equal(t.run('draft.sections.flatMap(s=>s.questions).length'), data.spec.sections.flatMap(s => s.questions).length);
  let clicks = 0; t.root.addEventListener('click', () => { clicks++; });
  t.root.emit('click'); assert.equal(clicks, 0, 'release generated an extra click');
  t.root.emit('click', { detail: 0 }); assert.equal(clicks, 1, 'keyboard click was swallowed');
  t.clean();
}
for (const cancel of ['escape', 'outside', 'cancel', 'lostcapture', 'blur', 'hidden', 'reset']) {
  const t = setup(); t.down(); t.move(650);
  if (cancel === 'escape') t.doc.emit('keydown', { key: 'Escape' });
  if (cancel === 'outside') t.up(650, { clientX: 100 });
  if (cancel === 'cancel') t.doc.emit('pointercancel', { pointerId: 1 });
  if (cancel === 'lostcapture') { t.root.releasePointerCapture(); }
  if (cancel === 'blur') t.win.emit('blur');
  if (cancel === 'hidden') { t.doc.hidden = true; t.doc.emit('visibilitychange'); }
  if (cancel === 'reset') t.doc.emit('reviewreset');
  assert.equal(t.order(), 's1,s2,s3', cancel + ' committed a move');
  assert.equal(t.saves(), 0); assert.equal(t.renders(), 0); t.clean();
}
{
  const t = setup();
  t.down(0, { button: 2 }); t.move(650); assert.equal(t.captured(), null);
  t.down(0, { isPrimary: false }); t.move(650); assert.equal(t.captured(), null);
  t.down(0, { target: t.rows[0] }); t.move(650); assert.equal(t.captured(), null, 'header text became a drag handle');
  t.down(); assert.equal(t.doc.activeElement, t.handles[0], 'pointer press did not focus the keyboard handle');
  t.move(123); assert.equal(t.frames.size, 0, 'tiny movement started a drag'); t.up(123); t.clean();
  t.down(); t.move(150); t.up(150); assert.equal(t.saves(), 0, 'no-op drop created a review request'); t.clean();
}
{
  const t = setup(); t.down(); t.move(880); t.flush(16); const first = t.win.scrollY;
  t.flush(32); assert(t.win.scrollY > first, 'stationary pointer did not keep scrolling');
  t.move(880, { clientX: 100 }); t.flush(48); const paused = t.win.scrollY;
  t.flush(64); assert.equal(t.win.scrollY, paused, 'pointer outside the column kept scrolling');
  assert.equal(t.body.children[1].hidden, true, 'invalid target still showed a drop line');
  t.doc.emit('keydown', { key: 'Escape' }); assert.equal(t.win.scrollY, 0, 'cancel did not restore scroll position'); t.clean();
}
{
  const t = setup(); t.down(0, { pointerType: 'touch' }); t.move(650); t.up(650); assert.equal(t.order(), 's2,s1,s3'); t.clean();
}
{
  const t = setup(); t.run('draft.sections[0].title="<img src=x onerror=alert(1)>"'); t.down(); t.move(650);
  assert.match(t.body.children[0].innerHTML, /&lt;img/); assert.doesNotMatch(t.body.children[0].innerHTML, /<img/);
  t.doc.emit('pointercancel', { pointerId: 1 }); t.clean();
}
{
  const t = setup();
  t.root.emit('keydown', { target: t.icons[0], key: 'ArrowUp' }); assert.equal(t.saves(), 0);
  t.root.emit('keydown', { target: t.icons[0], key: 'ArrowDown' }); assert.equal(t.order(), 's2,s1,s3');
  assert.equal(t.doc.activeElement, t.handles[0]);
  t.root.emit('keydown', { target: t.icons[0], key: 'ArrowUp' }); assert.equal(t.order(), 's1,s2,s3'); t.clean();
}
console.log('Main section drag: order, data preservation, threshold, touch, cancellations, capture, continuous autoscroll, keyboard, escaping, and cleanup pass');
