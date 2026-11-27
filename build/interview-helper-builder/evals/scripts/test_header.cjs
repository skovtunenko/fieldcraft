const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const styles = new Map(), events = {};
let height = 91.25, onSize;
const header = { getBoundingClientRect: () => ({ height }) };
const ctx = {
  window: { innerWidth: 1583, addEventListener: (name, fn) => { events[name] = fn; } },
  document: {
    addEventListener() {},
    querySelector: selector => { if (selector === '#prepPeek') return { open: false };assert.equal(selector, '.topbar');return header; },
    documentElement: { style: { setProperty: (key, value) => styles.set(key, value) } },
  },
  ResizeObserver: class {
    constructor(fn) { onSize = fn; }
    observe(element) { assert.equal(element, header); }
  },
};
vm.createContext(ctx);vm.runInContext(script, ctx);
ctx.bindHeaderSize();
assert.equal(styles.get('--header-height'), '92px', 'initial header height not measured');
height = 127.5;onSize();
assert.equal(styles.get('--header-height'), '128px', 'content change did not update the offset');
ctx.window.innerWidth = 773;height = 174;events.resize();
assert.equal(styles.get('--header-height'), '174px', 'tablet resize retained desktop offset');
ctx.window.innerWidth = 720;events.resize();
assert.equal(styles.get('--header-height'), '0px', 'static mobile header still reserves sticky space');
ctx.window.innerWidth = 390;onSize();
assert.equal(styles.get('--header-height'), '0px');
delete ctx.ResizeObserver;
ctx.window.innerWidth = 1360;height = 110;ctx.bindHeaderSize();
assert.equal(styles.get('--header-height'), '110px', 'resize fallback failed without observer');
assert.match(script, /renderTimer\(\);bindHeaderSize\(\)/, 'header measurement not bound during init');
// Sidebar links scroll in-page, so they still work where fragment navigation is blocked (data:/srcdoc previews).
const scrolled = [], hashes = [];
const section = { scrollIntoView: opts => scrolled.push(opts) };
ctx.document.getElementById = id => (id === 'section-3' ? section : null);
ctx.history = { replaceState: (_, __, hash) => { hashes.push(hash); throw new Error('blocked'); } };
const click = href => {
  let prevented = false;
  const link = href && { getAttribute: () => href, classList: { contains: () => false } };
  ctx.navTo({ target: { closest: () => link }, preventDefault: () => { prevented = true; } });
  return prevented;
};
assert.equal(click('#section-3'), true, 'nav click left fragment navigation to the browser');
assert.equal(JSON.stringify(scrolled), '[{"block":"start"}]', 'nav click did not scroll to its section');
assert.deepEqual(hashes, ['#section-3'], 'nav click did not try to record the hash');
assert.equal(click('#missing'), false, 'unknown target was swallowed');
assert.equal(click(null), false, 'click outside a link was swallowed');
assert.match(script, /\$\('#navList'\)\.addEventListener\('click',navTo\)/, 'nav handler not bound');
console.log('Header offsets: initial size, content changes, tablet/mobile resizing, and observer fallback pass');
console.log('Sidebar navigation: in-page scroll, blocked history, and ignored clicks pass');

