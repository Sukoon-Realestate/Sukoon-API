const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createRequire } = require('node:module');
const root = process.env.FRONTEND_ROOT || path.resolve(__dirname, '..');
const deps = createRequire(path.join(root, 'package.json'));
const ts = deps('typescript');
const React = deps('react');
const source = process.env.PAGE_SOURCE || path.join(root, 'src/components/admin/pages/financials/transactions/page.tsx');
const flush = async () => { await Promise.resolve(); await Promise.resolve(); };
function compile(file, modules, globals = {}) {
  const output = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React, esModuleInterop: true },
    reportDiagnostics: true,
  });
  assert.equal(output.diagnostics.filter(d => d.category === ts.DiagnosticCategory.Error).length, 0);
  const exports = {};
  vm.runInNewContext(output.outputText, { exports, require: id => {
    assert.ok(Object.hasOwn(modules, id), `Unexpected module ${id}`); return modules[id];
  }, ...globals });
  return exports;
}
const Pagination = compile(path.join(root, 'src/components/ui/Pagination.tsx'), {
  react: React, 'lucide-react': { ChevronLeft: () => null, ChevronRight: () => null },
}).Pagination;
function page(page = 1, count = 16) {
  return { page, per_page: 10, total_pages: Math.max(1, Math.ceil(count / 10)), count,
    next: page < Math.ceil(count / 10) ? `?page=${page + 1}` : null,
    previous: page > 1 ? `?page=${page - 1}` : null,
    results: Array.from({ length: Math.min(10, Math.max(0, count - (page - 1) * 10)) }, (_, i) => ({
      id: `txn-${(page - 1) * 10 + i + 1}`, description: 'Read-only transaction', landlord: 'Fixture owner', tenant: 'Fixture tenant', amount: '10 EGP', isPositive: true, status: 'مدفوع',
    })),
  };
}
function mount() {
  const states = [], refs = [], effects = [], timers = new Map(), calls = [];
  let stateIndex = 0, refIndex = 0, effectIndex = 0, timerId = 0, pendingEffects = [], unmounted = false, postUnmountWrites = 0;
  const hooks = { ...React,
    useState(initial) {
      const i = stateIndex++; if (!(i in states)) states[i] = typeof initial === 'function' ? initial() : initial;
      return [states[i], next => { if (unmounted) { postUnmountWrites++; return; } states[i] = typeof next === 'function' ? next(states[i]) : next; }];
    },
    useRef(initial) { const i = refIndex++; return refs[i] || (refs[i] = { current: initial }); },
    useEffect(effect, dependencies) {
      const i = effectIndex++, old = effects[i];
      if (!old || dependencies.some((d, j) => !Object.is(d, old.dependencies[j]))) {
        pendingEffects.push(() => { old?.cleanup?.(); effects[i] = { dependencies, cleanup: effect() }; });
      }
    },
  };
  const component = compile(source, {
    react: hooks, '@/components/ui/TableScroll': { TableScroll: ({ children }) => React.createElement('div', null, children) },
    '@/components/ui/Pagination': { Pagination }, '@/components/layout/Header': { Header: () => null },
    'lucide-react': { Search: () => null, FileSpreadsheet: () => null },
    '@/lib/api/financials': { fetchTransactions(params) { return new Promise((resolve, reject) => calls.push({ params: { ...params }, resolve, reject })); } },
  }, {
    setTimeout: fn => { timers.set(++timerId, fn); return timerId; }, clearTimeout: id => timers.delete(id),
    console: { error: () => {} },
  }).default;
  function expand(node) {
    if (node == null || typeof node !== 'object') return node;
    if (Array.isArray(node)) return node.map(expand);
    if (typeof node.type === 'function') return expand(node.type(node.props));
    return { ...node, props: { ...node.props, children: React.Children.toArray(node.props.children).map(expand) } };
  }
  function render() {
    stateIndex = refIndex = effectIndex = 0; pendingEffects = [];
    const tree = expand(component()); for (const effect of pendingEffects) effect(); return tree;
  }
  return { calls, render, timers, start: () => { const next = [...timers.values()]; timers.clear(); next.forEach(fn => fn()); },
    unmount: () => { unmounted = true; effects.forEach(e => e.cleanup?.()); }, postUnmountWrites: () => postUnmountWrites };
}
function nodes(node) {
  if (node == null || typeof node !== 'object') return [];
  if (Array.isArray(node)) return node.flatMap(nodes);
  return [node, ...nodes(node.props?.children)];
}
function text(node) {
  if (node == null || typeof node === 'boolean') return '';
  if (typeof node !== 'object') return String(node);
  if (Array.isArray(node)) return node.map(text).join('');
  return text(node.props?.children);
}
const button = (tree, label) => nodes(tree).find(n => n.type === 'button' && (n.props.title === label || n.props['aria-label'] === label || text(n) === label));
const rows = tree => nodes(tree).filter(n => n.type === 'tr' && nodes(n).some(x => x.type === 'td' && /^txn-/.test(text(x))));
async function loaded() { const m = mount(); m.render(); m.start(); m.calls[0].resolve(page()); await flush(); return m; }

