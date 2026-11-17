const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

for (const verified of [false, true]) {
  test(`user without reputation has no invented score (verified=${verified})`, () => {
    let index = 0;
    const user = { id: 'new-user', name: 'New user', is_verified: verified, status: 'نشط', roles: [] };
    const hooks = { useState: () => [index++ === 0 ? user : false, () => {}], useEffect: () => {} };
    const source = ts.transpileModule(fs.readFileSync('src/components/admin/pages/users/[id]/page.tsx', 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
    }).outputText;
    const exports = {};
    vm.runInNewContext(source, { exports, require: id => {
      if (id === 'react') return hooks;
      if (id === 'next/navigation') return { useParams: () => ({ id: user.id }) };
      if (id === '@/components/ui/Toast') return { useToast: () => ({ showToast() {} }) };
      if (id.startsWith('@/') || id === 'lucide-react') return {};
      return require(id);
    }, AbortController, console });
    const page = exports.default();
    const tree = page.type(page.props);
    function texts(node) {
      if (Array.isArray(node)) return node.flatMap(texts);
      if (node && typeof node === 'object') return texts(node.props?.children);
      return typeof node === 'string' || typeof node === 'number' ? [String(node)] : [];
    }
    const content = texts(tree);
    assert.ok(!content.includes('5.0') && !content.includes('4.5'), 'verification must not manufacture reputation');
    assert.ok(content.includes('غير متاح'), 'missing authoritative reputation must be explicit');
  });
}
