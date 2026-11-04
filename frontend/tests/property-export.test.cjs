const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

function load(read) {
  const blobs = [], anchors = [], revoked = [], timers = [], calls = [];
  const source = ts.transpileModule(fs.readFileSync('src/lib/api/properties.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS },
  }).outputText;
  const exports = {};
  vm.runInNewContext(source, { exports, Blob, encodeURIComponent,
    require: name => {
      assert.equal(name, './client');
      return { apiClient: async (...args) => { calls.push(args); return read(...args); } };
    },
    URL: { createObjectURL(blob) { blobs.push(blob); return 'blob:local-export'; },
      revokeObjectURL(url) { revoked.push(url); } },
    document: { createElement(tag) {
      assert.equal(tag, 'a'); const anchor = { click() { anchors.push(this); } }; return anchor;
    } },
    setTimeout(callback, delay) { timers.push({ callback, delay }); },
  });
  return { ...exports, blobs, anchors, revoked, timers, calls };
}

test('property export rechecks the exact resource and downloads its actual JSON', async () => {
  const record = { id: 'property-a', title: 'Synthetic', status: 'pending', revision: 7 };
  const api = load(async () => record);
  await api.exportProperty(record.id);
  assert.equal(api.calls.length, 1);
  assert.equal(api.calls[0][0], '/api/v1/admin/properties/property-a/');
  assert.equal(api.anchors[0].download, 'property-property-a.json');
  assert.deepEqual(JSON.parse(await api.blobs[0].text()), record);
  assert.equal(api.blobs[0].type, 'application/json;charset=utf-8');
  assert.equal(api.timers[0].delay, 1000);
  api.timers[0].callback();
  assert.deepEqual(api.revoked, ['blob:local-export']);
});

for (const failure of ['forbidden', 'missing', 'wrong-identity']) {
  test(`property export never creates a file after ${failure}`, async () => {
    const api = load(async () => {
      if (failure === 'wrong-identity') return { id: 'another-property' };
      throw new Error(failure);
    });
    await assert.rejects(api.exportProperty('property-a'));
    assert.equal(api.calls.length, 1);
    assert.equal(api.blobs.length, 0);
    assert.equal(api.anchors.length, 0);
  });
}
