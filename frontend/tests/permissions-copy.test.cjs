const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
test('permissions matrix truthfully describes immutable server policy without interactive cells', () => {
  let state = 0;
  const exports = {};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/admin/pages/roles/page.tsx', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React, esModuleInterop: true },
  }).outputText, { exports, console, require(name) {
    if (name === 'react') return { ...React, useEffect() {}, useState(initial) {
      const index = state++; return [index === 3 ? [{ action: 'Read audits', systemOwner: true }] : initial, () => {}];
    } };
    if (name === '@/context/AuthContext') return { useAuth: () => ({ user: { role_name: 'system_owner' } }) };
    if (name === '@/components/ui/Toast') return { useToast: () => ({ showToast() {} }) };
    return {};
  } });
  function nodes(n) { return !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(nodes) : [n, ...nodes(n.props?.children)]; }
  function text(n) { return n == null || typeof n === 'boolean' ? '' : Array.isArray(n) ? n.map(text).join('') : typeof n === 'object' ? text(n.props?.children) : String(n); }
  const tree = exports.default(); assert.doesNotMatch(text(tree), /انقر للتعديل المباشر/); assert.match(text(tree), /للعرض فقط/);
  const cells = nodes(tree).filter(n => n.props?.['aria-label'] === 'Read-only server role rule');
  assert.equal(cells.length, 5); assert.ok(cells.every(n => !n.props.onClick && !n.props.className.includes('cursor-pointer')));
});
