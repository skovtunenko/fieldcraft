const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const path=require('node:path'),os=require('node:os'),{execFileSync}=require('node:child_process');
// The skill sits at skills/<name> (public) or skills/<bucket>/<name> (source repository).
let repoRoot=__dirname;while(!fs.existsSync(path.join(repoRoot,'skills')))repoRoot=path.dirname(repoRoot);
const skill=['.',...fs.readdirSync(path.join(repoRoot,'skills'))].map(d=>path.join(repoRoot,'skills',d,'auditing-skill-best-practices')).find(d=>fs.existsSync(path.join(d,'SKILL.md')));
const root=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'audit-review-logic-')));
process.on('exit',()=>fs.rmSync(root,{recursive:true,force:true}));
const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'../fixtures/review/findings-violating.json'),'utf8'));
fixture.lang='ru';
fixture.labels={page:{saveChange:'Сохранить правку'}};  // test data: a translated label on top of the English ones
fs.writeFileSync(root+'/findings.json',JSON.stringify(fixture));
execFileSync('uv',['run','--quiet','--script',path.join(skill,'scripts/render_review_page.py'),root+'/findings.json',root+'/review.html'],{stdio:'pipe'});
const html=fs.readFileSync(root+'/review.html','utf8');
const script=[...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)].filter(m=>!m[1].includes('application/json')).map(m=>m[2]).join('\n');
const data=JSON.parse(html.match(/<script type="application\/json" id="audit-data">([\s\S]*?)<\/script>/)[1]);
const f=data.failures.find(f=>f.rule==='BP-55');
const item={key:'f0',f,rule:data.rules.find(r=>r.id==='BP-55')};
const cx=vm.createContext({state:{},data,markable:[item],failures:[item],refsOf:{}});
// Build the labels with the page's own lines: English from the embedded labels block, the findings' labels on top.
const labelsJson=html.match(/<script type="application\/json" id="page-labels">([\s\S]*?)<\/script>/)[1];
cx.document={getElementById:id=>{assert.equal(id,'page-labels');return {textContent:labelsJson};}};
vm.runInContext(script.match(/  var L = [^\n]+/)[0]+'\n'+script.match(/  function fill\([^\n]+/)[0],cx);
assert.equal(cx.L.saveChange,'Сохранить правку','A translated label must reach the page');
assert.equal(cx.L.editDraft,'Draft · not included in the instruction yet','A label the findings leave out must stay English');
const helperStart=script.indexOf('function reviewReplace('),helperEnd=script.indexOf('  function card(',helperStart);
assert(helperStart>=0&&helperEnd>helperStart);
vm.runInContext(`
function entry(key){return state[key]||(state[key]={mark:'',edited:null,comment:''});}
function setMark(key,mark){var e=entry(key);e.mark=mark;return e;}
function pending(text,marks){return (marks||[]).filter(m=>String(text).includes(m));}
function refRejected(){return false;}
`+script.slice(script.indexOf('  function isTextEdit('),script.indexOf('  function folder('))+script.slice(helperStart,helperEnd),cx);
const pure=Object.fromEntries(['reviewInfer','reviewCandidate'].map(name=>[name,cx[name]]));
const exportStart=script.indexOf('  function block(label, text) {');
const exportEnd=script.indexOf('  // Highlighted Markdown and XML source',exportStart);
assert(exportStart>=0&&exportEnd>exportStart);
vm.runInContext(script.slice(exportStart,exportEnd),cx);
cx.item=item;
function run(s){return vm.runInContext(s,cx);}
assert.equal(run('buildExport()'),'');
run("entry(item.key).comment='Why is this needed?'");
let questionExport=run('buildExport()');
assert(questionExport.includes('[question from the reviewer]'));
assert(questionExport.includes('Change no files. Reply with the answers only'));
assert(!questionExport.includes('Run the auditing-skill-best-practices'));
run("entry(item.key).mark='reject'");
let rejectedExport=run('buildExport()');
assert(rejectedExport.includes('[rejected by the reviewer]'));
assert(rejectedExport.includes('Do not run an audit, mechanical checker, or regenerate the review page.'));
assert(rejectedExport.includes('Offer to rerun the audit on request.'));
assert(rejectedExport.includes("wait for the user's reply."));
assert(!rejectedExport.includes("send the skill's full report"));
cx.state={};
assert.equal(run('reviewCanAccept(item)'),false,'Accept must be disabled only while placeholders are unresolved');
run('reviewBegin(item)');assert.equal(run('entry(item.key).mark'),'');
assert.equal(run('buildExport()'),'','An unsaved draft must not reach the agent');
assert.equal(run('reviewCommit(item)'),false,'An empty placeholder must block saving');
run("state.editDrafts[item.key].values['<server>']='github'");
assert.equal(run('buildExport()'),'','Typing into a draft must not apply it');
assert.equal(run('reviewCommit(item)'),true);
assert.equal(run('entry(item.key).mark'),'edit');
assert.equal(run('entry(item.key).edited'),'call the github:create_issue tool');
assert.equal(run('reviewCanAccept(item)'),true,'A saved revision with filled placeholders must be acceptable');
let result=run('buildExport()');assert(result.includes('call the github:create_issue tool'));assert(!result.includes('<server>'));assert(!result.includes('Warning: still contains'));
assert(result.includes('Offer to rerun the audit on request.'));
assert(result.includes("Stop after this summary and offer, and wait for the user's reply."));
assert(result.includes('A new audit requires a separate explicit request from the user.'));
assert(!result.includes('Run the auditing-skill-best-practices'));
assert.equal(run('reviewAccept(item)'),true);assert.equal(run('entry(item.key).mark'),'accept');
assert.equal(run('entry(item.key).edited'),'call the github:create_issue tool');
assert(run('buildExport()').includes('call the github:create_issue tool'));
assert(!run('buildExport()').includes('<server>'));
result=run('buildExport()');
const saved=JSON.parse(run('JSON.stringify(state)'));
cx.state=saved;run('reviewBegin(item)');assert.equal(run("state.editDrafts[item.key].values['<server>']"),'github');
run("state.editDrafts[item.key].values['<server>']='other';reviewCancel(item)");
assert.equal(run('entry(item.key).edited'),'call the github:create_issue tool');
assert.equal(run('buildExport()'),result,'Cancel must preserve the saved export');
run("reviewBegin(item);state.editDrafts[item.key].values['<server>']='gitlab'");
assert.equal(run('reviewCanAccept(item)'),true);assert.equal(run('reviewAccept(item)'),true);
assert.equal(run('entry(item.key).mark'),'accept');assert.equal(run('entry(item.key).edited'),'call the gitlab:create_issue tool');
assert(!run('state.editDrafts[item.key]'));
assert(run('buildExport()').includes('call the gitlab:create_issue tool'));
run("setMark(item.key,'reject')");assert.equal(run('reviewAccept(item)'),true);
assert.equal(run('entry(item.key).edited'),'call the gitlab:create_issue tool');
for(const mark of ['','accept','reject','edit']){
 cx.state={f0:{mark,edited:mark==='edit'?'call the github:create_issue tool':null,comment:'keep me',replacements:mark==='edit'?{'<server>':'github'}:{}}};
 const before=run('JSON.stringify(entry(item.key))'),beforeExport=run('buildExport()');
 run('reviewBegin(item)');run("state.editDrafts[item.key].values['<server>']='draft-only';reviewCancel(item)");
 assert.equal(run('JSON.stringify(entry(item.key))'),before);assert.equal(run('buildExport()'),beforeExport);
}
assert.deepEqual(JSON.parse(JSON.stringify(pure.reviewInfer('(<x>)+[<x>]','(team)+[team]',['<x>']))),{'<x>':'team'});
assert.equal(pure.reviewInfer('<x>/<x>','one/two',['<x>']),null);
assert.equal(pure.reviewCandidate(f,{mode:'fields',values:{'<server>':'<server>'}}).valid,false);
assert.equal(pure.reviewCandidate(f,{mode:'fields',values:{'<server>':'  '}}).valid,false);
const textF={before:'before',after:'after'};
assert.equal(pure.reviewCandidate(textF,{mode:'text',text:'new after'}).valid,true);
assert.equal(pure.reviewCandidate(textF,{mode:'text',text:''}).valid,false);
const rangeF={before:'before',after:'after',range:'SKILL.md:3-30',fix:'Replace these lines.'};
assert.equal(pure.reviewCandidate(rangeF,{mode:'text',text:'new replacement step'}).text,'new replacement step');
// A range edit starts with its full Change and first span, then exports the saved step.
cx.rangeItem={...item,f:rangeF};cx.state={};cx.markable=[cx.rangeItem];
run('reviewBegin(rangeItem)');
assert(run('state.editDrafts[rangeItem.key].text').includes('After (first changed span):\nafter'));
run("state.editDrafts[rangeItem.key].text='new replacement step'");
assert.equal(run('reviewCommit(rangeItem)'),true);
assert(run('buildExport()').includes('new replacement step'));
assert(!run('buildExport()').includes('Before (first changed span)'));
cx.markable=[item];
// Exercise the generated editor's input handler, including the live Accept button.
const editorStart=script.indexOf('function reviewResizeField('),editorEnd=script.indexOf('  function card(',editorStart);
assert(editorStart>=0&&editorEnd>editorStart);
vm.runInContext(script.slice(editorStart,editorEnd),cx);
class TestNode {
 constructor(tag,attrs={},text=''){this.tag=tag;this.attrs=attrs;this.textContent=text;this.children=[];this.events={};this.value='';this.style={};this.scrollHeight=0;this.clientWidth=320;this.offsetHeight=36;this.clientHeight=34;}
 appendChild(child){child.parentElement=this;this.children.push(child);return child;}
 addEventListener(name,fn){this.events[name]=fn;}
 getAttribute(name){return this.attrs[name];}
}
const acceptButton={disabled:true};
cx.el=(tag,attrs,text)=>new TestNode(tag,attrs,text);
cx.document={getElementById:id=>id==='card-f0'?{querySelector:()=>acceptButton}:null,createTextNode:text=>new TestNode('#text',{},text),createElement:tag=>{assert.equal(tag,'canvas');return {getContext:()=>({measureText:text=>({width:text.length*7})})};}};
cx.getComputedStyle=()=>({font:'12px monospace',paddingLeft:'8px',paddingRight:'8px',borderLeftWidth:'1px',borderRightWidth:'1px'});
cx.save=()=>{};
cx.requestAnimationFrame=fn=>fn();
cx.state={};run('reviewBegin(item)');
const editor=run('reviewEditor(item,"edit-f0")');
function nodes(node){return [node,...node.children.flatMap(nodes)];}
const field=nodes(editor).find(n=>n.tag==='textarea');
const saveButton=nodes(editor).find(n=>n.attrs.class==='primary save-edit');
assert(field&&saveButton);
assert.equal(saveButton.textContent,'Сохранить правку','The editor must show the translated label');
assert.equal(field.attrs['aria-label'],'Value for <server>');
assert.equal(field.parentElement.attrs.class,'inline-template','The field must stay in the same text flow as its prefix and suffix');
assert.deepEqual(field.parentElement.children.map(n=>n.tag),['#text','textarea','#text']);
assert.equal(field.parentElement.children[0].textContent,'call the ');
assert.equal(field.parentElement.children[2].textContent,':create_issue tool');
assert.equal(field.attrs.wrap,'off','Long lines must scroll horizontally instead of wrapping');
assert.equal(field.style.width,'76px','The empty field must fit the placeholder, padding, borders and caret');
field.value='x'.repeat(1000);field.events.input();
assert.equal(field.style.width,'320px','Width must stop at the parent column');
field.value='short';field.events.input();
assert.equal(field.style.width,'55px','Deleting text must also shrink the width');
field.value='one\nlonger';field.events.input();
assert.equal(field.style.width,'62px','Multiline width must follow the longest line');
field.value='';field.events.input();
assert.equal(field.style.width,'76px','Clearing the value must restore placeholder width');
field.scrollHeight=1000;field.events.input();
assert.equal(field.style.height,"240px","Long input must stop growing at 240px");
field.scrollHeight=45;field.events.input();
assert.equal(field.style.height,"47px","Deleting text must shrink the field");
assert.equal(acceptButton.disabled,true);
for(const value of ['github','очень-длинное-имя'.repeat(20),'first line\nsecond line','trailing line\n','x']){
 field.value=value;field.events.input();
 assert(Number.parseFloat(field.style.width)<=320,'Typing must never exceed the parent width');
 assert.equal(acceptButton.disabled,false,'Typing a valid value must immediately enable Accept');
 assert.equal(saveButton.disabled,false);
 assert.equal(run('buildExport()'),'','Input events must keep the draft out of the export');
}
field.value='';field.events.input();
assert.equal(acceptButton.disabled,true,'Clearing the placeholder must disable Accept again');
assert.equal(saveButton.disabled,true);
field.value='first line\nsecond line';field.events.input();
assert.equal(run('reviewCommit(item)'),true);
assert(run('buildExport()').includes('call the first line\nsecond line:create_issue tool'),'Saved multiline text must reach the export unchanged');
assert.equal(run('reviewCanAccept(item)'),true);
run('reviewBegin(item)');
const restoredEditor=run('reviewEditor(item,"edit-f0")');
assert.equal(nodes(restoredEditor).find(n=>n.tag==='textarea').value,'first line\nsecond line');
assert.equal(acceptButton.disabled,false,'Reopening a saved revision must keep Accept enabled');
assert.equal(run('reviewAccept(item)'),true);
assert(run('buildExport()').includes('call the first line\nsecond line:create_issue tool'));

assert(script.includes('afterPanel.lastElementChild.replaceWith(editor)'));
assert(!script.includes('input.style.width'));
assert(!script.includes('input-sizer'));
const css=html.match(/<style>([\s\S]*?)<\/style>/)[1];
assert(!css.includes('.inline-field{'),'No block wrapper may force the placeholder onto a separate line');
assert(css.includes('.inline-template>textarea{display:inline-block;vertical-align:middle;box-sizing:border-box;width:36px;max-width:100%;min-width:0;'));
assert(css.includes('max-height:240px;resize:none;overflow:auto;'));
assert(css.includes('white-space:pre;overflow-wrap:normal;'));
assert(css.includes('::-webkit-scrollbar{width:10px;height:10px}'));
assert(!script.includes('entry(item.key).edited = editBox.value'));
// Exercise the actual generated header guards and group status expressions.
const handlers=[...script.matchAll(/(?:top|head)\.addEventListener\("click", function \(ev\) \{ ([^\n]+) \}\);/g)];
assert.equal(handlers.length,2);
for(const match of handlers){
 let clicks=0;
 const handler=vm.runInNewContext('(function(ev){'+match[1]+'})',{chev:{click(){clicks++;}}});
 handler({target:{closest(){return null;}}});assert.equal(clicks,1);
 for(const kind of ['a','button','input','textarea','select','label']){
  handler({target:{closest(selector){assert(selector.split(',').includes(kind));return {};}}});assert.equal(clicks,1);
 }
}
const groupStart=script.indexOf('      var groupMark ='),groupEnd=script.indexOf('      section.appendChild(head);',groupStart);
assert(groupStart>=0&&groupEnd>groupStart);
const group=vm.runInNewContext('(function(marks){var items=marks.map(mark=>({mark})),decided=marks.filter(Boolean).length,result;'+
 'var markOf=i=>i.mark,STATE_LABEL={accept:"accepted",reject:"rejected",edit:"edited"},L={unreviewed:"open",progress:"{n}/{m}"};'+
 'var el=(tag,attrs,text)=>({attrs,text}),head={appendChild(value){result=value;}};'+script.slice(groupStart,groupEnd)+'return result;})');
for(const [marks,label] of [[['',''],'open'],[['accept','accept'],'accepted'],[['reject','reject'],'rejected'],[['edit','edit'],'edited'],[['accept',''],'1/2'],[['accept','reject'],'2/2']]){
 assert.equal(group(marks).text,label);
}
const outcome={checks:'passed',headerToggles:true,groupStatusCases:6,draftNotExported:true,placeholderValidation:true,saveUpdatesAfter:true,saveUpdatesExportAndNotes:true,acceptSavedRevision:true,acceptValidDraft:true,acceptAfterRejectionKeepsRevision:true,cancelPreservesAllDecisionStates:true,restoredValues:true,regularTextEdits:true,rangeEdits:true,inputSizing:'measured content width clamped to column; height capped at 240px; two-axis overflow',inlineTextFlow:true,contentWidthShrinks:true,horizontalScrolling:true,boundedTextarea:true,multilinePlaceholderRoundTrip:true,liveInputEnablesAccept:true,reopenedSavedEditorAcceptable:true};
console.log(JSON.stringify(outcome));
