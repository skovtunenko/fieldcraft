// Execute the live render path with DOM stubs; this checks output markup, not browser layout.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const nodes = new Map();
function node(selector) {
  if (!nodes.has(selector)) {
    const classes = new Set();
    nodes.set(selector, { innerHTML: '', textContent: '', hidden: false, setAttribute() {},
      classList: { toggle: (c, on) => on ? classes.add(c) : classes.delete(c), contains: c => classes.has(c) } });
  }
  return nodes.get(selector);
}
const ctx = { document: { addEventListener() {}, querySelector: node, querySelectorAll: () => [] } };
vm.runInNewContext(script + '\nrenderStatic();', ctx, { timeout: 2000 });
const body = node('#candidateProfile').innerHTML;
assert.equal(node('#prep').classList.contains('hidden'), false);
assert.equal(node('#openPrep').classList.contains('hidden'), false);
if (process.argv[3] === 'cv') {
  assert.equal(node('#candidateProfile').classList.contains('hidden'), false);
  assert.match(body, /<p class="portrait">According to cv\.md, a platform engineer/);
  assert.match(body, /<b>Example &amp; Co<\/b> · Engineer/);
  assert.match(body, /2020 – 2023/);
  assert.match(body, /CV: three services/);
  assert.match(body, /Claims payment runtime ownership/);
  assert.doesNotMatch(body, /class="insight inconsistencies"/);
} else if (process.argv[3] === 'feedback') {
  assert.match(body, /<p class="portrait">Round 1 feedback \(feedback\.md\) observed clear incident reasoning\.<\/p>/);
  assert.match(body, /Ownership remains untested/);
  assert.doesNotMatch(body, /Career timeline|class="insight standouts"/);
} else if (process.argv[3] === 'seven') {
  for (let i = 0; i < 7; i++) assert.match(body, new RegExp(`<b>Employer ${i}</b> · Engineer`));
  assert.match(body, /2000 – 2002/);
  assert.match(body, /2001 – 2003/);
  assert.doesNotMatch(body, /full.time|class="tl-row parallel"|Doesn't add up/);
} else if (process.argv[3] === 'overflow') {
  assert.match(body, /Career timeline \(selected entries\)/);
  assert.match(body, /Additional experience \(outside timeline\)/);
  assert.match(body, /Employer 12/);
  assert.match(body, /Independent &lt;lab&gt;/);
  assert.match(body, /Around 1999; end date not supplied/);
  assert.match(body, /Exact career dates unavailable/);
  assert.match(body, /Timeline limited to 12 entries/);
  for (let i = 0; i < 13; i++) assert.match(body, new RegExp(`<b>Employer ${i}</b>`));
  assert.doesNotMatch(body, /Independent <lab>/);
} else {
  assert.equal(body, '');
  assert.equal(node('#candidateProfile').classList.contains('hidden'), true);
}
console.log(`Background ${process.argv[3]}: executed renderer markup passed`);
