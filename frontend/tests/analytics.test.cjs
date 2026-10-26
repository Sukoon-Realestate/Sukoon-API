const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

function load(file, modules) {
  const output = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React, esModuleInterop: true },
  }).outputText;
  const exports = {};
  vm.runInNewContext(output, { exports, require: id => {
    assert.ok(id in modules, `Unexpected dependency ${id}`);
    return modules[id];
  } });
  return exports;
}
const snapshot = () => ({
  period: { days: 7, from: '2026-10-19T12:00:00Z', through: '2026-10-26T12:00:00Z' },
  snapshot_measured_at: '2026-10-26T12:00:00Z', dailyChart: [], topRegions: [], kycBreakdown: [], propertyActivity: [],
});

test('analytics passes the cancellation signal and rejects data from another period', async () => {
  let response = snapshot();
  const controller = new AbortController();
  const { fetchAnalyticsStats } = load('src/lib/api/analytics.ts', { './client': { apiClient: async (path, options) => {
    assert.equal(path, '/api/v1/admin/analytics/');
    assert.equal(options.params.period, '7');
    assert.equal(options.signal, controller.signal);
    return response;
  } } });
  assert.equal(await fetchAnalyticsStats('7', controller.signal), response);
  for (const invalid of [null, {}, { ...snapshot(), period: { ...snapshot().period, days: 30 } },
    { ...snapshot(), snapshot_measured_at: 'unknown' }, { ...snapshot(), dailyChart: null }]) {
    response = invalid;
    await assert.rejects(fetchAnalyticsStats('7', controller.signal), /Invalid analytics response/);
  }
});

test('chart renders zero as zero height and uses actual labels, including an empty interval', () => {
  const { BarChartComponent } = load('src/components/ui/BarChartComponent.tsx', {
    react: React, 'lucide-react': require('lucide-react'),
  });
  const markup = renderToStaticMarkup(React.createElement(BarChartComponent, {
    title: 'Measured requests', data: [{ label: '2026-10-19', value: 0 }, { label: '2026-10-20', value: 2 }], periodLabel: '7 days',
  }));
  assert.match(markup, /height:0%/);
  assert.match(markup, /height:100%/);
  assert.match(markup, /aria-label="2026-10-19: 0"/);
  assert.match(markup, /2026-10-20/);
  assert.doesNotMatch(markup, /منذ 30 يوم/);
  const empty = renderToStaticMarkup(React.createElement(BarChartComponent, { title: 'Empty', data: [], periodLabel: '7 days' }));
  assert.doesNotMatch(empty, /NaN|Infinity|role="img"/);
  assert.match(empty, /الإجمالي: 0/);
});

test('administrative follow-ups accept only real nonnegative counts and known queue destinations', async () => {
  const row = { id: 'kyc', title: 'Pending identity reviews', count: 0, href: '/admin/kyc' };
  const result = { measured_at: '2026-10-26T12:00:00Z', results: [row] };
  let response = result;
  const { fetchAdminFollowups } = load('src/lib/api/followups.ts', { './client': { apiClient: async () => response } });
  assert.equal(await fetchAdminFollowups(), result);
  for (const invalid of [null, {}, { ...result, measured_at: 'unavailable' },
    ...[-1, 0.5, '4'].map(count => ({ ...result, results: [{ ...row, count }] })),
    ...['https://example.invalid', '//example.invalid', '/admin/users/fake-id', 'javascript:alert(1)'].map(href => ({ ...result, results: [{ ...row, href }] }))]) {
    response = invalid;
    await assert.rejects(fetchAdminFollowups(), /Invalid administrative follow-up response/);
  }
});
