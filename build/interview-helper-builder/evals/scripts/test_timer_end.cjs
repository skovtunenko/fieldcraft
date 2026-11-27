const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
process.env.TZ = 'Europe/Warsaw';
const html = fs.readFileSync(process.argv[2], 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const NativeDate = Date;
let now;
class ClockDate extends NativeDate {
  constructor(...args) { super(...(args.length ? args : [now])); }
  static now() { return now; }
}
const clock = (hour, minute, second = 0, day = 6) => { now = new NativeDate(2026, 10, day, hour, minute, second).getTime(); };
const nodes = new Map(), storage = new Map();
const node = selector => {
  if (!nodes.has(selector)) {
    const classes = new Set();
    nodes.set(selector, {
      value: '', textContent: '', innerHTML: '', style: {}, hidden: false, attributes: {}, listeners: {},
      classList: { add: c => classes.add(c), remove: c => classes.delete(c), contains: c => classes.has(c), toggle: (c, yes) => yes ? classes.add(c) : classes.delete(c) },
      setAttribute(k, v) { this.attributes[k] = String(v); }, addEventListener(k, fn) { this.listeners[k] = fn; },
      querySelector: s => node(selector + ' ' + s), querySelectorAll: () => [], focus() {}, scrollIntoView() {},
    });
  }
  return nodes.get(selector);
};
const ctx = { Date: ClockDate, CSS: { escape: String },
  document: { addEventListener() {}, querySelector: node, querySelectorAll: () => [], activeElement: null },
  localStorage: { getItem: k => storage.get(k) || null, setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k) },
  setInterval: () => 1, clearInterval() {}, setTimeout() {}, clearTimeout() {}, confirm: () => true,
};
vm.createContext(ctx);vm.runInContext(script, ctx);
assert.equal(typeof ctx.setTimerEnd, 'function', 'a late pause has no local end-time correction');
const run = code => vm.runInContext(code, ctx);
const reset = () => { storage.clear();clock(11, 30);run('state.questions={};state.sections={};state.flags=[];state.briefing={};embeddedTimer=null;storageAvailable=true;timerTicker=null'); };
const endAt = value => { node('#timerEndAt').value = value;ctx.setTimerEnd(); };

