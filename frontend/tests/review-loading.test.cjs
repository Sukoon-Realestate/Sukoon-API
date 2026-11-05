const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');

const flush = () => new Promise(resolve => setImmediate(resolve));
function mount(file, apiName, api) {
  const states = [], effects = [], refs = [], callbacks = [];
  let stateIndex, effectIndex, refIndex, callbackIndex, pending = [], unmounted = false, lateWrites = 0, dirty = false;
  const hooks = { ...React,
    useState(initial) {
      const i = stateIndex++;
      if (!(i in states)) states[i] = typeof initial === 'function' ? initial() : initial;
      return [states[i], value => {
        if (unmounted) { lateWrites++; return; }
        const next = typeof value === 'function' ? value(states[i]) : value;
        if (!Object.is(states[i], next)) dirty = true;
        states[i] = next;
      }];
    },
    useRef(initial) { const i = refIndex++; return refs[i] || (refs[i] = { current: initial }); },
    useCallback(callback, dependencies) {
      const i = callbackIndex++, old = callbacks[i];
      if (!old || dependencies.some((value, j) => !Object.is(value, old.dependencies[j]))) {
        callbacks[i] = { dependencies, callback };
      }
      return callbacks[i].callback;
    },
    useEffect(callback, dependencies) {
      const i = effectIndex++, old = effects[i];
      if (!old || dependencies.some((value, j) => !Object.is(value, old.dependencies[j]))) {
        pending.push(() => { old?.cleanup?.(); effects[i] = { dependencies, cleanup: callback() }; });
      }
    },
  };
  const modules = { react: hooks, [apiName]: api,
    '../layout/Header': { Header: () => null }, './TourPreviewButton': { TourPreviewButton: () => null },
    '../../lib/api/client': { ApiError: class extends Error {} },
  };
  const { outputText } = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React, esModuleInterop: true },
  });
  const exports = {};
  vm.runInNewContext(outputText, { exports, React: hooks, AbortController, require(name) {
    assert.ok(Object.hasOwn(modules, name), `Unexpected dependency ${name}`); return modules[name];
  } });
  const Component = exports.default || exports.StaffIdentitySetup;
  return {
    render() {
      // React commits state updates scheduled by effects before the next
      // settled observation. Preserve callback identity while doing so.
      for (let pass = 0; pass < 20; pass++) {
        dirty = false;
        stateIndex = effectIndex = refIndex = callbackIndex = 0;
        const tree = Component({ enabled: true });
        const queued = pending; pending = []; queued.forEach(effect => effect());
        if (!dirty) return tree;
      }
      throw new Error('Component effects did not settle');
    },
    unmount() { unmounted = true; effects.forEach(effect => effect.cleanup?.()); },
    lateWrites: () => lateWrites,
  };
}
function nodes(tree) {
  if (tree == null || typeof tree !== 'object') return [];
  if (Array.isArray(tree)) return tree.flatMap(nodes);
  return [tree, ...nodes(tree.props?.children)];
}
function readQueue() {
  const calls = [];
  return { calls, read(...args) { return new Promise((resolve, reject) => calls.push({ args, resolve, reject })); } };
}

test('staff identities load asynchronously and discard a response after unmount', async () => {
  const queue = readQueue();
  const page = mount('src/components/security/StaffIdentitySetup.tsx', '../../lib/api/security', { fetchStaffIdentities: queue.read });
  assert.ok(nodes(page.render()).some(node => node.props?.role === 'status'));
  assert.equal(queue.calls.length, 1);
  page.unmount();
  assert.equal(queue.calls[0].args[0].aborted, true);
  queue.calls[0].resolve({ results: [{ user_id: 'late', email: 'late@example.invalid' }] });
  await flush();
  assert.equal(page.lateWrites(), 0);
});

test('tour filter changes lock controls until the new server result and abort on unmount', async () => {
  const queue = readQueue();
  const page = mount('src/components/tours/TourReviewPage.tsx', '../../lib/api/tour-review', { reviewList: queue.read });
  let tree = page.render();
  assert.equal(nodes(tree).find(node => node.type === 'select').props.disabled, true);
  await flush();
  assert.deepEqual(queue.calls[0].args.slice(0, 2), ['pending', 1]);
  queue.calls[0].resolve({ items: [], count: 0, has_next: false });
  await flush();
  tree = page.render();
  const filter = nodes(tree).find(node => node.type === 'select');
  assert.equal(filter.props.disabled, false);
  filter.props.onChange({ target: { value: 'approved' } });
  tree = page.render();
  assert.equal(nodes(tree).find(node => node.type === 'select').props.disabled, true);
  await flush();
  assert.deepEqual(queue.calls[1].args.slice(0, 2), ['approved', 1]);
  page.unmount();
  assert.equal(queue.calls[1].args[2].aborted, true);
  queue.calls[1].reject(new Error('Cancelled response'));
  await flush();
  assert.equal(page.lateWrites(), 0);
});

test('tour unmount before its scheduled read starts makes no server request', async () => {
  const queue = readQueue();
  const page = mount('src/components/tours/TourReviewPage.tsx', '../../lib/api/tour-review', { reviewList: queue.read });
  page.render();
  page.unmount();
  await flush();
  assert.equal(queue.calls.length, 0);
  assert.equal(page.lateWrites(), 0);
});
