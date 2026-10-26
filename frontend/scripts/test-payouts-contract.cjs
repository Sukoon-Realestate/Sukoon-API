const assert = require('node:assert/strict');
const test = require('node:test');
const vm = require('node:vm');
const fs = require('node:fs');
const ts = require('typescript');
function load(live = true) {
  const calls = [];
  const output = ts.transpileModule(fs.readFileSync('src/lib/api/payouts.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;
  const context = { exports: {}, Intl, crypto: { randomUUID: () => 'new-operation' }, require: name => name === './config' ? { isBackendEnabled: () => live } : { apiClient: async (url, options) => { calls.push({ url, options }); if (url.endsWith('/preview/')) return { resource_id: 'lease', resource_revision: 7, masked_beneficiary: '4050', authorization_details: { amount_minor: 12345, currency: 'EGP', recipient_digest: 'reviewed-digest' } }; return { resource: { id: 'payout' } }; } } };
  vm.runInNewContext(output, context);
  return { api: context.exports, calls };
}
const plain = value => JSON.parse(JSON.stringify(value));
test('new approval uses reviewed amount, recipient, original payable and one request identity', async () => {
  const { api, calls } = load();
  const approval = await api.preparePayout({ id: 'payable' });
  await api.beginPayoutApproval(approval);
  await api.confirmPayoutApproval(approval, 'single-use-proof');
  assert.deepEqual(plain(calls[1].options.body), { action: 'payout.execute', resource_id: 'lease', resource_revision: 7, payload: { command: { request_key: 'new-operation', payable_ids: ['payable'] }, amount_minor: 12345, currency: 'EGP', recipient_digest: 'reviewed-digest' } });
  assert.equal(calls[2].options.headers['X-Sokoun-Authorization'], 'single-use-proof');
  assert.equal(calls[2].options.body.request_key, calls[1].options.body.payload.command.request_key);
  assert.match(calls[2].url, /payouts\/execute\/$/);
});
test('retry and unsent reauthorization bind different reviewed intents', async () => {
  for (const retry of [false, true]) {
    const { api, calls } = load();
    const review = { resource: { id: 'original', revision: 9, masked_beneficiary: '4050' }, authorization_details: { amount_minor: 12345, currency: 'EGP', instruction_reference: 'original-attempt', beneficiary_revision: 4, beneficiary_account_digest: 'same-account', funding_digest: 'reviewed-funding' } };
    const approval = api.prepareReauthorization(review, retry);
    await api.beginPayoutApproval(approval); await api.confirmPayoutApproval(approval, 'new-proof');
    assert.equal(calls[0].options.body.payload.approval_kind, retry ? 'retry' : 'reauthorize');
    assert.equal(calls[0].options.body.payload.instruction_reference, 'original-attempt');
    assert.equal(calls[0].options.body.payload.beneficiary_revision, 4);
    assert.equal(calls[0].options.body.payload.funding_digest, 'reviewed-funding');
    assert.equal(calls[0].options.body.payload.command.expected_revision, 9);
    assert.ok(calls[1].url.endsWith(`/original/${retry ? 'retry' : 'reauthorize'}/`));
  }
});
test('original-outcome inquiry contains no beneficiary or execution command', async () => {
  const { api, calls } = load();
  await api.reconcilePayout('original');
  assert.match(calls[0].url, /original\/reconcile\/$/);
  assert.deepEqual(plain(calls[0].options.body), { request_key: 'new-operation' });
});
test('demo cannot manufacture financial approval or reconciliation', async () => {
  const { api, calls } = load(false);
  await assert.rejects(api.reconcilePayout('original'));
  await assert.rejects(api.fetchPayoutQueue(1));
  await assert.rejects(api.preparePayout({ id: 'payable' }));
  assert.equal(calls.length, 0);
});