// Exercise the real section/final handlers; model bubbling so chevrons cannot toggle twice.
const nodes = new Map();
const node = selector => {
  if (!nodes.has(selector)) {
    const attrs = {}, classes = new Set(), listeners = {};
    nodes.set(selector, {
      value: '', style: {}, attrs, listeners,
      classList: { contains: c => classes.has(c), add: c => classes.add(c), remove: c => classes.delete(c), toggle: (c, on) => on ? classes.add(c) : classes.delete(c) },
      focus() {}, scrollIntoView() {},
      setAttribute: (k, v) => { attrs[k] = String(v); },
      querySelector: s => node(selector + ' ' + s), querySelectorAll: s => s === '.done-collapse' ? [node(selector + ' ' + s)] : [],
      addEventListener: (name, fn) => { listeners[name] = fn; },
      click() { listeners.click?.({ target: this }); ctx.onSectionHeaderClick({ target: this }); },
      closest: s => s.split(',').includes('button') ? nodes.get(selector) : null,
    });
  }
  return nodes.get(selector);
};
ctx.document.querySelector = node;
ctx.document.querySelectorAll = () => [];
ctx.CSS = { escape: s => s };
ctx.setTimeout = () => {};
ctx.clearTimeout = () => {};
let saved, saves = 0;
ctx.localStorage = { setItem: (_, value) => { saved = value; saves++; }, getItem: () => saved };
const realUpdateProgress = ctx.updateProgress;
const realLoadState = ctx.loadState;
vm.runInContext(`
updateProgress = renderSaveStatus = scheduleAutosave = () => {};
storageAvailable = true;
`, ctx);
ctx.bindInterview();
ctx.bindFinal();
const sections = vm.runInContext('CONFIG.sections', ctx);
assert.ok(sections.length >= 2, 'fixture needs independent sections');
const targets = sections.map(s => ({
  header: node('#section-' + s.id + ' .section-header'),
  button: node('#section-' + s.id + ' .section-toggle'),
  folded: () => vm.runInContext(`sState(${JSON.stringify(s.id)}).collapsed`, ctx),
}));
const questions = sections.flatMap(s => s.questions);
assert.ok(questions.length >= 2, 'fixture needs independent questions');
const questionTargets = questions.map(q => ({
  header: node('#' + q.id + ' .question-header'), button: node('#' + q.id + ' .q-toggle'),
  folded: () => vm.runInContext(`qState(${JSON.stringify(q.id)}).collapsed`, ctx),
}));
targets.push(...questionTargets);
targets.push({
  header: node('#final-section .section-header'), button: node('#finalToggle'),
  folded: () => vm.runInContext('state.finalCollapsed', ctx),
});
// Init owns the background handler; retain it without booting unrelated UI features.
const prepHandler = script.match(/\$\('#prepToggle'\)\.addEventListener\('click',([\s\S]*?)\);window\.addEventListener/)[1];
node('#prepToggle').addEventListener('click', vm.runInContext('(' + prepHandler + ')', ctx));
ctx.applyPrep();
targets.push({
  header: node('#prep > .prep-head'), button: node('#prepToggle'),
  folded: () => vm.runInContext('!!state.prepCollapsed', ctx),
});
const interactive = 'a,button,input,textarea,select,label';
const headers = '.section-header,.question-header,#prep > .prep-head';
const clickHeader = (t, tag = 'h2', nested = false) => {
  const control = { tag, parent: null };
  const target = nested ? { tag: 'span', parent: control } : control;
  target.closest = selector => {
    if (selector === interactive) {
      for (let n = target; n; n = n.parent) if (selector.split(',').includes(n.tag)) return n;
      return null;
    }
    assert.equal(selector, headers);
    return t?.header || null;
  };
  ctx.onSectionHeaderClick({ target });
};
for (const t of targets) {
  t.header.querySelector = s => { assert.equal(s, '.chev'); return t.button; };
  for (const nested of [false, true]) {
    for (const tag of ['div', 'h2', 'span']) {
      for (const expected of [true, false]) {
        const before = saves;
        clickHeader(t, tag, nested);
        assert.equal(t.folded(), expected, 'header did not toggle in both directions');
        assert.equal(t.button.attrs['aria-expanded'], String(!expected));
        assert.equal(saves, before + 1, 'header must save exactly once');
        ctx.loadState();
        assert.equal(t.folded(), expected, 'fold state did not survive persistence');
      }
    }
    for (const expected of [true, false]) {
      const before = saves;
      if (nested) {
        const icon = { closest: selector => selector === interactive ? t.button : t.header };
        t.button.listeners.click({ target: icon });
        ctx.onSectionHeaderClick({ target: icon });
      } else t.button.click();
      assert.equal(t.folded(), expected, 'chevron did not toggle exactly once');
      assert.equal(saves, before + 1);
      for (const tag of interactive.split(',')) {
        clickHeader(t, tag, nested);
        assert.equal(t.folded(), expected, tag + ' toggled the section');
        assert.equal(saves, before + 1, tag + ' saved state');
      }
    }
  }
}
clickHeader(targets[0]);
assert.equal(targets[0].folded(), true);
assert.equal(targets[1].folded(), false, 'sections no longer expand independently');
const before = saves;
clickHeader(null); // Includes card bodies and the background modal header.
assert.equal(saves, before, 'click outside a section header toggled a section');
assert.match(script, /document\.addEventListener\('click',onSectionHeaderClick\)/, 'header interaction not bound');
assert.match(html, /<button type="button" class="chev section-toggle"/, 'native keyboard toggle lost');
console.log('Section headers: both directions, independent state, aria-expanded, persistence, control exclusions, and single chevron toggles pass (DOM stubs)');

