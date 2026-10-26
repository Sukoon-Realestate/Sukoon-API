const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

function dialog(onConfirm) {
  const states = [], refs = [];
  let index = 0, refIndex = 0, closes = 0;
  const hooks = {
    useEffect: () => {},
    useState: value => { const key = index++; if (!(key in states)) states[key] = value; return [states[key], next => { states[key] = typeof next === 'function' ? next(states[key]) : next; }]; },
    useRef: value => refs[refIndex++] ?? (refs[refIndex - 1] = { current: value }),
  };
  const source = ts.transpileModule(fs.readFileSync('src/components/ui/ConfirmModal.tsx', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  const exports = {};
  vm.runInNewContext(source, { exports, require: id => id === 'react' ? hooks : require(id) });
  const props = { isOpen: true, title: 'Confirm a specific operation', onConfirm, onClose: () => { closes++; } };
  const render = () => { index = refIndex = 0; const child = exports.ConfirmModal(props); return child.type(child.props); };
  return { render, closes: () => closes, hidden: () => exports.ConfirmModal({ ...props, isOpen: false }) };
}
function elements(node) {
  if (!node || typeof node !== 'object') return [];
  return [node, ...[node.props?.children].flat(Infinity).flatMap(elements)];
}
const flush = () => new Promise(resolve => setImmediate(resolve));

test('confirmation stays pending and rapid repeated activation invokes the command once', async () => {
  let finish, calls = 0;
  const command = new Promise(resolve => { finish = resolve; });
  const d = dialog(() => { calls++; return command; });
  const initial = d.render();
  const button = elements(initial).find(e => e.type === 'button' && e.props.children === 'تأكيد الإجراء');
  button.props.onClick(); button.props.onClick();
  assert.equal(calls, 1);
  assert.equal(d.closes(), 0);
  const pending = d.render();
  assert.ok(elements(pending).filter(e => e.type === 'button').every(e => e.props.disabled));
  let prevented = false;
  pending.props.onCancel({ preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  finish(); await flush();
  assert.equal(d.closes(), 1);
  assert.equal(d.hidden(), null);
});

test('unconfirmed outcome remains visible without automatic retry or a success close', async () => {
  let calls = 0;
  const d = dialog(async () => { calls++; throw new Error('Response lost'); });
  elements(d.render()).find(e => e.type === 'button' && e.props.children === 'تأكيد الإجراء').props.onClick();
  await flush();
  assert.equal(calls, 1);
  assert.equal(d.closes(), 0);
  assert.equal(elements(d.render()).filter(e => e.props?.role === 'alert').length, 1);
});
