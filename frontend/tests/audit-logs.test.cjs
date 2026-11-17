const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const flush = () => new Promise(resolve => setImmediate(resolve));
function compile(file, modules, globals = {}) {
  const exports = {};
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React, esModuleInterop: true, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  vm.runInNewContext(code, { exports, require: name => {
    assert.ok(Object.hasOwn(modules, name), `Unexpected module ${name}`); return modules[name];
  }, ...globals });
  return exports;
}
function nodes(node) {
  if (!node || typeof node !== 'object') return [];
  if (Array.isArray(node)) return node.flatMap(nodes);
  return [node, ...nodes(node.props?.children)];
}
function text(node) {
  if (node == null || typeof node === 'boolean') return '';
  if (Array.isArray(node)) return node.map(text).join('');
  return typeof node === 'object' ? text(node.props?.children) : String(node);
}
const button = (tree, label) => nodes(tree).find(n => n.type === 'button' && (n.props.title === label || n.props['aria-label'] === label || text(n).includes(label)));
function page(number = 1, count = 16) {
  return { page: number, per_page: 10, total_pages: Math.max(1, Math.ceil(count / 10)), count,
    next: number < Math.ceil(count / 10) ? `?page=${number + 1}` : null,
    previous: number > 1 ? `?page=${number - 1}` : null,
    results: Array.from({ length: Math.min(10, Math.max(0, count - (number - 1) * 10)) }, (_, i) => ({
      id: `audit-${(number - 1) * 10 + i + 1}`, time: '2026-11-17 10:00', action: `Action ${(number - 1) * 10 + i + 1}`,
      typeBadge: 'نظام', target: 'Synthetic record', operator: 'Synthetic staff',
    })),
  };
}
function mount() {
  const states = [], refs = [], effects = [], timers = new Map(), calls = [], exports = [];
  let si = 0, ri = 0, ei = 0, timerId = 0, pending = [], unmounted = false, lateWrites = 0;
  const hooks = { ...React,
    useState(initial) { const i = si++; if (!(i in states)) states[i] = typeof initial === 'function' ? initial() : initial;
      return [states[i], value => { if (unmounted) { lateWrites++; return; } states[i] = typeof value === 'function' ? value(states[i]) : value; }]; },
    useRef(initial) { const i = ri++; return refs[i] || (refs[i] = { current: initial }); },
    useEffect(effect, dependencies) { const i = ei++, old = effects[i];
      if (!old || dependencies.some((d, j) => !Object.is(d, old.dependencies[j]))) {
        pending.push(() => { old?.cleanup?.(); effects[i] = { dependencies, cleanup: effect() }; });
      }
    },
  };
  const pagination = compile('src/components/ui/Pagination.tsx', { react: React, 'lucide-react': { ChevronLeft: () => null, ChevronRight: () => null } }).Pagination;
  const helper = fs.existsSync('src/lib/api/auditLogs.ts') ? compile('src/lib/api/auditLogs.ts', {}, { Blob, URL, document: {} }) : {};
  const component = compile('src/components/admin/pages/system/logs/page.tsx', {
    react: hooks, '@/components/ui/TableScroll': { TableScroll: ({ children }) => React.createElement('div', null, children) },
    '@/components/layout/Header': { Header: () => null }, '@/components/ui/Pagination': { Pagination: pagination },
    'lucide-react': { Search: () => null, Download: () => null },
    '@/lib/api/system': { fetchAuditLogs(params) { return new Promise((resolve, reject) => calls.push({ params: { ...params }, resolve, reject })); } },
    '@/lib/api/auditLogs': { ...helper, downloadAuditLogPage(...args) { exports.push(args); } },
  }, { console: { error() {} }, AbortController,
    setTimeout(fn) { timers.set(++timerId, fn); return timerId; }, clearTimeout(id) { timers.delete(id); } }).default;
  function expand(node) {
    if (!node || typeof node !== 'object') return node;
    if (Array.isArray(node)) return node.map(expand);
    if (typeof node.type === 'function') return expand(node.type(node.props));
    return { ...node, props: { ...node.props, children: React.Children.toArray(node.props.children).map(expand) } };
  }
  return { calls, exports,
    render() { si = ri = ei = 0; pending = []; const tree = expand(component()); pending.forEach(effect => effect()); return tree; },
    start() { const list = [...timers.values()]; timers.clear(); list.forEach(fn => fn()); },
    unmount() { unmounted = true; effects.forEach(e => e.cleanup?.()); }, lateWrites: () => lateWrites,
  };
}
async function loaded(data = page()) { const m = mount(); m.render(); m.start(); m.calls[0].resolve(data); await flush(); return m; }

