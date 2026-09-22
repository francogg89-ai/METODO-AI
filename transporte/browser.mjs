// Run INSIDE the authorized CUA/Node runtime, passing its actual tab factories.
// runtime = {newTab(url), getTab(id)}; each tab exposes the tested CUA API.
// No model-generated copies: fs -> variables -> paste/clipboard -> fs.
const encode = s => new TextEncoder().encode(s);
async function write(fs, path, value) {
  await fs.mkdir(path.slice(0, path.lastIndexOf('/')), {recursive:true});
  await fs.writeFile(path + '.tmp', JSON.stringify(value, null, 2), 'utf8');
  await fs.rename(path + '.tmp', path);
}
async function exists(fs, path) {try {await fs.access(path); return true;} catch {return false;}}
function conversation(url) {
  const u = new URL(url);
  if (u.origin !== 'https://chatgpt.com') throw Error('Unexpected browser origin');
  return u.pathname.match(/^\/c\/([^/]+)$/)?.[1] || null;
}
async function messages(tab) {
  return tab.playwright.locator('[data-message-id]').evaluateAll(nodes => nodes.map(n => ({
    id:n.getAttribute('data-message-id'), role:n.getAttribute('data-message-author-role')
  })));
}
async function composer(tab) {
  return tab.playwright.getByRole('textbox', {name:'Chatear con ChatGPT'});
}
async function readback(tab) {
  return (await composer(tab)).evaluate(el => {
    function walk(n) {
      if(n.nodeType === 3) return n.nodeValue || '';
      if(n.nodeType !== 1) return '';
      if(n.tagName === 'BR') return n.classList.contains('ProseMirror-trailingBreak') ? '' : '\n';
      return Array.from(n.childNodes).map(walk).join('');
    }
    return Array.from(el.childNodes).map(walk).join('\n');
  });
}
async function target(tab, id) {
  const message = tab.playwright.locator(`[data-message-id="${id}"]`);
  if(await message.count() !== 1 || await message.getAttribute('data-message-author-role') !== 'assistant')
    throw Error('Assistant response missing or ambiguous');
  const wrapper = message.locator('xpath=../..');
  const ids = await wrapper.locator('[data-message-id]').evaluateAll(ns => ns.map(n=>n.getAttribute('data-message-id')));
  if(ids.length !== 1 || ids[0] !== id) throw Error('Response wrapper identity ambiguous');
  const copy = wrapper.getByRole('button', {name:'Copiar respuesta'});
  if(await copy.count() !== 1) throw Error('Target response has no completion/copy control');
  const dom = await tab.playwright.domSnapshot();
  if(/button "(?:Detener respuesta|Stop generating|Stop response)"/i.test(dom)) throw Error('Generation still active');
  return {message, wrapper, copy};
}
async function resolve(runtime, instance) {
  let tab;
  try {tab = await runtime.getTab(instance.tab_id);} catch {
    if(!instance.conversation_id) throw Error('Fresh tab lost before first send');
    tab = await runtime.newTab('https://chatgpt.com/c/' + instance.conversation_id);
  }
  if(!tab) throw Error('Tab unavailable');
  const id = conversation(await tab.url());
  if(id !== instance.conversation_id) throw Error('Wrong conversation; do not use another current');
  return tab;
}