reset();ctx.startTimer();
assert.equal(node('#timerStart').disabled, true, 'Start stays active while the timer runs');assert.equal(node('#timerPause').disabled, false);
{ // the prompt carries only marked evidence and only the task sentences it needs
  const qd = run('CONFIG.sections[0].questions[0]'), [pos, pos2] = qd.positives, [neg, neg2] = qd.negatives;
  run(`setMark(qState(${JSON.stringify(qd.id)}),sigKey('positive',${JSON.stringify(pos)}),'+')`);
  ctx.generatePrompt();const pr = node('#promptOutput').value;
  assert.ok(pr.includes(pos), 'the marked signal is missing from the prompt');
  assert.ok(pr.includes(`<ask>${qd.ask}</ask>`), 'the question text is missing from the prompt');
  assert.ok(pr.includes('by meaning'), 'the task does not say that asks are rephrased');
  for (const t of [pos2, neg, neg2]) assert.ok(!pr.includes(t), 'unmarked signal reached the prompt: ' + t);
  for (const t of ['signals_not_marked', 'requirement_coverage', 'cut for time', 'skipped', 'flagged_moments', 'timer 0']) assert.ok(!pr.includes(t), 'unneeded prompt content: ' + t);
  assert.match(pr, / @ \d+:\d\d\n/, 'a mark lost its short elapsed time');
  run('state.questions={}');
}
{ // the editable instructions replace the standing task; data notes stay automatic
  const qd = run('CONFIG.sections[0].questions[0]'), [pos] = qd.positives;
  run(`setMark(qState(${JSON.stringify(qd.id)}),sigKey('positive',${JSON.stringify(pos)}),'+')`);
  run(`state.final.instructions='1. Rate the candidate on our L1-L5 ladder.\\n\\n- Answer in Russian <briefly>.'`);
  ctx.generatePrompt();let pr = node('#promptOutput').value;
  assert.ok(pr.includes('\n1. Rate the candidate on our L1-L5 ladder.\n2. Answer in Russian &lt;briefly>.\n3. "@ mm:ss"'), 'custom instructions were not numbered, escaped, and followed by the data notes');
  assert.ok(!pr.includes('Respond in English'), 'default instructions leaked past the edit');
  run(`state.final.instructions='   '`);ctx.generatePrompt();pr = node('#promptOutput').value;
  assert.ok(pr.includes('Stay within my marks') && pr.includes('Respond in English'), 'empty instructions did not fall back to the default');
  // the language line follows the spec language; an unknown tag falls back to English
  for (const [tag, line] of [['ru', 'Respond in Russian.'], ['uk', 'Respond in Ukrainian.'], ['qqq', 'Respond in English.'], ['not a tag', 'Respond in English.']]) {
    run(`CONFIG.language=${JSON.stringify(tag)}`);ctx.generatePrompt();
    assert.ok(node('#promptOutput').value.includes(line), `language ${tag} did not give "${line}"`);
  }
  run('delete CONFIG.language');
  run('delete state.final.instructions;state.questions={}');
}
{ // paired cues sit on their follow-up's line, not in the signal blocks
  const qd = run('CONFIG.sections[0].questions[0]'), id = JSON.stringify(qd.id), [pos] = qd.positives, [neg] = qd.negatives, fu = qd.followups[0];
  run(`CONFIG.sections[0].questions[0].probes=[{text:${JSON.stringify(fu)},listenFor:${JSON.stringify(pos)},warnIf:${JSON.stringify(neg)}}]`);
  run(`const q=qState(${id});setMark(q,sigKey('followup',${JSON.stringify(fu)}),'+');setMark(q,sigKey('positive',${JSON.stringify(pos)}),true);setMark(q,sigKey('negative',${JSON.stringify(neg)}),true)`);
  ctx.generatePrompt();const pr = node('#promptOutput').value, line = pr.split('\n').find(l => l.startsWith('- Follow-up'));
  assert.ok(line && line.includes(`; heard: "${pos}"`) && line.includes(`; observed: "${neg}"`), 'paired cues are not on the follow-up line');
  assert.ok(!pr.includes('<positive_signals_rated>') && !pr.includes('<negative_signals_observed>'), 'paired cues repeated in a signal block');
  run('state.questions={}');
}
clock(12, 50, 43);ctx.pauseTimer();
assert.equal(node('#timerStart').disabled, false);assert.equal(node('#timerPause').disabled, true, 'Pause stays active while paused');
assert.equal(node('.timer-box').classList.contains('ended'), true, 'a stopped timer is not shown as ended');
assert.equal(ctx.loadTimer().elapsed, 80 * 60000 + 43000);
ctx.openTimerEnd();endAt('2026-11-06T12:30:00');
assert.equal(ctx.loadTimer().elapsed, 60 * 60000, 'late pause was not corrected to the entered local end');
assert.equal(ctx.loadTimer().endedAt, new NativeDate(2026, 10, 6, 12, 30).getTime());
assert.equal(ctx.loadTimer().running, false);
assert.equal(node('.timer-box').classList.contains('paused'), false, 'finished timer still warns about an accidental pause');
assert.ok(node('#timerEndStatus').textContent.includes('12:30'));
const ended = ctx.loadTimer();ctx.renderTimer();assert.deepEqual(ctx.loadTimer(), ended, 'render mutated saved correction');
const beforeFuture = JSON.stringify(ended);
endAt('2026-03-29T02:30:00');assert.equal(JSON.stringify(ctx.loadTimer()), beforeFuture, 'nonexistent local DST time was normalized silently');
endAt('2026-11-06T14:00:00');assert.equal(JSON.stringify(ctx.loadTimer()), beforeFuture, 'future end was accepted');
endAt('2026-11-06T11:00:00');assert.equal(JSON.stringify(ctx.loadTimer()), beforeFuture, 'end before start was accepted');
endAt('2026-11-06T12:35:00');assert.equal(ctx.loadTimer().elapsed, 65 * 60000, 'repeated correction lost the original run history');
clock(13, 0);assert.equal(ctx.stampNow(), null, 'post-interview mark received a time');
assert.ok(ctx.stampTitle({ at: Date.now() }).includes('After interview end'), 'post-end tooltip of older state falsely claims the timer never started');
ctx.generatePrompt();assert.ok(node('#promptOutput').value.includes('<interview_timing>'));
reset();ctx.startTimer();clock(11, 40);ctx.pauseTimer();endAt('2026-11-06T11:30:00');
assert.equal(ctx.loadTimer().elapsed, 0);ctx.stampNow();assert.equal(ctx.loadTimer().running, false, 'zero-duration ended timer auto-started');

reset();ctx.startTimer();clock(11, 40);ctx.pauseTimer();assert.equal(ctx.stampNow(), null, 'mark during a pause received a time');clock(11, 45);ctx.startTimer();assert.ok(ctx.stampNow().el > 0, 'running timer lost its stamp');clock(13, 0);ctx.pauseTimer();
endAt('2026-11-06T12:30:00');assert.equal(ctx.loadTimer().elapsed, 55 * 60000, 'pause duration counted as interview time');
endAt('2026-11-06T11:42:00');assert.equal(ctx.loadTimer().elapsed, 10 * 60000, 'end during a pause used wall-clock duration');
endAt('2026-11-06T11:35:00');assert.equal(ctx.loadTimer().elapsed, 5 * 60000, 'earlier known run cannot be selected');
clock(13, 0);ctx.startTimer();clock(13, 5);ctx.pauseTimer();
assert.equal(ctx.loadTimer().elapsed, 10 * 60000, 'resume after correction restored discarded overrun');

