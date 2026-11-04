const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

function load(value) {
  const exports = {}, calls = [];
  const source = ts.transpileModule(fs.readFileSync('src/lib/api/system.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  vm.runInNewContext(source, { exports, require(name) {
    if (name === './client') return { apiClient: async (...args) => { calls.push(args); return value; } };
    if (name === './systemHealth') return {};
    throw new Error(`Unexpected import ${name}`);
  } });
  return { ...exports, calls };
}

test('campaign choices come from current server capability data', async () => {
  const api = load({ audiences: ['all', 'tenants', 'landlords', 'verified', 'all'] });
  assert.deepEqual(Array.from(await api.fetchCampaignAudiences()), ['all', 'tenants', 'landlords', 'verified']);
  assert.equal(api.calls[0][0], '/api/v1/admin/system/notifications/');
  assert.equal(api.calls[0][1].params.capabilities, '1');
});

for (const value of [null, {}, { audiences: [] }, { audiences: ['invented'] }, { audiences: [1] }]) {
  test(`malformed campaign configuration fails closed: ${JSON.stringify(value)}`, async () => {
    await assert.rejects(load(value).fetchCampaignAudiences());
  });
}

test('full release can restore the server-authorized deferred audiences', async () => {
  const api = load({ audiences: ['all', 'students', 'companies'] });
  assert.deepEqual(Array.from(await api.fetchCampaignAudiences()), ['all', 'students', 'companies']);
});