test('server page 1 shows 10 then accessible next shows the remaining 6 of 16', async () => {
  const m = await loaded(); let tree = m.render(); assert.equal(rows(tree).length, 10);
  assert.ok(button(tree, 'الصفحة التالية'), 'Accessible next-page control is required after a successful ten-row page');
  assert.equal(button(tree, 'الصفحة السابقة').props.disabled, true);
  assert.match(text(tree), /إجمالي المعاملات: 16/);
  button(tree, 'الصفحة التالية').props.onClick(); tree = m.render(); assert.match(text(tree), /جاري تحميل/); m.start();
  assert.equal(m.calls[1].params.page, 2); m.calls[1].resolve(page(2)); await flush(); tree = m.render();
  assert.equal(rows(tree).length, 6); assert.match(text(tree), /txn-16/); assert.doesNotMatch(text(tree), /txn-1Read/);
  assert.equal(button(tree, 'الصفحة التالية').props.disabled, true);
  assert.equal(button(tree, 'الصفحة السابقة').props.disabled, false);
  assert.equal(button(tree, 'الصفحة 2').props['aria-current'], 'page');
  button(tree, 'الصفحة السابقة').props.onClick();m.render();m.start();assert.equal(m.calls[2].params.page,1);m.calls[2].resolve(page());await flush();assert.equal(rows(m.render()).length,10);
});

test('search and status atomically reset page while preserving the other filter', async () => {
  const m = await loaded(); let tree = m.render(); button(tree, 'الصفحة التالية').props.onClick();m.render();m.start();m.calls[1].resolve(page(2));await flush();tree=m.render();
  nodes(tree).find(n => n.type === 'input').props.onChange({ target: { value: ' txn-16 ' } });m.render();m.start();
  assert.deepEqual(m.calls[2].params, { status: 'all', search: 'txn-16', page: 1 });m.calls[2].resolve(page());await flush();tree=m.render();
  button(tree,'الصفحة التالية').props.onClick();m.render();m.start();assert.deepEqual(m.calls[3].params,{status:'all',search:'txn-16',page:2});m.calls[3].resolve(page(2));await flush();tree=m.render();
  button(tree,'مدفوع').props.onClick();m.render();m.start();assert.deepEqual(m.calls[4].params,{status:'paid',search:'txn-16',page:1});
  m.calls[4].resolve(page(1,1));await flush();tree=m.render();assert.equal(nodes(tree).find(n=>n.type==='input').props.value,' txn-16 ');assert.equal(button(tree,'مدفوع').props['aria-pressed'],true);
});

test('read failure is an alert, never a successful empty page, and retry reads the same page once', async () => {
  const m=await loaded();button(m.render(),'الصفحة التالية').props.onClick();m.render();m.start();m.calls[1].reject(new Error('Read failed'));await flush();let tree=m.render();
  assert.equal(nodes(tree).filter(n=>n.props.role==='alert').length,1);assert.doesNotMatch(text(tree),/لا توجد معاملات مطابقة/);assert.equal(rows(tree).length,0);assert.equal(m.calls.length,2);
  button(tree,'إعادة المحاولة').props.onClick();m.render();m.start();assert.deepEqual(m.calls[2].params,m.calls[1].params);
  m.calls[2].resolve(page(2));await flush();tree=m.render();assert.equal(rows(tree).length,6);assert.equal(nodes(tree).filter(n=>n.props.role==='alert').length,0);assert.equal(m.calls.length,3);
});

test('late old success cannot replace a new filter even before effect cleanup runs', async () => {
  const m=mount();let tree=m.render();m.start();nodes(tree).find(n=>n.type==='input').props.onChange({target:{value:'latest'}});
  m.calls[0].resolve(page());await flush();tree=m.render();assert.equal(rows(tree).length,0);m.start();m.calls[1].resolve(page(1,1));await flush();tree=m.render();assert.equal(rows(tree).length,1);assert.equal(m.calls[1].params.search,'latest');
});

test('late old rejection cannot clear the newer successful page', async () => {
  const m=mount();let tree=m.render();m.start();button(tree,'معلق').props.onClick();m.render();m.start();m.calls[1].resolve(page(1,1));await flush();m.calls[0].reject(new Error('Late old read'));await flush();tree=m.render();
  assert.equal(rows(tree).length,1);assert.equal(nodes(tree).filter(n=>n.props.role==='alert').length,0);
});

test('unmount discards a pending read without scheduling updates', async () => {
  const m=mount();m.render();m.start();m.unmount();m.calls[0].resolve(page());await flush();assert.equal(m.postUnmountWrites(),0);
});

test('missing or inconsistent pagination cannot silently become an empty success', async () => {
  for (const response of [[], {results:[]}, {...page(),page:2}, {...page(),count:9}, {...page(),next:null}, {...page(),results:[]}]) {
    const m=mount();m.render();m.start();m.calls[0].resolve(response);await flush();const tree=m.render();assert.equal(nodes(tree).filter(n=>n.props.role==='alert').length,1);assert.doesNotMatch(text(tree),/لا توجد معاملات مطابقة/);
  }
});

test('true zero-count metadata shows zero and no navigation or unwired export action', async () => {
  const m=mount();m.render();m.start();m.calls[0].resolve(page(1,0));await flush();const tree=m.render();assert.match(text(tree),/لا توجد معاملات مطابقة/);assert.match(text(tree),/إجمالي المعاملات: 0/);assert.equal(button(tree,'الصفحة التالية'),undefined);assert.equal(button(tree,'تصدير Excel'),undefined);
});