export async function serviceOne(runtime, root, fs) {
  root = root.replaceAll('\\','/');
  const commandPath = root + '/mailbox/command.json';
  if(!await exists(fs, commandPath)) return false;
  const cmd = JSON.parse(await fs.readFile(commandPath, 'utf8'));
  if(!/^[0-9a-f]{32}$/.test(cmd.id)) throw Error('Invalid mailbox id');
  const reply = root + '/mailbox/responses/' + cmd.id + '.json';
  if(await exists(fs, reply)) return false;
  const claim = root + '/mailbox/claims/' + cmd.id + '.json';
  await fs.mkdir(root + '/mailbox/claims', {recursive:true});
  // Exclusive persistent claim also prevents two browser workers from duplicating a send.
  try {await fs.writeFile(claim, JSON.stringify({op:cmd.op, issued_at:new Date().toISOString()}), {flag:'wx'});}
  catch(error) {if(error.code === 'EEXIST') return false; throw error;}
  let result, error, capturedCandidate;
  try {
    if(cmd.op === 'fresh') {
      const tab = await runtime.newTab('https://chatgpt.com/');
      if(conversation(await tab.url()) !== null || (await messages(tab)).length !== 0)
        throw Error('New tab is not an empty fresh conversation');
      result = {fresh:true, tab_id:tab.id, conversation_id:null};
      if(result.tab_id == null) throw Error('Runtime must expose persistent tab.id');
    } else {
      const tab = await resolve(runtime, cmd.instance);
      if(cmd.op === 'current') result = {matches:true};
      else if(cmd.op === 'prepare') {
        const box = await composer(tab);
        // Clear only pending composer text; never edit a previous message.
        await box.click(); await box.press('Control+A'); await box.press('Backspace');
        await tab.paste(null, cmd.text, {format:'text'});
        const actual = await readback(tab);
        result = {anomaly:actual !== cmd.text, utf8_bytes:encode(actual).length};
      } else if(cmd.op === 'readback') result = {text:await readback(tab)};
      else if(cmd.op === 'send') {
        if(await readback(tab) !== cmd.expected_text) result = {receipt:'NOT_SENT', detail:'Composer changed before send'};
        else {
          const before = new Set((await messages(tab)).map(x=>x.id));
          await (await composer(tab)).press('Enter');
          const deadline = Date.now()+600000;
          let observed = [];
          while(Date.now()<deadline) {
            await tab.playwright.waitForTimeout(300);
            observed = (await messages(tab)).filter(x=>!before.has(x.id));
            const user = observed.filter(x=>x.role === 'user');
            const assistant = observed.filter(x=>x.role === 'assistant');
            if(user.length === 1 && assistant.length === 1) {
              try {await target(tab, assistant[0].id);} catch {continue;}
              const id = conversation(await tab.url());
              if(!id || (cmd.instance.conversation_id && id !== cmd.instance.conversation_id)) throw Error('Conversation changed during send');
              result = {receipt:'DELIVERED', conversation_id:id, user_message_id:user[0].id, assistant_message_id:assistant[0].id};
              break;
            }
          }
          if(!result) result = {receipt:'UNKNOWN', observed, detail:'Send invoked, completion not established; never replay'};
        }
      } else if(cmd.op === 'capture') {
        const t = await target(tab, cmd.response_id);
        const sentinel = `METODO-COPY:${cmd.id}:${Date.now()}`;
        await tab.clipboard.writeText(sentinel);
        if(await tab.clipboard.readText() !== sentinel) throw Error('Clipboard sentinel unavailable');
        await t.copy.click();
        const deadline = Date.now()+2500;
        let text = '';
        while(Date.now()<deadline) {
          await tab.playwright.waitForTimeout(100);
          text = await tab.clipboard.readText();
          if(text && text !== sentinel) capturedCandidate = text;
          if(text && text !== sentinel) break;
        }
        if(!text || text === sentinel) throw Error('Clipboard not replaced; safe recapture allowed');
        await target(tab, cmd.response_id);
        if(conversation(await tab.url()) !== cmd.instance.conversation_id) throw Error('Conversation changed during capture');
        result = {text, complete:true, response_id:cmd.response_id, conversation_id:cmd.instance.conversation_id,
          provenance:'message-specific copy after completion; fresh clipboard sentinel replaced'};
      } else throw Error('Unsupported operation');
    }
  } catch(e) {
    if(cmd.op === 'capture' && capturedCandidate !== undefined) result = {text:capturedCandidate, complete:false, response_id:cmd.response_id, conversation_id:cmd.instance.conversation_id, error_detail:String(e)};
    else if(cmd.op === 'send') result = {receipt:'UNKNOWN', detail:String(e)};
    else error = String(e);
  }
  await write(fs, reply, {id:cmd.id, result, error});
  return true;
}