// A nested header only changes that question; Done and completion remain independent.
const questionId = JSON.stringify(questions[0].id);
clickHeader(targets[0]); // Open the parent before interacting with its nested card.
clickHeader(questionTargets[0]);
assert.equal(questionTargets[0].folded(), true);
assert.equal(questionTargets[1].folded(), false, 'question headers toggled a sibling');
assert.equal(targets[1].folded(), false, 'question header toggled another section');
assert.equal(targets[0].folded(), false, 'question header toggled its parent section');
assert.equal(vm.runInContext(`qState(${questionId}).completed`, ctx), false);
clickHeader(questionTargets[0]);
const done = node('#' + questions[0].id + ' .done-collapse');
const beforeNoVerdict = saves;
done.click();
assert.equal(vm.runInContext(`qState(${questionId}).completed`, ctx), false, 'Done bypassed the verdict requirement');
assert.equal(questionTargets[0].folded(), false, 'Done without a verdict folded the question');
assert.equal(saves, beforeNoVerdict, 'Done without a verdict triggered the header toggle');
vm.runInContext(`qState(${questionId}).rating = 'neutral'`, ctx);
const beforeDone = saves;
done.click();
assert.equal(vm.runInContext(`qState(${questionId}).completed`, ctx), true);
assert.equal(questionTargets[0].folded(), true);
assert.equal(saves, beforeDone + 1, 'Done triggered an additional header toggle');
clickHeader(questionTargets[0]);
assert.equal(questionTargets[0].folded(), false);
assert.equal(vm.runInContext(`qState(${questionId}).completed`, ctx), true, 'header changed completion');
done.click();
assert.equal(vm.runInContext(`qState(${questionId}).completed`, ctx), false);
assert.equal(questionTargets[0].folded(), false, 'Undo lost its expand action');
console.log('Nested question headers: independent fold state and preserved Done/Undo actions pass');

// Skip shares the real persistence, navigation, and prompt paths with Done.
ctx.updateProgress = realUpdateProgress;
const qid = questions[0].id, qid2 = questions[1].id;
const readQ = () => JSON.parse(vm.runInContext(`JSON.stringify(qState(${questionId}))`, ctx));
const skip = node('#' + qid + ' .skip-question');
vm.runInContext(`state.questions = {}; stampNow = () => { throw new Error('Skip started the timer'); };`, ctx);
const beforeSkip = saves;
skip.click();
assert.equal(saves, beforeSkip + 1, 'Skip also toggled the header');
assert.equal(readQ().skipped, true);
assert.equal(readQ().completed, false);
assert.equal(readQ().collapsed, true);
assert.equal(readQ().rating, '');
assert.equal(skip.attrs['aria-pressed'], 'true');
assert.equal(done.hidden, true, 'Skipped still offers Done');
const skippedBeforeForcedDone = JSON.stringify(readQ());
done.click();
assert.equal(JSON.stringify(readQ()), skippedBeforeForcedDone, 'hidden Done changed a skipped question');
assert.equal(questionTargets[0].button.attrs['aria-expanded'], 'false');
assert.equal(node('#' + qid).classList.contains('skipped'), true);
assert.equal(readQ().times.rating, undefined);
assert.equal(node('#progressCount').textContent, `0/${questions.length - 1} completed · 1 skipped`);
const nav = node(`.nav-link[data-nav="${sections[0].id}"]`);
assert.equal(nav.classList.contains('nav-skipped'), true);
assert.equal(nav.classList.contains('nav-done'), false);
ctx.loadState();
assert.equal(readQ().skipped, true, 'Skip lost on LocalStorage restore');
ctx.generatePrompt();
let prompt = node('#promptOutput').value;
assert.ok(!prompt.includes(questions[0].title), 'a skipped question without marks reached the prompt');
assert.ok(!prompt.includes('not failed by the candidate'), 'skip instruction without a skipped question in the prompt');
assert.ok(!prompt.includes(questions[1].title), 'untouched question leaked into prompt');
vm.runInContext(`qState(${questionId}).notes = 'asked half of it'`, ctx);
ctx.generatePrompt();prompt = node('#promptOutput').value;
assert.ok(prompt.includes('<status>skipped by interviewer; not assessed by this question</status>'));
assert.ok(!prompt.includes('<status>asked/completed</status>'));
assert.ok(!prompt.includes('<interviewer_rating>'));
assert.ok(prompt.includes('not failed by the candidate'));
vm.runInContext(`qState(${questionId}).notes = ''`, ctx);
skip.click();
assert.equal(readQ().skipped, false);
assert.equal(readQ().collapsed, false);
assert.equal(skip.attrs['aria-pressed'], 'false');

