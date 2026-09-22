import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {serviceOne} from '../transporte/browser.mjs';
async function fixture(t, command) {
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'metodo-'));
 t.after(()=>fs.rm(root,{recursive:true,force:true}));
 await fs.mkdir(root+'/mailbox',{recursive:true});
 await fs.writeFile(root+'/mailbox/command.json',JSON.stringify(command));
 return root;
}
const id='a'.repeat(32);
test('fresh persists response; same operation never opens twice',async t=>{
 const root=await fixture(t,{id,op:'fresh',token:'t'});let calls=0;
 const runtime={newTab:async()=>{calls++;return {id:'tab',url:async()=>'https://chatgpt.com/',playwright:{locator:()=>({evaluateAll:async()=>[]})}};}};
 await serviceOne(runtime,root,fs);await serviceOne(runtime,root,fs);
 assert.equal(calls,1);
 assert.equal(JSON.parse(await fs.readFile(root+'/mailbox/responses/'+id+'.json')).result.fresh,true);
});
test('unfinished browser send claim is never invoked again',async t=>{
 const root=await fixture(t,{id,op:'send'});
 await fs.mkdir(root+'/mailbox/claims');await fs.writeFile(root+'/mailbox/claims/'+id+'.json','{}');
 assert.equal(await serviceOne({getTab:()=>assert.fail('replayed')},root,fs),false);
});
test('wrong current conversation returns an error without editing',async t=>{
 const root=await fixture(t,{id,op:'prepare',instance:{tab_id:'t',conversation_id:'wanted'},text:'x'});
 const runtime={getTab:async()=>({url:async()=>'https://chatgpt.com/c/other'})};
 await serviceOne(runtime,root,fs);
 assert.match(JSON.parse(await fs.readFile(root+'/mailbox/responses/'+id+'.json')).error,/Wrong conversation/);
});
test('lost tab recovers same conversation URL, never blank fresh',async t=>{
 const root=await fixture(t,{id,op:'current',instance:{tab_id:'old',conversation_id:'same'}});
 let url;
 const runtime={getTab:async()=>{throw Error('lost tab');},newTab:async u=>{url=u;return {url:async()=>u};}};
 await serviceOne(runtime,root,fs);
 assert.equal(url,'https://chatgpt.com/c/same');
 assert.equal(JSON.parse(await fs.readFile(root+'/mailbox/responses/'+id+'.json')).result.matches,true);
});
