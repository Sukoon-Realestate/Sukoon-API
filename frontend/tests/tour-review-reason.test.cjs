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
  vm.runInNewContext(source, { exports, crypto: { randomUUID: () => '50e6bbdf-795e-4141-9134-48fa4217b8e8' },
    require: name => modules[name] ?? require(name) });
  return exports;
}
function nodes(node) {
  if (!node || typeof node !== 'object') return [];
  return [node, ...[node.props?.children].flat(Infinity).flatMap(nodes)];
}

test('tour rejection API keeps owner correction separate from private review evidence', async () => {
  const calls = [];
  const api = load('src/lib/api/tour-review.ts', {
    './client': { apiClient: async (...args) => calls.push(args) },
  });
  await api.decideTour({ asset_kind: 'property', asset_id: 'property-one', tour_id: 'tour-one',
    id: 'revision-one', source_hash: 'current-source' }, 'rejected', 'Private evidence', 'original-key', 'Fix the bedroom image');
  assert.equal(calls[0][0], '/api/v1/admin/properties/property-one/virtual-tours/tour-one/revisions/revision-one/review-decisions/');
  assert.deepEqual(JSON.parse(JSON.stringify(calls[0][1])), { method: 'POST', headers: { 'Idempotency-Key': 'original-key' },
    body: { decision: 'rejected', reason: 'Private evidence', public_reason: 'Fix the bedroom image', expected_source_hash: 'current-source' } });
});

test('tour rejection editor preserves both reasons and the exact operation after uncertain delivery', async () => {
  const states = [], refs = [], calls = [];
  let index = 0, refIndex = 0;
  const initial = { id: 'revision-one', source_hash: 'current-source', can_review: true,
    title: 'Synthetic tour', review_state: 'pending', processing_state: 'ready', variants: [], history: [] };
  const api = { decideTour: async (...args) => { calls.push(args); if (calls.length === 1) throw new Error('Synthetic lost response'); },
    reviewDetail: async () => ({ ...initial, review_state: 'rejected', can_review: false }) };
  const module = load('src/components/tours/TourReviewPage.tsx', {
    react: { useState: value => { const i = index++; if (!(i in states)) states[i] = value;
      return [states[i], next => { states[i] = next; }]; }, useRef: value => {
      const i = refIndex++; return refs[i] ?? (refs[i] = { current: value }); } },
    '../../lib/api/tour-review': api, '../layout/Header': { Header: () => null },
    './TourPreviewButton': { TourPreviewButton: () => null }, '../../lib/api/client': { ApiError: class extends Error {} },
  });
  const render = () => { index = refIndex = 0; return nodes(module.ReviewEditor({ initial, onSaved: async () => {} })); };
  let tree = render();
  tree.find(n => n.type === 'textarea' && n.props.maxLength === 4000).props.onChange({ target: { value: 'Private evidence' } });
  tree.find(n => n.type === 'select').props.onChange({ target: { value: 'rejected' } });
  tree = render();
  const publicField = tree.find(n => n.type === 'textarea' && n.props.maxLength === 2000);
  assert.equal(publicField.props.required, true);
  publicField.props.onChange({ target: { value: 'Fix the bedroom image' } });
  tree = render();
  assert.equal(calls.length, 0);
  await tree.find(n => n.type === 'form').props.onSubmit({ preventDefault() {} });
  tree = render();
  assert.ok(tree.filter(n => n.type === 'textarea').every(n => n.props.disabled));
  assert.equal(tree.find(n => n.type === 'textarea' && n.props.maxLength === 2000).props.value, 'Fix the bedroom image');
  await tree.find(n => n.type === 'form').props.onSubmit({ preventDefault() {} });
  assert.equal(calls.length, 2);
  assert.equal(calls[0][1], 'rejected');
  assert.equal(calls[0][2], 'Private evidence');
  assert.equal(calls[0][4], 'Fix the bedroom image');
  assert.deepEqual(calls[1], calls[0]);
});