// Partial evidence survives Skip and Undo; Done and Skip remain mutually exclusive.
vm.runInContext(`Object.assign(qState(${questionId}), {
  completed:true, rating:'neutral', notes:'Partial note <kept>',
  signals:{'positive:sample':'~'}, reasons:{'positive:sample':['needed hints']},
  times:{rating:{at:123456,el:1000},'positive:sample':{at:123457,el:1001}}
});`, ctx);
const evidence = q => JSON.stringify([q.rating, q.notes, q.signals, q.reasons, q.times]);
const beforeEvidence = evidence(readQ());
ctx.applyQ(node('#' + qid), questions[0]);
assert.equal(skip.hidden, true, 'Completed still offers Skip');
const completedBeforeForcedSkip = JSON.stringify(readQ());
skip.click();
assert.equal(JSON.stringify(readQ()), completedBeforeForcedSkip, 'hidden Skip changed a completed question');
done.click(); // Explicit Undo is required before Skip.
assert.equal(skip.hidden, false);
skip.click();
assert.equal(readQ().completed, false);
assert.equal(readQ().skipped, true);
assert.equal(evidence(readQ()), beforeEvidence);
ctx.generatePrompt();
prompt = node('#promptOutput').value;
assert.ok(prompt.includes('<note>Partial note &lt;kept></note>'));
assert.ok(prompt.includes('<interviewer_rating>Neutral / factual'));
skip.click();
assert.equal(evidence(readQ()), beforeEvidence);
assert.equal(readQ().completed, false, 'Undo skip invented completion');
skip.click();
const markedSkipBeforeDone = JSON.stringify(readQ());
done.click();
assert.equal(JSON.stringify(readQ()), markedSkipBeforeDone, 'a retained verdict bypassed Undo skip');
skip.click();done.click();
assert.equal(readQ().completed, true);
assert.equal(readQ().skipped, false);
assert.equal(readQ().collapsed, true);
assert.equal(nav.classList.contains('nav-done'), true);
assert.equal(skip.hidden, true);
assert.equal(done.hidden, false);
ctx.loadState();ctx.applyQ(node('#' + qid), questions[0]);
assert.equal(skip.hidden, true, 'completed action visibility lost on reload');

// A section containing one done question and one skipped question is resolved, not all done.
const mixed = { ...sections[0], questions: [questions[0], questions[1]] };
vm.runInContext(`qState(${JSON.stringify(qid2)}).skipped=true`, ctx);
ctx.applyS(node('#section-' + mixed.id), mixed);
assert.equal(nav.classList.contains('nav-resolved'), true);
assert.equal(nav.classList.contains('nav-done'), false);
assert.equal(nav.classList.contains('nav-progress'), false);
vm.runInContext('CONFIG.sections.flatMap(s=>s.questions).forEach(q=>Object.assign(qState(q.id),{completed:false,skipped:true,collapsed:true}))', ctx);
ctx.updateProgress();
assert.equal(node('#progressCount').textContent, `0/0 completed · ${questions.length} skipped`);
assert.equal(node('#progressPct').textContent, '0%');