reset();clock(23, 50);ctx.startTimer();clock(0, 40, 0, 7);ctx.pauseTimer();
endAt('2026-11-07T00:20:00');assert.equal(ctx.loadTimer().elapsed, 30 * 60000, 'midnight correction used the wrong date');
reset();ctx.startTimer();clock(11, 40);node('#timerStartAt').value = '11:25';ctx.setTimerStart();clock(12, 10);ctx.pauseTimer();
endAt('2026-11-06T12:00:00');assert.equal(ctx.loadTimer().elapsed, 35 * 60000, 'start-time edit left stale run history');

reset();run('saveTimer({running:false,elapsed:80*60000,startedAt:null})');clock(13, 0);ctx.openTimerEnd();
assert.equal(node('#timerEndLegacy').hidden, false);
endAt('2026-11-06T12:30:00');assert.equal(ctx.loadTimer().elapsed, 80 * 60000, 'legacy pause history was guessed');
node('#timerEndElapsed').value = '60:00';endAt('2026-11-06T12:30:00');assert.equal(ctx.loadTimer().elapsed, 60 * 60000);
assert.equal(ctx.loadTimer().endSource, 'manual-duration');
ctx.openTimerEnd();assert.equal(node('#timerEndLegacy').hidden, false, 'repeat legacy correction pretended to have run history');
const legacyBefore = JSON.stringify(ctx.loadTimer());endAt('2026-11-06T12:35:00');assert.equal(JSON.stringify(ctx.loadTimer()), legacyBefore);
node('#timerEndElapsed').value = '65:00';endAt('2026-11-06T12:35:00');assert.equal(ctx.loadTimer().elapsed, 65 * 60000);
ctx.generatePrompt();assert.ok(node('#promptOutput').value.includes('Interview length on my timer: 65:00'), 'prompt lost the corrected interview length');
reset();clock(12, 0);run('saveTimer({running:true,elapsed:10*60000,startedAt:Date.now()})');clock(13, 0);
endAt('2026-11-06T12:30:00');assert.equal(ctx.loadTimer().elapsed, 40 * 60000, 'known legacy running interval lost its prior elapsed prefix');
const prior = JSON.stringify(ctx.loadTimer());endAt('2026-11-06T11:50:00');assert.equal(JSON.stringify(ctx.loadTimer()), prior);

// Backup fallback uses the corrected frozen timer; an existing LocalStorage timer wins.
const timerCopy = ctx.timerForBackup();
storage.clear();run('storageAvailable=false');ctx.backup = timerCopy;run('embeddedTimer=backup');
assert.equal(ctx.loadTimer().elapsed, 40 * 60000);
run('storageAvailable=true;saveTimer({running:false,elapsed:1000,startedAt:null})');
assert.equal(ctx.loadTimer().elapsed, 1000);
ctx.resetTimer();assert.equal(ctx.loadTimer().elapsed, 0);assert.equal(ctx.loadTimer().endedAt, undefined);
run('storageAvailable=false;embeddedTimer=null');ctx.startTimer();assert.equal(ctx.loadTimer().running, false);
assert.equal(ctx.loadTimer().historyFrom, undefined, 'unavailable timer invented a run interval');
{ // pace rail: timed sections only, labeled; needle tag reads time left, then time over
  const rail = node('#paceRail');run('state.questions={}');
  run('renderPaceRail(0)');
  assert.equal((rail.innerHTML.match(/class="pace-seg/g) || []).length, 2, 'a section without numeric minutes got a segment');
  assert.ok(!rail.innerHTML.includes('pace-needle'), 'needle shown before the timer ran');
  assert.match(rail.attributes['aria-label'], /timer not started, 30 min planned/);
  run('renderPaceRail(1.5)');
  assert.ok(rail.innerHTML.includes('data-t="01:30 · 29m left"'), 'needle tag lacks elapsed time and minutes left');
  assert.match(rail.innerHTML, /class="pace-seg now"[^>]*><span class="pace-fill" style="width:15%"><\/span><span class="pace-name">1\. Opening<\/span><i>10m<\/i>/);
  assert.equal(rail.className, 'pace-rail');
  run('renderPaceRail(23)');assert.equal(rail.className, 'pace-rail warn', 'last 8 minutes are not marked');
  run('renderPaceRail(32.5)');
  assert.ok(rail.innerHTML.includes(' · +3m over"'), 'overrun is not tagged');assert.equal(rail.className, 'pace-rail over');
  assert.match(rail.attributes['aria-label'], /32 of 30 min, \+3m over; by the clock in section 2 of 2, Deep dive/);
}
console.log('Timer end: late pause, local date/time, pauses, midnight, start edits, repeat edits, resume, legacy limits, post-end marks, prompt, backup, storage priority, reset, and pace rail pass');
