const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

function load(file, modules = {}) {
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
  telemetry: { state: 'no_samples', measured_at: 1793016000, window_seconds: 600,
    requests: 0, server_errors: 0, error_rate: null, average_ms: null,
    p95_upper_ms: null, p95_lower_ms: null, release_sha: 'local', routes: [],
    memory: { ratio: null, used_bytes: null, limit_bytes: null, scope: 'unknown' },
    runtime: null, queue: { state: 'unavailable', pending: null, oldest_seconds: null } },
  metrics: { uptime: 'Unavailable', uptimeSub: 'No long-term uptime measurement',
    responseTime: 'Unavailable', responseSub: 'Observed window: 600 seconds',
    errorsToday: '0', errorsSub: '5xx errors in the measured window; not a daily total',
    dbStatus: 'Reachable', dbSub: '2026-10-26T12:00:00Z' },
  incidents: [], auditLogs: [], apiPerformanceData: [], internalAdminNotes: [],
});
const validation = load('src/lib/api/systemHealth.ts');

test('health distinguishes zero observations from unknown measurements and rejects malformed responses', async () => {
  let response = snapshot();
  const controller = new AbortController();
  const { fetchSystemHealth } = load('src/lib/api/system.ts', {
    './systemHealth': validation, './client': { apiClient: async (path, options) => {
      assert.equal(path, '/api/v1/admin/system/health/');
      assert.equal(options.signal, controller.signal);
      return response;
    } },
  });
  assert.equal(await fetchSystemHealth(controller.signal), response);
  response.telemetry.requests = null;
  response.telemetry.server_errors = null;
  response.telemetry.state = 'unavailable';
  assert.equal(await fetchSystemHealth(controller.signal), response);
  const broken = [null, {}, { ...snapshot(), telemetry: undefined },
    { ...snapshot(), metrics: { ...snapshot().metrics, dbSub: 'unknown' } },
    ...[NaN, Infinity, -1, '0', 0.5].map(requests => ({ ...snapshot(), telemetry: { ...snapshot().telemetry, requests } })),
    { ...snapshot(), telemetry: { ...snapshot().telemetry, memory: null } },
    { ...snapshot(), telemetry: { ...snapshot().telemetry, runtime: { failures: null } } },
    { ...snapshot(), telemetry: { ...snapshot().telemetry, queue: { state: 'measured', pending: -1 } } },
    { ...snapshot(), telemetry: { ...snapshot().telemetry, routes: [{ route: 'GET /', requests: 1, errors: 0, duration_ms: -9 }] } },
    { ...snapshot(), incidents: [{ code: 'runtime.queue_delay', state: 'healthy', occurrences: 1 }] },
    { ...snapshot(), auditLogs: [{ id: 'actual', action: { title: 'bad' } }] },
  ];
  for (const value of broken) {
    response = value;
    await assert.rejects(fetchSystemHealth(controller.signal), /Invalid system health response/);
  }
});

const { SystemHealthReadings } = load('src/components/system/SystemHealth.tsx', {
  react: React, '@/components/layout/Header': { Header: () => null },
  '../../lib/api/system': {}, '../../lib/api/client': { ApiError: Error },
});
const render = value => renderToStaticMarkup(React.createElement(SystemHealthReadings, { data: value }));

test('an empty recorded window has zero errors but no invented latency, uptime, queue or healthy workers', () => {
  const markup = render(snapshot());
  assert.match(markup, /أخطاء الخادم 5xx<\/dt><dd[^>]*>0<\/dd>/);
  assert.match(markup, /600 ثانية/);
  assert.match(markup, /عدد الطلبات<\/dt><dd>0<\/dd>/);
  assert.match(markup, /المهام المنتظرة<\/dt><dd>غير متاح/);
  assert.match(markup, /تشغيل العمال والجدولة: غير مؤكد/);
  assert.doesNotMatch(markup, /99\.8|142|الساعة الأخيرة|اليوم|NaN|Infinity|Invalid Date/);
});

test('overflow latency is a lower bound, route averages use counts, and open incidents survive unknown telemetry', () => {
  const value = snapshot();
  Object.assign(value.telemetry, { state: 'unavailable', requests: null, server_errors: null,
    p95_lower_ms: 60000, routes: [{ route: 'GET properties/<uuid:pk>/', requests: 2, errors: 0, duration_ms: 300 }] });
  value.incidents = [{ code: 'runtime.api_latency', state: 'open', occurrences: 2,
    opened_at: '2026-10-26T12:00:00Z', resolved_at: null }];
  const markup = render(value);
  assert.match(markup, /يتجاوز ٦٠٬٠٠٠ مللي ثانية/);
  assert.match(markup, /متوسط الاستجابة: ١٥٠ مللي ثانية/);
  assert.match(markup, /زمن الاستجابة — مفتوح/);
  assert.match(markup, /مرات الحدوث: 2/);
  assert.match(markup, /أخطاء الخادم 5xx<\/dt><dd[^>]*>غير متاح<\/dd>/);
  assert.doesNotMatch(markup, /تمت الاستعادة/);
});