// The HTML backup embeds Skip and boots from it without LocalStorage; local state wins.
const embedded = node('#embeddedState');
const cloneNodes = new Map();
ctx.document.documentElement.cloneNode = () => ({
  querySelector(s) { if (!cloneNodes.has(s)) cloneNodes.set(s, { innerHTML: '', textContent: '' }); return cloneNodes.get(s); },
  get outerHTML() { return `<script type="application/json" id="embeddedState">${cloneNodes.get('#embeddedState').textContent}</script>`; },
});
const backup = ctx.buildSavedHtml();
embedded.textContent = backup.match(/id="embeddedState">(.*?)<\/script>/s)[1];
saved = undefined;
vm.runInContext('state.questions={};storageAvailable=false', ctx);
ctx.loadState();ctx.migrate();ctx.applyQ(node('#' + qid), questions[0]);
assert.equal(readQ().skipped, true);
assert.equal(readQ().collapsed, true);
assert.equal(done.hidden, true, 'backup restored a skipped question with Done visible');
saved = JSON.stringify({ questions: { [qid]: { completed: false, collapsed: false, signals: {} } } });
vm.runInContext('storageAvailable=true', ctx);
ctx.loadState();ctx.migrate();ctx.applyQ(node('#' + qid), questions[0]);
assert.equal(!!readQ().skipped, false, 'older LocalStorage did not override the backup');
assert.equal(skip.attrs['aria-pressed'], 'false');

// Run init to bind the actual bulk-action handlers; keep unrelated layout rendering stubbed.
ctx.localStorage.removeItem = () => {};
for (const fn of ['checkStorage', 'loadState', 'renderStatic', 'renderSections', 'renderScores', 'renderTimer', 'bindHeaderSize', 'renderFlags']) ctx[fn] = () => {};
ctx.init();
skip.click();
const other = node('#' + qid2 + ' .q-toggle');
other.click();
node('#expandAllSections').click();node('#expandAllSections').click();
assert.equal(readQ().collapsed, true, 'topbar Expand all opened a skipped question');
questionTargets[0].button.click();
assert.equal(readQ().collapsed, false, 'individual chevron cannot open skipped question');
assert.equal(readQ().skipped, true);
skip.click();
assert.equal(readQ().collapsed, false);
assert.equal(readQ().skipped, false);
console.log('Skip: verdict-free toggle, evidence preservation, Done, progress, navigation, LocalStorage, HTML backup, legacy state, prompt, and bulk controls pass (DOM stubs)');

