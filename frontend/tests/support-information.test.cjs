const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

function load(file, modules) {
  const source = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  const exports = {};
  vm.runInNewContext(source, { exports, require: id => modules[id] ?? require(id), URL, Date });
  return exports;
}
function elements(node) {
  if (!node || typeof node !== 'object') return [];
  return [node, ...[node.props?.children].flat(Infinity).flatMap(elements)];
}
function panel(status, disabled = false, evidence = false) {
  const states = []; let index = 0; const calls = [];
  const hooks = { useState: initial => {
    const key = index++; if (!(key in states)) states[key] = initial;
    return [states[key], value => { states[key] = value; }];
  } };
  const module = load('src/components/support/SupportInformationPanel.tsx', { react: hooks });
  const render = () => {
    index = 0;
    return elements(module.default({ requests: [{ id: 'request-one', revision: 4, prompt: 'Which entrance?', status,
      answer_message_id: 'answer-one', history: [], evidence_requirement: evidence ? { min_attachments: 1 } : {},
      evidence_versions: evidence ? [{ id: 'version-one', version: 1, review_status: 'submitted', review_reason: '', files: [{ id: 'file-one', available: true }] }] : [] }], actions: { request_information: true, accept_information: true,
      return_information: true, withdraw_information: true, request_evidence: true, mark_evidence_conflicting: true }, disabled,
      onCommand: async (action, fields) => calls.push({ action, fields }) }));
  };
  return { render, calls };
}

test('support answer remains pending until an explicit authorized acceptance', async () => {
  const p = panel('answer_sent'); const nodes = p.render();
  assert.equal(p.calls.length, 0);
  assert.ok(nodes.some(node => node.props?.role === 'status' && node.props.children.includes('تنتظر')));
  const accept = nodes.find(node => node.type === 'button' && node.props.children === 'قبول الإجابة');
  await accept.props.onClick();
  assert.equal(p.calls[0].action, 'accept_information');
  assert.equal(p.calls[0].fields.information_request_id, 'request-one');
  assert.equal(p.calls[0].fields.information_revision, 4);
});

test('withdrawn requests offer no answer review and uncertain commands disable writes', () => {
  const withdrawn = panel('withdrawn').render();
  assert.ok(!withdrawn.some(node => node.type === 'button' && ['قبول الإجابة', 'طلب تصحيح الإجابة', 'سحب الطلب'].includes(node.props.children)));
  const busy = panel('answer_sent', true).render();
  assert.ok(busy.filter(node => node.type === 'button').every(node => node.props.disabled));
});

test('staff request is explicit and the API retains its original recovery identity', async () => {
  const p = panel('requested'); let nodes = p.render();
  const prompt = nodes.find(node => node.type === 'textarea' && node.props.maxLength === 2000);
  prompt.props.onChange({ target: { value: 'Please name the entrance.' } }); nodes = p.render();
  await nodes.find(node => node.type === 'button' && node.props.children === 'إرسال طلب المعلومات').props.onClick();
  assert.equal(p.calls[0].fields.prompt, 'Please name the entrance.');
  const requests = [];
  const api = load('src/lib/api/support.ts', { './client': { apiClient: async (path, options) => { requests.push({ path, options }); return {}; } }, './config': { API_BASE_URL: 'https://isolated.invalid' } });
  await api.commandSupport('ticket-one', { action: 'request_information', expected_revision: 3, reason: 'Follow-up', prompt: 'Which entrance?' }, 'original-key');
  await api.recoverSupport('ticket-one', 'original-key', 'request_information');
  assert.equal(requests[0].options.headers['Idempotency-Key'], 'original-key');
  assert.ok(requests[1].path.includes('original-key'));
  assert.equal(requests[1].options.params.action, 'request_information');
});

test('conflicting evidence is reviewed explicitly without deleting the submitted version', async () => {
  const p = panel('answer_sent', false, true);
  let nodes = p.render();
  nodes.find(node => node.type === 'textarea' && node.props.maxLength === 1000).props.onChange({ target: { value: 'Please correct the entrance.' } });
  nodes = p.render();
  await nodes.find(node => node.type === 'button' && node.props.children === 'تسجيل تعارض مع الاحتفاظ بالنسخ').props.onClick();
  assert.equal(p.calls[0].action, 'mark_evidence_conflicting');
  assert.equal(p.calls[0].fields.information_revision, 4);
  assert.ok(p.render().some(node => node.type === 'div' && node.key === 'version-one'));
});
