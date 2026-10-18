// Executes the actual TypeScript modules with controlled transport/hooks.
// This is a local contract check, not a browser or deployed-provider test.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
function load(file, modules, globals = {}) {
  const output = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React, esModuleInterop: true },
  }).outputText;
  const exports = {};
  vm.runInNewContext(output, { exports, require: id => {
    if (!(id in modules)) throw new Error(`Unexpected dependency ${id}`);
    return modules[id];
  }, URLSearchParams, FormData, Blob, Event, console, ...globals }, { filename: file });
  return exports;
}
for (const root of ['src', 'landing/src']) {
  function client(fetch, live = true) {
    let mockCalls = 0;
    const module = load(path.join(root, 'lib/api/client.ts'), {
      './config': { isBackendEnabled: () => live, API_BASE_URL: 'https://test.invalid' },
      './mockHandler': { handleMockRequest: () => { mockCalls++; return { demo: true }; } },
      '../basePath': { BASE_PATH: root === 'src' ? '' : '/admin' },
    }, { fetch });
    return { api: module.apiClient, count: () => mockCalls };
  }
  test(`${root}: live failure cannot become a simulated command`, async () => {
    for (const fetch of [async () => { throw new Error('Disconnected'); },
      async () => new Response('{}', { status: 500 })]) {
      const c = client(fetch);
      await assert.rejects(c.api('/api/v1/admin/staff/invite/', { method: 'POST', body: { email: 'a@example.test' } }), /unknown|unconfirmed/);
      assert.equal(c.count(), 0);
    }
  });
  test(`${root}: malformed acknowledgment fails closed`, async () => {
    const c = client(async () => new Response(JSON.stringify({ success: true })));
    await assert.rejects(c.api('/api/v1/admin/staff/invite/', { method: 'POST' }), /Invalid API response/);
    assert.equal(c.count(), 0);
  });
  test(`${root}: demo routing requires explicit configuration`, async () => {
    const c = client(async () => { throw new Error('Must not contact live server'); }, false);
    assert.equal((await c.api('/demo')).demo, true);
    assert.equal(c.count(), 1);
  });
  function auth(api, live = true) {
    const states = [], refs = [];
    let stateIndex = 0, refIndex = 0;
    const storage = new Map();
    const react = {
      createContext: value => ({ Provider: 'provider', value }), useContext: c => c.value,
      useEffect: () => {},
      useRef: value => refs[refIndex++] ?? (refs[refIndex - 1] = { current: value }),
      useState: value => { const i = stateIndex++; if (!(i in states)) states[i] = value; return [states[i], v => { states[i] = v; }]; },
      createElement: (type, props) => ({ type, props }),
    };
    const module = load(path.join(root, 'context/AuthContext.tsx'), {
      react: { __esModule: true, default: react, ...react },
      'next/navigation': { useRouter: () => ({ push: () => {} }), usePathname: () => '/login' },
      '@/lib/api/client': { apiClient: api }, '@/lib/api/config': { isBackendEnabled: () => live },
      '@/lib/basePath': { adminPath: x => x, adminRelativePath: x => x },
    }, { localStorage: { getItem: k => storage.get(k), setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k) } });
    return { value: () => { stateIndex = refIndex = 0; return module.AuthProvider({ children: null }).props.value; }, storage };
  }
  test(`${root}: rejected password login never authenticates demo`, async () => {
    const a = auth(async () => { throw new Error('Rejected'); });
    assert.equal(await a.value().login('admin@example.test', 'bad'), false);
    a.value().loginDemo();
    assert.equal(a.value().isAuthenticated, false);
    assert.equal(a.storage.has('sukoon_access_token'), false);
  });
  test(`${root}: role comes from current server session, not email`, async () => {
    const a = auth(async endpoint => endpoint.includes('/auth/login/') ? { access: 'real-shaped-test-token' }
      : { id: 'support-id', name: 'Support', email: 'admin@example.test', role: 'support', canManageStaff: false });
    assert.equal(await a.value().login('admin@example.test', 'valid'), true);
    assert.equal(a.value().user.role, 'support');
    assert.equal(a.value().user.canManageStaff, false);
  });
  test(`${root}: logout discards a late login response`, async () => {
    let finish;
    const a = auth(endpoint => endpoint.includes('/auth/login/') ? new Promise(resolve => { finish = resolve; }) : Promise.resolve({}));
    const pending = a.value().login('admin@example.test', 'valid');
    await a.value().logout();
    finish({ access: 'late-test-token' });
    assert.equal(await pending, false);
    assert.equal(a.value().isAuthenticated, false);
    assert.equal(a.storage.has('sukoon_access_token'), false);
  });
}