// Section Skip snapshots only eligible questions; group Undo retains subsequent evidence and decisions.
vm.runInContext(`
const old = CONFIG.sections;
CONFIG.sections = [{...old[0],id:'group',questions:[...old.flatMap(s=>s.questions),{...old[0].questions[0],id:'q4',index:'1.4'}]},
 {...old[1],id:'other',questions:[{...old[0].questions[0],id:'q5',index:'2.1'},{...old[0].questions[0],id:'q6',index:'2.2'}]}];
state.questions={};state.sections={};
`, ctx);
const group = vm.runInContext('CONFIG.sections[0]', ctx);
const groupSkip = node('#section-group .skip-section');
const getState = expression => JSON.parse(vm.runInContext(`JSON.stringify(${expression})`, ctx));
const resetGroup = collapsed => {
  vm.runInContext(`state.sections={group:{collapsed:${collapsed},notes:'Section note'}};state.questions={};
  Object.assign(qState('q1'),{completed:true,collapsed:true,rating:'adequate',notes:'Done evidence'});
  Object.assign(qState('q2'),{skipped:true,collapsed:false,notes:'Prior skip'});
  Object.assign(qState('q3'),{collapsed:false,rating:'concern',notes:'Partial evidence',signals:{sample:'~'},reasons:{sample:['needed hints']},times:{sample:{at:123456,el:1000}}});
  qState('q4').collapsed=true;`, ctx);
  ctx.bindInterview();
};
for (const collapsed of [false, true]) {
  resetGroup(collapsed);
  const prior = getState('state'), beforeSaves = saves;
  groupSkip.click();
  assert.equal(saves, beforeSaves + 1, 'section Skip toggled its header again');
  assert.deepEqual(getState('qState("q1")'), prior.questions.q1, 'completed question changed');
  assert.deepEqual(getState('qState("q2")'), prior.questions.q2, 'previous individual skip changed');
  assert.equal(getState('qState("q3").skipped'), true);
  assert.equal(getState('qState("q4").skipped'), true);
  assert.equal(getState('sState("group").collapsed'), true);
  assert.equal(groupSkip.attrs['aria-pressed'], 'true');
  assert.equal(groupSkip.disabled, false);
  assert.equal(node('#section-group .skip-section .section-skip-count').hidden, true);
  assert.equal(node('#section-group .section-skipped-count').textContent, '3 skipped');
  const snapshot = getState('sState("group").skipUndo');
  assert.deepEqual(Object.keys(snapshot.questions), ['q3', 'q4']);
  vm.runInContext('state.questions={};state.sections={}', ctx);realLoadState();ctx.bindInterview();
  assert.deepEqual(getState('sState("group").skipUndo'), snapshot, 'group Undo lost on reload');
  node('#expandAllSections').click();
  assert.equal(getState('sState("group").collapsed'), true, 'bulk expansion reopened skipped section');
  assert.deepEqual(getState('qState("q1")'), prior.questions.q1, 'bulk expansion changed a completed question inside the skipped section');
  vm.runInContext('qState("q3").notes="Added after skipping"', ctx);
  groupSkip.click();
  assert.equal(getState('sState("group").collapsed'), collapsed);
  assert.equal(getState('qState("q3").skipped'), false);
  assert.equal(getState('qState("q3").collapsed'), false);
  assert.equal(getState('qState("q4").collapsed'), true);
  assert.equal(getState('qState("q3").notes'), 'Added after skipping');
  assert.deepEqual(getState('qState("q3").times'), prior.questions.q3.times);
  assert.deepEqual(getState('qState("q3").reasons'), prior.questions.q3.reasons);
  assert.equal(getState('sState("group").notes'), 'Section note');
}
resetGroup(false);groupSkip.click();
const groupBackup = ctx.buildSavedHtml();
embedded.textContent = groupBackup.match(/id="embeddedState">(.*?)<\/script>/s)[1];
vm.runInContext('storageAvailable=false;state.questions={};state.sections={}', ctx);
realLoadState();ctx.bindInterview();
assert.deepEqual(Object.keys(getState('sState("group").skipUndo.questions')), ['q3', 'q4']);
node('#q3 .skip-question').click(); // Resume before completing a group-skipped question.
node('#q3 .done-collapse').click();
assert.equal(getState('qState("q3").completed'), true);
assert.deepEqual(Object.keys(getState('sState("group").skipUndo.questions')), ['q4']);
groupSkip.click();
assert.equal(getState('qState("q3").completed'), true, 'Undo overwrote a later Done');
assert.equal(getState('qState("q3").skipped'), false);
assert.equal(getState('qState("q4").skipped'), false);
resetGroup(false);groupSkip.click();node('#q3 .skip-question').click();
groupSkip.click();
assert.equal(getState('qState("q3").skipped'), false, 'Undo overwrote an individual resume');
assert.equal(getState('qState("q3").collapsed'), false);
vm.runInContext('CONFIG.sections[0].questions.forEach(q=>qState(q.id).completed=true)', ctx);
ctx.applyS(node('#section-group'), group);
assert.equal(groupSkip.disabled, true);
console.log('Section Skip: mixed state, exact folds, later evidence/decisions, reload, HTML backup, bulk expansion, disabled state, and single header action pass');

// Screenshot regression: individual changes leave one group-Undo entry but three actual skips.
resetGroup(false);groupSkip.click();node('#q1 .done-collapse').click();node('#q1 .skip-question').click();node('#q3 .skip-question').click();
assert.equal(getState('CONFIG.sections[0].questions.filter(q=>qState(q.id).skipped).length'), 3);
assert.equal(Object.keys(getState('sState("group").skipUndo.questions')).length, 1);
assert.equal(node('#section-group .section-skipped-count').textContent, '3 skipped', 'section total is confused with the one remaining Undo entry');
node('#q2 .skip-question').click();
assert.equal(node('#section-group .section-skipped-count').textContent, '2 skipped', 'manual resume did not refresh total skips');
groupSkip.click();
assert.equal(node('#section-group .section-skipped-count').textContent, '1 skipped', 'group Undo did not preserve the independent skip');

