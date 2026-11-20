'use strict';
const $ = selector => document.querySelector(selector);
const task = $('#task');
let lastResult = null;
let busy = false;

function updateCount() { $('#character-count').textContent = `${task.value.length.toLocaleString()} / 4,000`; }
task.addEventListener('input', updateCount);
document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
  if (busy) return;
  task.value = button.dataset.example;
  updateCount(); task.focus();
}));
document.querySelectorAll('input[name="mode"]').forEach(input => input.addEventListener('change', () => {
  const ai = input.value === 'openai';
  $('#ai-consent').hidden = !ai;
  $('#consent').checked = false;
  $('#mode-note').textContent = ai ? 'AI mode makes up to three API requests. Results are generated for your task.' : 'Demo mode does not generate code or contact an AI service.';
}));

fetch('/api/config').then(response => {
  if (!response.ok) throw new Error();
  return response.json();
}).then(config => {
  $('#ai-mode').disabled = !config.openai;
  if (config.openai) $('#setup-note').textContent = 'AI mode is configured. Choose it when you want task-specific output. Your API key stays on this computer’s backend.';
}).catch(() => { $('#setup-note').textContent = 'Could not read server configuration. Restart the local server or reload this page.'; });

function download(name, content, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement('a');
  link.href = url; link.download = name;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function section(title, items) {
  const box = document.createElement('section'); box.className = 'result-section';
  const heading = document.createElement('h3'); heading.textContent = title;
  const list = document.createElement('ol');
  items.forEach(text => { const li = document.createElement('li'); li.textContent = text; list.append(li); });
  box.append(heading, list); return box;
}
function render(result) {
  $('#result-mode').textContent = result.mode === 'openai' ? 'AI-GENERATED RESULT' : 'DEMO RESULT · PREDEFINED NOTES';
  $('#result-task').textContent = result.task;
  $('#result-disclaimer').textContent = result.mode === 'openai' ? 'Review generated code and run the suggested tests. This app has not executed or verified the scaffold.' : 'This is a workflow demonstration. Notes are predefined; no AI was called and no code was generated.';
  const body = $('#result-body'); body.replaceChildren();
  body.append(section('Plan', result.plan), section('Architecture', result.architecture), section('Implementation notes', result.implementation_notes), section('Test plan', result.test_plan));
  result.files.forEach(file => {
    const box = document.createElement('section'); box.className = 'result-section';
    const heading = document.createElement('div'); heading.className = 'file-heading';
    const name = document.createElement('span'); name.textContent = file.path;
    const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Download file';
    button.addEventListener('click', () => download(file.path.replaceAll('/', '_'), file.content, 'text/plain;charset=utf-8'));
    const pre = document.createElement('pre'); const code = document.createElement('code'); code.textContent = file.content; pre.append(code);
    heading.append(name, button); box.append(heading, pre); body.append(box);
  });
  $('#results').hidden = false;
}
$('#task-form').addEventListener('submit', async event => {
  event.preventDefault(); if (busy) return;
  const mode = document.querySelector('input[name="mode"]:checked').value;
  const error = $('#error'); error.hidden = true;
  if (!task.value.trim()) { error.textContent = 'Please describe what you want to build.'; error.hidden = false; return; }
  if (mode === 'openai' && !$('#consent').checked) { error.textContent = 'Confirm the AI usage notice before running AI mode.'; error.hidden = false; return; }
  busy = true; $('#run').disabled = true; $('#run').textContent = 'Working…';
  $('#results').hidden = true; lastResult = null;
  $('.workflow-panel').classList.add('busy');
  document.querySelectorAll('.stage-state').forEach(el => { el.textContent = 'Queued'; });
  $('#status').textContent = mode === 'openai' ? 'Running Planner, Architect and Coder. This can take a couple of minutes.' : 'Running the demo workflow…';
  try {
    const response = await fetch('/api/workflow', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ task: task.value, mode }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'The workflow could not finish.');
    lastResult = result; render(result);
    document.querySelectorAll('.stage-state').forEach(el => { el.textContent = 'Done'; });
    $('#status').textContent = 'Workflow complete. Your results are ready below.';
    $('#results').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
  } catch (problem) {
    error.textContent = problem instanceof TypeError ? 'Could not reach the server. Check that it is still running.' : problem.message;
    error.hidden = false; $('#status').textContent = 'The workflow did not complete.';
    document.querySelectorAll('.stage-state').forEach(el => { el.textContent = 'Stopped'; });
  } finally {
    busy = false; $('#run').disabled = false; $('#run').textContent = 'Run workflow ＋';
    $('.workflow-panel').classList.remove('busy');
  }
});
$('#download-json').addEventListener('click', () => { if (lastResult) download('workflow-result.json', JSON.stringify(lastResult, null, 2), 'application/json'); });
$('#download-md').addEventListener('click', () => {
  if (!lastResult) return;
  const r = lastResult;
  let text = `# Software delivery workflow\n\nMode: ${r.mode}\n\n## Task\n${r.task}\n`;
  for (const [label, key] of [['Plan', 'plan'], ['Architecture', 'architecture'], ['Implementation notes', 'implementation_notes'], ['Test plan', 'test_plan']]) text += `\n## ${label}\n${r[key].map((line, i) => `${i + 1}. ${line}`).join('\n')}\n`;
  for (const file of r.files) {
    const fence = '`'.repeat(Math.max(3, ...((file.content.match(/`+/g) || []).map(run => run.length + 1))));
    text += `\n## File: ${file.path}\n\n${fence}\n${file.content}\n${fence}\n`;
  }
  download('workflow-result.md', text, 'text/markdown;charset=utf-8');
});
