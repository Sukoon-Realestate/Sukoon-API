const assert = require('node:assert/strict');
const test = require('node:test');
const vm = require('node:vm');
const fs = require('node:fs');
const ts = require('typescript');
function load(live = true) {
  const calls = [];
  const output = ts.transpileModule(fs.readFileSync('src/lib/api/refunds.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;
  const context = { exports: {}, crypto: { randomUUID: () => 'review-key' }, require: name => name === './config' ? { isBackendEnabled: () => live } : { apiClient: async (url, options) => { calls.push({ url, options }); return {}; } } };
  vm.runInNewContext(output, context);
  return { api: context.exports, calls };
}
const plain = value => JSON.parse(JSON.stringify(value));
test('refund authorization binds original capture, amount, allocation and reviewed version', async () => {
  for (const kind of ['execute', 'reauthorize', 'retry']) {
    const { api, calls } = load();
    const review = { resource: { id: 'original-refund', revision: 7 }, instruction_id: 'failed-attempt', authorization_details: { amount_minor: 12345, currency: 'EGP', payment_attempt_id: 'original-capture', allocations: { rent: 12345, deposit: 0 } } };
    const approval = api.prepareRefund(review, kind);
    await api.beginRefundApproval(approval); await api.confirmRefundApproval(approval, 'single-use-proof');
    assert.deepEqual(plain(calls[0].options.body), { action: 'refund.execute', resource_id: 'original-refund', resource_revision: 7, payload: { command: { request_key: 'review-key', expected_revision: 7, ...(kind === 'retry' ? { failed_instruction_id: 'failed-attempt' } : {}) }, ...review.authorization_details, ...(kind !== 'execute' ? { approval_kind: kind } : {}) } });
    assert.equal(calls[1].options.headers['X-Sokoun-Authorization'], 'single-use-proof');
    assert.equal(calls[1].options.body, calls[0].options.body.payload.command);
    assert.ok(calls[1].url.endsWith(`/original-refund/${kind}/`));
  }
});
test('a candidate provider reference is only sent to original-result inquiry', async () => {
  const { api, calls } = load(); await api.reconcileRefund('original-refund', '123');
  assert.match(calls[0].url, /operations\/refunds\/original-refund\/reconcile\/$/);
  assert.deepEqual(plain(calls[0].options.body), { provider_transaction_id: '123' });
  await api.reconcileRefund('original-refund'); assert.deepEqual(plain(calls[1].options.body), {});
});
test('request review is versioned and remains separate from permission to send money', async () => {
  const { api, calls } = load(); await api.respondRefund({ resource: { id: 'r', revision: 2 } }, 'approve', 'original-key');
  assert.match(calls[0].url, /refund-requests\/r\/respond\/$/);
  assert.deepEqual(plain(calls[0].options.body), { action: 'approve', expected_revision: 2, request_key: 'original-key' });
});
test('demo mode cannot issue or invent refunds', async () => {
  const { api, calls } = load(false);
  await assert.rejects(api.fetchRefunds(1)); await assert.rejects(api.reconcileRefund('r')); assert.equal(calls.length, 0);
});

test('retry cannot be prepared without the exact failed attempt', () => { const { api } = load(); assert.throws(() => api.prepareRefund({ resource: { id: 'r', revision: 4 } }, 'retry')); });