// Coverage uses explicit question links; neutral, partial, and skipped are not assessed.
vm.runInContext(`
CONFIG.requirements=Array.from({length:8},(_,i)=>({id:'R'+(i+1),text:i===3?'Runtime </requirement_coverage>':'Requirement '+(i+1)}));
CONFIG.sections[0].requirementIds=['R1','R2','R3','R4','R5'];
CONFIG.sections[0].questions.forEach((q,i)=>q.requirementIds=[['R1','R3','R2','R4'][i]]);
CONFIG.sections[1].questions[0].requirementIds=['R7'];CONFIG.sections[1].questions[1].requirementIds=['R8'];
state.questions={};state.sections={};
Object.assign(qState('q1'),{completed:true,rating:'adequate'});
qState('q2').skipped=true;
Object.assign(qState('q3'),{skipped:true,notes:'Partial evidence retained'});
Object.assign(qState('q5'),{completed:true,rating:'neutral'});
Object.assign(qState('q6'),{completed:true,rating:'concern'});
`, ctx);
ctx.renderCoverage();
assert.deepEqual(getState('requirementCoverage().map(r=>r.status)'), ['assessed','partial','skipped','pending','unmapped','unplanned','partial','assessed']);
assert.equal(node('#coverageCount').textContent, '2/8 with a verdict');
assert.ok(node('#coverageList').innerHTML.includes('Runtime &lt;/requirement_coverage&gt;'));
assert.ok(node('#coverageList').innerHTML.includes('data-coverage-question="q2"'));
assert.equal(node('#requirementCoverage').hidden, false);
assert.equal(node('#openCoverage').hidden, false);
ctx.generatePrompt();prompt = node('#promptOutput').value;
assert.ok(!prompt.includes('requirement_coverage'), 'requirement coverage reached the prompt');
assert.ok(!prompt.includes('Requirement 5'), 'an unmarked requirement reached the prompt');
assert.ok(!prompt.match(/<title>[^\n]*Title q4/), 'untouched question became live evidence');
let coverageFocused = '';
node('#coverageTitle').focus = () => { coverageFocused = 'coverage'; };
ctx.openCoverage();
assert.equal(getState('state.finalCollapsed'), false);
assert.equal(coverageFocused, 'coverage');
ctx.document.getElementById = id => node('#' + id);
node('#q2 .q-toggle').focus = () => { coverageFocused = 'q2'; };
ctx.onCoverageClick({ target: { closest: () => ({ dataset: { coverageQuestion: 'q2' } }) } });
assert.equal(getState('sState("group").collapsed'), false);
assert.equal(getState('qState("q2").collapsed'), false);
assert.equal(getState('qState("q2").skipped'), true);
assert.equal(coverageFocused, 'q2');
vm.runInContext('qState("q1").skipped=true', ctx);ctx.renderCoverage();
assert.equal(getState('requirementCoverage()[0].status'), 'partial', 'retained rating was lost after skip');
vm.runInContext('delete CONFIG.requirements', ctx);ctx.renderCoverage();
assert.equal(node('#requirementCoverage').hidden, true);
assert.equal(node('#openCoverage').hidden, true);
vm.runInContext('CONFIG.sections[0].id=7;CONFIG.sections[0].questions[1].id=9;qState("9").skipped=true', ctx);
ctx.onCoverageClick({ target: { closest: () => ({ dataset: { coverageQuestion: '9' } }) } });
assert.equal(getState('qState("9").collapsed'), false, 'numeric legacy question ID did not open');
assert.equal(getState('qState("9").skipped'), true);
vm.runInContext('sState("7").collapsed=true', ctx);
ctx.onCoverageClick({ target: { closest: () => ({ dataset: { coverageSection: '7' } }) } });
assert.equal(getState('sState("7").collapsed'), false, 'numeric legacy section ID did not open');
console.log('Coverage: verdicts including negative, neutral/partial/skipped/pending/section-only/unplanned, escaping, prompt, navigation/focus, and legacy visibility pass');
