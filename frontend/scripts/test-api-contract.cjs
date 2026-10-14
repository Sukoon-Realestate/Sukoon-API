const assert = require('node:assert/strict');
const test = require('node:test');
const vm = require('node:vm');
const fs = require('node:fs');
const ts = require('typescript');

function clientFor(body, headers = {}, status = 200) {
  const output = ts.transpileModule(fs.readFileSync('src/lib/api/client.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const context = { exports: {}, URLSearchParams, FormData, Blob,
    fetch: async () => new Response(JSON.stringify(body), { status, headers }),
    require: name => name === './config'
      ? { isBackendEnabled: () => true, API_BASE_URL: 'https://local.invalid' }
      : { handleMockRequest: () => { throw new Error('Mock bypassed contract'); } },
  };
  vm.runInNewContext(output, context);
  return () => context.exports.apiClient('/invoices/');
}
const envelope = data => ({ message: 'Done.', data });
const page = { 'X-Page': '1', 'X-Per-Page': '20', 'X-Total-Count': '21', 'X-Total-Pages': '2', 'X-Next-Page': '2' };
test('object, list and null resources unwrap without invented metadata', async () => {
  for (const value of [{ id: 'one' }, [], null]) {
    assert.deepEqual(JSON.parse(JSON.stringify(await clientFor(envelope(value))())), value);
  }
});
test('paginated body and transport headers produce the dashboard page model', async () => {
  const value = await clientFor(envelope([{ id: 'one' }]), page)();
  assert.equal(value.count, 21);
  assert.equal(value.next, '?page=2');
  assert.equal(value.results[0].id, 'one');
});
test('partial, overflowing and inconsistent pagination cannot become a complete list', async () => {
  for (const headers of [
    { 'X-Total-Count': '21' }, { ...page, 'X-Page': '9007199254740993' },
    { ...page, 'X-Total-Pages': '3' }, { ...page, 'X-Next-Page': '1' },
  ]) await assert.rejects(clientFor(envelope([]), headers), /Invalid API pagination/);
});
test('legacy and scalar success payloads are rejected; failures retain server wording', async () => {
  for (const body of [{ data: {} }, { ...envelope({}), key: 'success' }, envelope(true)]) {
    await assert.rejects(clientFor(body), /Invalid API response/);
  }
  await assert.rejects(clientFor({ message: 'Review the current revision.', data: null }, {}, 409), /Review the current revision/);
});
