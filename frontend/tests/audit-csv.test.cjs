const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function load({ clickFails = false } = {}) {
  const blobs = [], anchors = [], revoked = [], timers = [];
  const exports = {};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/lib/api/auditLogs.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2021 },
  }).outputText, { exports, Blob, Set, Number,
    URL: { createObjectURL(blob) { blobs.push(blob); return 'blob:audit'; }, revokeObjectURL(url) { revoked.push(url); } },
    document: { createElement() { const anchor = { click() { if (clickFails) throw new Error('download blocked'); anchors.push(this); } }; return anchor; } },
    setTimeout(callback, delay) { timers.push({ callback, delay }); },
  });
  return { ...exports, blobs, anchors, revoked, timers };
}
const row = { id: 'fixture-1', time: '2026-11-17', action: 'Accepted "quoted", text\nnext line', typeBadge: 'نظام', target: 'عقار', operator: 'Synthetic staff' };
const page = results => ({ results, count: results.length, page: 1, per_page: 10, total_pages: 1, next: null, previous: null });
test('CSV contains exact displayed fields, Arabic text, escaped delimiters and row identity', async () => {
  const m = load(); m.downloadAuditLogPage(page([row]));
  assert.equal(m.blobs.length, 1); assert.equal(m.blobs[0].type, 'text/csv;charset=utf-8');
  const bytes = new Uint8Array(await m.blobs[0].arrayBuffer()); assert.deepEqual([...bytes.slice(0, 3)], [239, 187, 191]);
  const csv = await m.blobs[0].text(); assert.match(csv, /"Accepted ""quoted"", text\nnext line"/);
  assert.match(csv, /"عقار"/); assert.match(csv, /"fixture-1"/); assert.ok(csv.endsWith('\r\n'));
  assert.equal(m.anchors[0].download, 'audit-logs-page-1.csv');
  assert.equal(m.timers[0].delay, 1000); m.timers[0].callback(); assert.deepEqual(m.revoked, ['blob:audit']);
});
for (const value of ['=SUM(1,2)', '+123', '-1+2', '@SUM(A1)', '  =1', '\t=1', '\r=1', '\n@x', '\u202e=1', '\u200b=1']) {
  test(`neutralizes spreadsheet formula/control prefix ${JSON.stringify(value)}`, async () => {
    const m = load(); m.downloadAuditLogPage(page([{ ...row, action: value }]));
    assert.ok((await m.blobs[0].text()).includes(`"'${value}"`));
  });
}
test('invalid/partial/empty pages never create a download', () => {
  const m = load();
  for (const data of [page([]), { results: [row] }, { ...page([row]), count: 12 }, page([{ ...row, action: null }]), page([row, row])]) {
    assert.throws(() => m.downloadAuditLogPage(data));
  }
  assert.equal(m.blobs.length, 0); assert.equal(m.anchors.length, 0);
});
test('download failures revoke their URL and propagate for visible feedback', () => {
  const m = load({ clickFails: true }); assert.throws(() => m.downloadAuditLogPage(page([row])), /blocked/);
  assert.deepEqual(m.revoked, ['blob:audit']); assert.equal(m.timers.length, 0);
});

test('explicit demo audit pages retain the live pagination contract', async () => {
  const exports = {};
  const fixtures = Array.from({ length: 16 }, (_, i) => ({ ...row, id: `demo-${i}` }));
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/lib/api/mockHandler.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2021 },
  }).outputText, { exports, require() { return { settingsData: {}, systemData: { health: { auditLogs: fixtures } } }; },
    setTimeout(callback) { callback(); }, URLSearchParams,
  });
  const validator = load();
  for (const pageNumber of [1, 2]) {
    const response = await exports.handleMockRequest('/api/v1/admin/system/logs/', { params: { page: pageNumber } });
    assert.doesNotThrow(() => validator.auditLogPage(response, pageNumber));
    assert.equal(response.results.length, pageNumber === 1 ? 10 : 6);
  }
});