test('audit 503 has visible failure and retry, never a successful empty table', async () => {
  const m = mount(); m.render(); m.start(); m.calls[0].reject(new Error('HTTP 503')); await flush();
  let tree = m.render(); assert.ok(nodes(tree).some(n => n.props.role === 'alert'));
  assert.doesNotMatch(text(tree), /لا توجد سجلات مطابقة/);
  assert.equal(button(tree, 'CSV').props.disabled, true);
  button(tree, 'إعادة المحاولة').props.onClick(); m.render(); m.start();
  assert.equal(m.calls.length, 2); m.calls[1].resolve(page(1, 0)); await flush(); tree = m.render();
  assert.match(text(tree), /لا توجد سجلات مطابقة/); assert.ok(!nodes(tree).some(n => n.props.role === 'alert'));
});

test('populated audit pages remain reachable; CSV explicitly exports only the displayed successful page', async () => {
  const m = await loaded(); let tree = m.render();
  const csv = button(tree, 'CSV'); assert.equal(typeof csv.props.onClick, 'function'); assert.match(text(csv), /الصفحة/);
  csv.props.onClick(); assert.equal(m.exports.length, 1); assert.equal(m.exports[0][0].results.length, 10);
  button(tree, 'الصفحة التالية').props.onClick(); tree = m.render(); assert.equal(button(tree, 'CSV').props.disabled, true); m.start();
  assert.equal(m.calls[1].params.page, 2); m.calls[1].resolve(page(2)); await flush(); tree = m.render();
  assert.match(text(tree), /Action 16/); assert.doesNotMatch(text(tree), /Action 1Synthetic/);
  button(tree, 'CSV').props.onClick(); assert.equal(m.exports[1][0].page, 2); assert.equal(m.exports[1][0].results.length, 6);
});

test('filter change hides prior rows immediately and late responses cannot replace current results', async () => {
  const m = await loaded(); let tree = m.render();
  nodes(tree).find(n => n.type === 'input').props.onChange({ target: { value: 'old query' } }); tree = m.render();
  assert.doesNotMatch(text(tree), /Action 1/); assert.equal(button(tree, 'CSV').props.disabled, true); m.start();
  nodes(tree).find(n => n.type === 'input').props.onChange({ target: { value: 'current query' } }); m.render(); m.start();
  m.calls[2].resolve(page(1, 0)); await flush(); m.calls[1].resolve(page()); await flush(); tree = m.render();
  assert.match(text(tree), /لا توجد سجلات مطابقة/); assert.doesNotMatch(text(tree), /Action 1/);
  assert.equal(m.calls[2].params.page, 1);
});

test('late failed requests cannot write component state after unmount', async () => {
  const m = mount(); m.render(); m.start(); m.unmount(); m.calls[0].reject(new Error('late')); await flush();
  assert.equal(m.lateWrites(), 0);
});

test('malformed pagination is an error rather than a successful empty response', async () => {
  const m = await loaded({ results: [] }); const tree = m.render();
  assert.ok(nodes(tree).some(n => n.props.role === 'alert')); assert.doesNotMatch(text(tree), /لا توجد سجلات مطابقة/);
});
