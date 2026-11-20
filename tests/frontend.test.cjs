// Unit-test interface behaviour with a small fake DOM; no browser or network.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('src/agentic_sdlc/static/app.js', 'utf8');

class Element {
  constructor() { this.children = []; this.listeners = {}; this.value = ''; this.hidden = false; this.checked = false; this.dataset = {}; this.classList = {add(){}, remove(){}}; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  focus() {}
  scrollIntoView() {}
  remove() {}
  click() { return this.listeners.click?.({preventDefault(){}}); }
}

function setup(result, ok = true) {
  const nodes = new Map();
  const get = selector => {
    if (!nodes.has(selector)) nodes.set(selector, new Element());
    return nodes.get(selector);
  };
  get('input[name="mode"]:checked').value = 'demo';
  const stageStates = [new Element(), new Element(), new Element()];
  const blobs = [];
  const document = {
    querySelector:get,
    querySelectorAll: selector => selector === '.stage-state' ? stageStates : [],
    createElement: () => new Element(),
    body: new Element(),
  };
  const context = vm.createContext({document, Blob, TypeError, setTimeout(){}, matchMedia:()=>({matches:true}),
    URL: {createObjectURL(blob){blobs.push(blob); return 'blob:test';}, revokeObjectURL(){}},
    fetch: async (url, options) => url === '/api/config' ? {ok:true,json:async()=>({openai:false})}
      : {ok,json:async()=>result},
  });
  vm.runInContext(source, context);
  return {get, blobs, document};
}

const result = {
  task:'Build an enquiry API', mode:'demo', engine:'langgraph',
  plan:['Define requirements'], architecture:['Use a small API'],
  implementation_notes:['Review the implementation'], files:[], test_plan:['Validate inputs'],
};

test('demo runs and JSON/Markdown exports contain the result', async () => {
  const ui = setup(result);
  ui.get('#task').value = result.task;
  await ui.get('#task-form').listeners.submit({preventDefault(){}});
  assert.equal(ui.get('#results').hidden, false);
  assert.equal(ui.get('#result-mode').textContent, 'DEMO RESULT · PREDEFINED NOTES');
  assert.equal(ui.get('#result-body').children.length, 4);
  ui.get('#download-json').click();
  assert.deepEqual(JSON.parse(await ui.blobs[0].text()), result);
  ui.get('#download-md').click();
  assert.match(await ui.blobs[1].text(), /Define requirements/);
});

test('untrusted model text stays text and generated files can be downloaded', async () => {
  const unsafe = '<img src=x onerror=alert(1)>';
  const ui = setup({...result, mode:'openai', plan:[unsafe], files:[{path:'src/app.py',content:'print("hello")'}]});
  ui.get('#task').value = result.task;
  ui.get('input[name="mode"]:checked').value = 'openai';
  ui.get('#consent').checked = true;
  await ui.get('#task-form').listeners.submit({preventDefault(){}});
  assert.equal(ui.get('#result-body').children[0].children[1].children[0].textContent, unsafe);
  const file = ui.get('#result-body').children[4];
  assert.equal(file.children[1].children[0].textContent, 'print("hello")');
  file.children[0].children[1].click();
  assert.equal(await ui.blobs[0].text(), 'print("hello")');
});

test('AI usage confirmation and server errors are actionable', async () => {
  const ui = setup({error:'The AI service is unavailable.'}, false);
  ui.get('#task').value = result.task;
  ui.get('input[name="mode"]:checked').value = 'openai';
  await ui.get('#task-form').listeners.submit({preventDefault(){}});
  assert.match(ui.get('#error').textContent, /Confirm/);
  ui.get('#consent').checked = true;
  await ui.get('#task-form').listeners.submit({preventDefault(){}});
  assert.equal(ui.get('#error').textContent, 'The AI service is unavailable.');
  assert.equal(ui.get('#run').disabled, false);
});
