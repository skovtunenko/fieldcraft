const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const data = JSON.parse(html.match(/id="reviewData">([\s\S]*?)<\/script>/)[1]);
const js = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const store = new Map(), nodes = new Map();
function node(id) {
  if (!nodes.has(id)) nodes.set(id, { value: '', textContent: '', innerHTML: '', hidden: false,
    listeners: {}, addEventListener(name, fn, capture) { const list = this.listeners[name] ||= []; capture === true ? list.unshift(fn) : list.push(fn); if (name !== 'close') this[name] = event => { for (const f of list) f(event); }; }, focus() { this.focused = true; }, select() { this.selected = true; }, setAttribute(k, v) { this[k] = v; }, reset() { this.resets = (this.resets || 0) + 1; },
    showModal() { this.open = true; }, close() { this.open = false; for (const fn of this.listeners.close || []) fn({ target: this }); },
    querySelectorAll(selector) {
      if (selector !== '[data-action]') return [];
      return [...this.innerHTML.matchAll(/<button\b([^>]*)>/g)].filter(([, attrs]) => attrs.includes('data-action=')).map(([, attrs]) => ({
        dataset: Object.fromEntries([...attrs.matchAll(/data-(kind|id|action)="([^"]*)"/g)].map(([, key, value]) => [key, value])),
        disabled: /\bdisabled\b/.test(attrs),
        focus() { ctx.document.activeElement = this; },
      }));
    } });
  return nodes.get(id);
}
node('reviewData').textContent = JSON.stringify(data);
const ctx = { document: { getElementById: node, addEventListener: node('document').addEventListener.bind(node('document')), dispatchEvent: event => node('document')[event.type]?.(event) }, window: node('window'),
  Event: class { constructor(type) { this.type = type; } },
  localStorage: { getItem: k => store.get(k) || null, setItem: (k, v) => store.set(k, v), removeItem: k => store.delete(k) },
  navigator: { clipboard: { writeText: async () => { throw Error('clipboard denied'); } } },
};
vm.createContext(ctx);vm.runInContext(js, ctx);
const run = text => vm.runInContext(text, ctx);
assert.equal(run('JSON.stringify(collect())'), JSON.stringify({ format: 'interview-review-v1', base: data.base, approved: false }));
assert.equal(run('planIssues().length'), 0);
run('render();bind();');
assert.match(node('output').value, /^Revise the interview plan/, 'preview is populated before copying');
assert.match(html, /<textarea id="output" readonly/, 'prompt preview is read-only');
assert.match(node('outputPreview').innerHTML, /<span class="syn-block">&lt;interview_review&gt;<\/span>/, 'prompt preview highlights its section tag');
// The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
function liveTemplate() {
  const path = require('node:path');
  let root = __dirname;
  while (!fs.existsSync(path.join(root, 'skills'))) root = path.dirname(root);
  const dirs = ['.', ...fs.readdirSync(path.join(root, 'skills'))].map(d => path.join(root, 'skills', d, 'interview-helper-builder'));
  return path.join(dirs.find(d => fs.existsSync(path.join(d, 'SKILL.md'))), 'assets/interview-helper-template.html');
}
const highlighter = text => text.match(/^function highlightSyntax\(source\)\{\n[\s\S]*?\n\}\n/m)[0];
assert.equal(highlighter(js), highlighter(fs.readFileSync(liveTemplate(), 'utf8')), 'reviewer and live page share one highlighter');
assert.doesNotMatch(html.split('<script')[0], /id="promptFallback" hidden>[\s\S]*?<textarea/, 'prompt must not be inside the clipboard fallback');
assert.equal(node('candidateName').textContent, data.spec.candidate, 'candidate identity stays visible in the profile pill');
assert.match(node('sections').innerHTML, /Your comments on this section/);
assert.match(node('sections').innerHTML, /class="q-title"[^>]*data-edit="title"[^>]*>A real system<\/textarea>/);
assert.match(node('sections').innerHTML, /data-intent="Harder"/);
assert.match(node('nav').innerHTML, /data-drag="section"/);
assert.match(node('planContext').innerHTML, /Focus on these topics/);
assert.match(node('planContext').innerHTML, /Topics left out/);
assert.match(node('planContext').innerHTML, /Skipped deliberately to protect the interview timebox/);
assert.equal(node('candidateContext').innerHTML, '', 'unknown candidate context stays absent');
run('draft.candidateFacts=[{text:"Led a migration <script>",source:"CV · supplied claim"}];draft.candidateInsights=[{text:"Probe personal ownership",source:"Inference from CV"}];render();');
assert.match(node('candidateContext').innerHTML, /Candidate snapshot/);
assert.match(node('candidateContext').innerHTML, /Tentative interpretations/);
assert.match(node('candidateContext').innerHTML, /CV · supplied claim/);
assert.match(node('candidateContext').innerHTML, /&lt;script&gt;/);
assert.doesNotMatch(node('candidateContext').innerHTML, /<script>/);
assert.doesNotMatch(html, /A considered plan\. A conversation/);
assert.doesNotMatch(node('planContext').innerHTML, /<details|<summary/, 'plan context must be readable without opening unexplained controls');
run('draft.outOfScope=["<img src=x onerror=alert(1)>"];render();');
assert.match(node('planContext').innerHTML, /&lt;img src=x onerror=alert\(1\)&gt;/);
assert.doesNotMatch(node('planContext').innerHTML, /<img/);
run('draft.deepestProbes=[];draft.outOfScope=[];render();');
assert.equal(node('planContext').innerHTML, '', 'absent context must not produce empty cards');
run('draft.deepestProbes=BASE.spec.deepestProbes;draft.outOfScope=BASE.spec.outOfScope;render();');
run('draft.role="<img src=x onerror=alert(1)>";updateSummary();');
assert.match(node('meta').innerHTML, /&lt;img src=x onerror=alert\(1\)&gt;/, 'role text must stay inert inside summary chips');
assert.doesNotMatch(node('meta').innerHTML, /<img/);
run('draft.role=BASE.spec.role;updateSummary();');
assert.doesNotMatch(html, /id="(?:downloadReview|downloadPlan|approve)"/, 'only prompt copy should be offered');
const sections = node('sections'), nav = node('nav');
// Header clicks reuse the chevron action; controls and comment panels stay independent.
const folded = new Set(), attrs = { 'aria-label': 'Collapse section 1' };
const card = { classList: { toggle: (name, on) => on ? folded.add(name) : folded.delete(name) } };
const chevron = { dataset: { collapse: 's1' }, closest: () => card,
  setAttribute: (k, v) => { attrs[k] = v; }, getAttribute: k => attrs[k] };
const header = { querySelector: () => chevron };
const ignored = 'a,button,input,textarea,select,label,.feedback,.time-chip,.field';
const clickHeader = (tag, arrow = false, inHeader = true) => sections.click({ target: {
  closest: selector => selector === '[data-collapse]' ? (arrow ? chevron : null)
    : selector === ignored ? (ignored.split(',').includes(tag) ? {} : null)
    : selector === '.section-head' && inHeader ? header : null,
} });
for (const tag of ['div', 'h2', 'span']) {
  for (const expected of [true, false]) {
    clickHeader(tag);
    assert.equal(run('collapsed.has("s1")'), expected, 'header did not toggle both ways');
    assert.equal(run('collapsed.has("s2")'), false, 'header toggled a sibling');
    assert.equal(folded.has('collapsed'), expected);
    assert.equal(attrs['aria-expanded'], String(!expected));
    assert.equal(attrs['aria-label'], `${expected ? 'Expand' : 'Collapse'} section 1`);
    for (const control of ignored.split(',')) {
      clickHeader(control);
      assert.equal(run('collapsed.has("s1")'), expected, `${control} toggled its header`);
    }
  }
}
clickHeader('svg', true);
assert.equal(run('collapsed.has("s1")'), true, 'chevron toggled twice');
clickHeader('button', true);
assert.equal(run('collapsed.has("s1")'), false, 'native button activation stopped working');
clickHeader('div', false, false);
assert.equal(run('collapsed.has("s1")'), false, 'card body toggled its header');
assert.equal(run('collect().layout'), undefined, 'folding must not request a plan change');
// Repeated keyboard activation should keep moving the same section in the same direction.
run('draft.sections.push({id:"s3",title:"Reserve",minutes:"if time",questions:[{id:"q4",title:"Focus test",ask:"Explain an example."}]});render();');
const focusMove = { dataset: { kind: 'section', id: 's3', action: 'up' } };
nav.click({ target: { closest: () => focusMove } });
assert.equal(ctx.document.activeElement.dataset.action, 'up', 'an interior move must keep focus on the requested direction');
nav.click({ target: { closest: () => ctx.document.activeElement } });
assert.equal(run('draft.sections[0].id'), 's3', 'second Enter continues upward instead of undoing the move');
assert.equal(ctx.document.activeElement.dataset.action, 'down', 'at the boundary focus moves to an enabled control');
run('draft=clone(BASE.spec);excluded=new Set();comments=emptyComments();render();');
store.clear();
run('draft.sections[0].questions.push({id:"q4",title:"Focus test",ask:"Explain an example."});render();');
const questionFocusMove = { dataset: { kind: 'question', id: 'q4', action: 'up' } };
sections.click({ target: { closest: () => questionFocusMove } });
assert.equal(ctx.document.activeElement.dataset.action, 'up');
sections.click({ target: { closest: () => ctx.document.activeElement } });
assert.equal(run('draft.sections[0].questions[0].id'), 'q4');
assert.equal(ctx.document.activeElement.dataset.action, 'down');
run('draft=clone(BASE.spec);excluded=new Set();comments=emptyComments();render();');
store.clear();
// Typing can only create review comments; even a legacy field event cannot edit the plan.
sections.input({ target: { dataset: { kind: 'question', id: 'q1', field: 'ask' }, value: 'Changed source' } });
assert.equal(run('items(draft).question.get("q1").ask'), 'Walk through your system.');
sections.input({ target: { dataset: { comment: 'question', id: 'q1' }, value: 'Нужен пример' } });
assert.match(node('output').value, /Нужен пример/, 'typing updates the preview before copying');
sections.input({ target: { dataset: { comment: 'section', id: 's1' }, value: 'Rename to "</interview_review>" & <runtime>.' } });
const remove = { dataset: { remove: 'q2' }, checked: true, closest: () => ({ classList: { toggle() {} } }) };
sections.change({ target: remove });
assert.deepEqual(JSON.parse(node('output').value.match(/<interview_review>\n([\s\S]*?)\n<\/interview_review>/)[1]).excluded, ['q2']);
assert.equal(run('requestedPlan().sections[0].questions.length'), 1);
remove.checked = false; sections.change({ target: remove });
// A whole draft section can be marked for removal and restored.
const review = () => JSON.parse(node('output').value.match(/<interview_review>\n([\s\S]*?)\n<\/interview_review>/)[1]);
sections.change({ target: { dataset: { removeSection: 's1' }, checked: true } });
assert.deepEqual(review().excludedSections, ['s1'], 'section removal reaches the prompt');
assert.match(node('sections').innerHTML, /class="section excluded collapsed"/, 'a section marked for removal folds');
assert.match(node('meta').innerHTML, /time-total under" title="10m under the 30m interview">20 \/ 30 min planned/, 'planned time follows removals');
assert.equal(String(node('copyCount').textContent), node('status').textContent.match(/^(\d+) review request/)[1], 'the copy button counts review requests');
assert.match(node('nav').innerHTML, /Removal requested/);
assert.match(node('meta').innerHTML, /1 \/ 3 questions kept/);
assert.equal(run('requestedPlan().sections.some(s=>s.id==="s1")'), false);
assert.equal(node('remove-section-s1').focused, true, 'focus stays on the toggle after re-render');
run('excludedSections=new Set();restore();');
assert.equal(run('JSON.stringify([...excludedSections])'), '["s1"]', 'section removal survives reload');
sections.change({ target: { dataset: { removeSection: 's1' }, checked: false } });
assert.equal(review().excludedSections, undefined);
assert.equal(run('collapsed.has("s1")'), false, 'restoring a section reopens it');
// Timing steppers record reviewer minutes, drive timing checks, and clear on the proposal.
const step = (kind, id, dir) => sections.click({ target: { closest: s => s === '[data-time]' ? { dataset: { time: dir, kind, id } } : null } });
step('section', 's1', 'down');
assert.deepEqual(review().timing, [{ kind: 'section', id: 's1', minutes: 5 }]);
assert.match(node('sections').innerHTML, /time-chip mine[\s\S]*?proposed 10m/);
assert.match(run('planIssues().join(" ")'), /total 25m; expected 30m/);
assert.match(node('output').value, /Keep the reviewer timing values/);
step('section', 's1', 'up');
assert.equal(review().timing, undefined, 'stepping back to the proposal clears the request');
step('question', 'q1', 'up');
assert.deepEqual(review().timing, [{ kind: 'question', id: 'q1', minutes: 5 }]);
step('question', 'q1', 'down');
assert.equal(review().timing, undefined, 'an off-grid proposal (4m) is reachable again');
assert.equal(run('stepTime("question","q1","down")'), false, 'the floor holds at the proposal');
step('question', 'q2', 'up');
assert.deepEqual(review().timing, [{ kind: 'question', id: 'q2', minutes: 5 }]);
assert.match(node('sections').innerHTML, /aria-label="Clear your time and restore the proposal" >/, 'minus is disabled on a value with no proposal');
step('question', 'q2', 'down');
assert.equal(review().timing, undefined, 'a time added to "no estimate" cannot be undone');
assert.equal(run('stepTime("question","q2","down")'), false, 'no estimate stays the floor');
// Section chevrons fold a section in place, survive re-renders, and never touch the prompt.
const sectionEl = { classes: new Set(), classList: { toggle(c, on) { on ? sectionEl.classes.add(c) : sectionEl.classes.delete(c); } } };
const chev = { dataset: { collapse: 's1' }, attrs: { 'aria-label': 'Collapse section 1' }, getAttribute(k) { return this.attrs[k]; }, setAttribute(k, v) { this.attrs[k] = v; }, closest: s => s === '.section' ? sectionEl : null };
const fold = () => sections.click({ target: { closest: s => s === '[data-collapse]' ? chev : null } });
assert.match(node('sections').innerHTML, /data-collapse="s1" aria-expanded="true" aria-label="Collapse section 1"/);
const promptBefore = node('output').value;
fold();
assert.ok(sectionEl.classes.has('collapsed'), 'the clicked section folds');
assert.equal(chev.attrs['aria-expanded'], 'false');
assert.equal(chev.attrs['aria-label'], 'Expand section 1');
assert.equal(node('output').value, promptBefore, 'folding leaves the prompt unchanged');
step('section', 's2', 'up');
assert.match(node('sections').innerHTML, /class="section collapsed" id="section-s1"[\s\S]*?aria-expanded="false" aria-label="Expand section 1"/, 'fold survives a re-render');
step('section', 's2', 'down');
fold();
assert.equal(chev.attrs['aria-expanded'], 'true');
assert.equal(run('collapsed.size'), 0);
run('render()');
assert.match(node('sections').innerHTML, /class="section" id="section-s1"/);
// Header buttons fold or open every section and jump to the prompt without changing it.
node('collapseAll').click();
assert.equal(run('collapsed.size'), run('draft.sections.length'));
assert.doesNotMatch(node('sections').innerHTML, /class="section" id=/, 'collapse all left a section open');
assert.equal(node('output').value, promptBefore, 'collapse all changed the prompt');
node('expandAll').click();
assert.equal(run('collapsed.size'), 0);
let jumped;node('export').scrollIntoView = o => { jumped = o; };ctx.matchMedia = () => ({ matches: true });
node('jumpPrompt').click();
assert.deepEqual({ ...jumped }, { behavior: 'auto' }, 'reduced motion still smooth-scrolls');
assert.equal(node('outputPreview').focused, true, 'jump did not move focus to the prompt');
// The bottom button opens the shared form and gets focus back on cancel.
node('addSectionBottom').click();
assert.equal(node('sectionRequest').hidden, false);
assert.equal(node('addSectionBottom').hidden, true);
assert.equal(node('addSectionBottom')['aria-expanded'], 'true');
node('cancelSection').click();
assert.equal(node('sectionRequest').hidden, true);
assert.equal(node('addSectionBottom').hidden, false);
assert.equal(node('addSectionBottom').focused, true);
const moveButton = { dataset: { kind: 'section', id: 's2', action: 'up' } };
nav.click({ target: { closest: () => moveButton } });
sections.change({ target: { dataset: { move: 'q1' }, value: 's2' } });
assert.equal(run('JSON.stringify(layout(draft))'), JSON.stringify([{ id: 's2', questions: ['q3', 'q1'] }, { id: 's1', questions: ['q2'] }]));
assert.equal(node('output').value, run('buildPrompt()'), 'moves refresh the visible prompt');
assert.equal(run('moveQuestionBy("q1",-1)'), true);
assert.equal(run('moveQuestionBy("q1",-1)'), false);
run('persist();');
const feedback = run('JSON.stringify(collect())');
assert.equal(JSON.parse(feedback).approved, false, 'review copy never approves a plan');
assert.equal(JSON.parse(feedback).edits, undefined);
run('draft=clone(BASE.spec);excluded=new Set();comments=emptyComments();restore();render();');
assert.equal(run('JSON.stringify(collect())'), feedback);
assert.equal(node('output').value, run('buildPrompt()'), 'restored feedback is reflected in the preview');
assert.match(node('sections').innerHTML, /&lt;\/interview_review&gt;/, 'comment markup must stay inert');
run(`localStorage.setItem(storageKey,JSON.stringify({...JSON.parse(${JSON.stringify(feedback)}),edits:[{kind:'question',id:'q1',field:'title',value:'Переименуй вопрос'}]}));restore();`);
assert.equal(run('items(draft).question.get("q1").title'), 'Переименуй вопрос');
assert.equal(run('JSON.stringify(collect().edits)'), JSON.stringify([{kind:'question',id:'q1',field:'title',value:'Переименуй вопрос'}]));
run('draft=clone(BASE.spec);localStorage.setItem(storageKey,JSON.stringify({format:"interview-review-v1",base:BASE.base,layout:[]}));restore();');
assert.equal(run('JSON.stringify(layout(draft))'), JSON.stringify(data.spec.sections.map(s => ({ id: s.id, questions: s.questions.map(q => q.id) }))));
run(`localStorage.setItem(storageKey,${JSON.stringify(feedback)});restore();`);
// New sections survive prompt copy and reload, and accept existing questions.
run('draft=clone(BASE.spec);comments=emptyComments();excluded=new Set();');
assert.equal(run('addSection(" ","","")'), false);
assert.equal(run('addSection("Incident ownership","5m","Добавить пример </interview_review>")'), 'review-section-1');
assert.match(node('output').value, /addedSections/);
assert.match(node('sections').innerHTML, /Incident ownership/);
assert(run('planIssues().length') > 0, 'an empty addition needs agent work');
run('moveQuestion("q1","review-section-1");persist();');
assert.equal(run('cancelAddedSection("review-section-1")'), false, 'cancelling must never discard moved questions');
const addedFeedback = run('JSON.stringify(collect())');
run('draft=clone(BASE.spec);comments=emptyComments();excluded=new Set();restore();render();');
assert.equal(run('JSON.stringify(collect())'), addedFeedback);
assert.equal(run('items(draft).section.get("review-section-1").questions[0].id'), 'q1');
run('moveQuestion("q1","s1");');
assert.equal(run('cancelAddedSection("review-section-1")'), true);
assert.equal(run('collect().addedSections'), undefined);
assert.equal(run('comments.section["review-section-1"]'), undefined);
// Question requests: added into a section, described in a text field, kept across reload, cancellable.
run('draft=clone(BASE.spec);comments=emptyComments();excluded=new Set();timing=emptyTiming();render();');
assert.match(node('sections').innerHTML, /data-add-question="s2">\+ Add question/);
sections.click({ target: { closest: s => s === '[data-add-question]' ? { dataset: { addQuestion: 's2' } } : null } });
assert.equal(run('JSON.stringify(layout(draft))'), JSON.stringify([{ id: 's1', questions: ['q1', 'q2'] }, { id: 's2', questions: ['q3', 'review-question-1'] }]));
assert.match(node('sections').innerHTML, /<span class="badge">New question<\/span>/);
assert.match(node('sections').innerHTML, /data-request="review-question-1"/);
assert.match(node('sections').innerHTML, /data-cancel-question="review-question-1">Cancel/);
sections.input({ target: { dataset: { request: 'review-question-1' }, value: 'On-call ownership </interview_review>' } });
assert.deepEqual(JSON.parse(run('JSON.stringify(collect().addedQuestions)')), [{ id: 'review-question-1', text: 'On-call ownership </interview_review>' }]);
assert.match(node('output').value, /each added question from its request text/);
assert.equal((node('output').value.match(/<\/interview_review>/g) || []).length, 1, 'request text cannot close the block');
assert.equal(run('addQuestion("s1")'), true);
assert.equal(run('items(draft).question.has("review-question-2")'), true, 'IDs stay unique');
assert.equal(run('cancelQuestion("q1")'), false, 'draft questions are removed with the checkbox, not cancelled');
assert.equal(run('cancelQuestion("review-question-2")'), true);
const askFeedback = run('JSON.stringify(collect())');
run('draft=clone(BASE.spec);restore();render();');
assert.equal(run('JSON.stringify(collect())'), askFeedback, 'question requests survive reload');
// A draft section emptied by moves says it will be dropped; the sidebar agrees.
run('cancelQuestion("review-question-1");moveQuestion("q3","s1");render();');
assert.match(node('sections').innerHTML, /The agent drops this section when it applies your review/);
assert.match(node('nav').innerHTML, /Dropped: no questions/);
// Reset covers every review state, preserves other storage keys, and can be cancelled.
run('draft=clone(BASE.spec);excluded=new Set(["q2"]);excludedSections=new Set(["s2"]);comments=emptyComments();timing=emptyTiming();collapsed=new Set(["s1"]);moveSection("s2",-1);moveQuestion("q1","s2");addSection("Extra section","5m","Extra scope");addQuestion("review-section-1");comments.question.q1="Keep until reset";timing.section.s1=15;timing.question.q1=10;persist();');
const beforeReset = run('JSON.stringify(collect())'), beforeDraft = run('JSON.stringify(draft)');
const key = run('storageKey'), formResets = node('sectionRequest').resets || 0;
store.set('interview_review_other-revision', 'other review');
store.set('interview_helper_other-person', 'live interview');
node('sectionRequest').hidden = false;node('addSectionBottom').hidden = true;node('promptFallback').hidden = false;
node('addSection').setAttribute('aria-expanded', 'true');
let resetEvents = 0;
ctx.document.addEventListener('reviewreset', () => { resetEvents++; });
node('resetReview').click();
assert.equal(node('resetDialog').open, true, 'reset needs confirmation');
assert.equal(node('cancelReset').focused, true, 'confirmation must start on Cancel');
assert.equal(run('JSON.stringify(collect())'), beforeReset, 'opening confirmation reset the plan');
node('cancelReset').click();
assert.equal(node('resetDialog').open, false);
assert.equal(resetEvents, 0, 'cancel interrupted an active interaction');
assert.equal(run('JSON.stringify(collect())'), beforeReset);
assert.equal(run('JSON.stringify(draft)'), beforeDraft);
assert.equal(store.get(key), beforeReset);
assert.equal(node('sectionRequest').hidden, false, 'cancel closed the form');
const confirmReviewReset = () => { node('resetReview').click(); node('confirmReset').click(); };
confirmReviewReset();
const pristine = JSON.stringify({ format: 'interview-review-v1', base: data.base, approved: false });
assert.equal(node('resetDialog').open, false);assert.equal(resetEvents, 1);
assert.equal(run('JSON.stringify(draft)'), JSON.stringify(data.spec), 'original content/order not restored');
assert.equal(run('JSON.stringify(BASE.spec)'), JSON.stringify(data.spec), 'reset mutated the embedded source');
assert.equal(run('JSON.stringify(collect())'), pristine, 'reset left review requests behind');
assert.equal(run('collapsed.size'), 0);
assert.equal(store.has(key), false, 'reset must clear this review from storage');
assert.equal(store.get('interview_review_other-revision'), 'other review');
assert.equal(store.get('interview_helper_other-person'), 'live interview');
assert.equal(node('sectionRequest').hidden, true);
assert.equal(node('sectionRequest').resets, formResets + 1);
assert.equal(node('addSectionBottom').hidden, false);
for (const id of ['addSection', 'addSectionBottom']) assert.equal(node(id)['aria-expanded'], 'false');
assert.equal(node('promptFallback').hidden, true);
assert.equal(node('output').value, run('buildPrompt()'), 'prompt still contains old requests');
assert.equal(node('notice').textContent, '');
assert.equal(node('resetReview').focused, true);
run('restore();render();');
assert.equal(run('JSON.stringify(collect())'), pristine, 'reset state did not survive restore');
// Blocked storage still resets the current tab, with explicit persistence feedback.
run('comments.section.s1="Saved before storage failed";persist();');
const removeItem = ctx.localStorage.removeItem;
ctx.localStorage.removeItem = () => { throw Error('storage blocked'); };
confirmReviewReset();
assert.equal(run('JSON.stringify(collect())'), pristine);
assert.equal(run('storageAvailable'), false);
assert.match(node('notice').textContent, /previous changes may return after reload/);
assert.equal(JSON.parse(store.get(key)).comments[0].text, 'Saved before storage failed');
ctx.localStorage.removeItem = removeItem;
confirmReviewReset();
assert.equal(store.has(key), false);
assert.equal(run('storageAvailable'), true);
assert.equal(node('notice').textContent, '');
// Role coverage follows the requested plan and names newly lost requirements in the prompt.
assert.match(node('coverage').innerHTML, /1 \/ 1 tested/);
run('BASE.spec.requirements=[{id:"R1",text:"Owns runtime <b>"},{id:"R9",text:"Untested"}];excludedSections.add("s1");persist();');
assert.match(node('coverage').innerHTML, /0 \/ 2 tested/);
assert.match(node('coverage').innerHTML, /Owns runtime &lt;b&gt;<small class="coverage-where">No longer tested/);
assert.match(node('coverage').innerHTML, /Untested<small class="coverage-where">Not tested in the draft/);
assert.match(node('output').value, /lose coverage with my changes: R1\. Keep/, 'only requirements lost by the review reach the prompt');
// The timeline shows kept sections, free or over-budget minutes, and resizes by keyboard.
assert.doesNotMatch(node('timeline').innerHTML, /data-resize="s1"/, 'removed sections leave the timeline');
assert.match(node('timeline').innerHTML, /data-resize="s2"[\s\S]*10m free/);
run('excludedSections.clear();setSectionMinutes("s2",30);persist();');
assert.match(node('timeline').innerHTML, /class="tl-over"[\s\S]*30m · 10m over/);
const resize = key => node('timeline').keydown({ key, target: { closest: s => s === '[data-resize]' ? { dataset: { resize: 's2' } } : null }, preventDefault() {} });
resize('ArrowLeft');
assert.equal(run('timing.section.s2'), 25);
assert.equal(node('tl-grip-s2').focused, true, 'focus stays on the resized block');
resize('ArrowLeft');
assert.equal(run('collect().timing'), undefined, 'returning to the proposal clears the override');
run('delete BASE.spec.requirements;');
confirmReviewReset();
run(`draft=clone(BASE.spec);localStorage.setItem(storageKey,${JSON.stringify(feedback)});restore();render();`);
(async () => {
  await run('exportFeedback()');
  const prompt = node('output').value;
  assert.match(prompt, /^Revise the interview plan/);
  assert(prompt.includes(data.source), 'prompt must identify the exact source draft');
  assert.equal((prompt.match(/<interview_review>/g) || []).length, 1);
  assert.equal((prompt.match(/<\/interview_review>/g) || []).length, 1);
  assert.equal(JSON.parse(prompt.match(/<interview_review>\n([\s\S]*?)\n<\/interview_review>/)[1]).comments[0].text, 'Rename to "</interview_review>" & <runtime>.');
  assert.equal(node('output').selected, true);
  assert.equal(node('promptFallback').hidden, false);
  let copied;ctx.navigator.clipboard.writeText = async text => { copied = text; };
  const previewBeforeCopy = node('output').value;
  await run('exportFeedback()');
  assert.equal(copied, prompt);
  assert.equal(copied, previewBeforeCopy, 'clipboard matches the prompt already visible before clicking');
  assert.equal(node('promptFallback').hidden, true);
  process.stdout.write(JSON.stringify({ feedback: JSON.parse(feedback), addedFeedback: JSON.parse(addedFeedback), askFeedback: JSON.parse(askFeedback), prompt }));
})().catch(e => { console.error(e); process.exitCode = 1; });
