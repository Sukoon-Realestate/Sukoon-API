const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const output = ts.transpileModule(fs.readFileSync('src/lib/admin-access.ts', 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
}).outputText;
const result = {};
vm.runInNewContext(output, { exports: result });
const { canOpenAdminPath } = result;

test('nested sections use their own server authority and never inherit from the dashboard root', () => {
  assert.equal(canOpenAdminPath(['/'], '/financials'), false);
  assert.equal(canOpenAdminPath(['/users'], '/users/reports'), false);
  assert.equal(canOpenAdminPath(['/users'], '/users/suspended'), false);
  assert.equal(canOpenAdminPath(['/users'], '/users/123'), true);
  assert.equal(canOpenAdminPath(['/users/reports'], '/users/reports?id=actual'), true);
  assert.equal(canOpenAdminPath(['/reports/overview'], '/reports'), true);
  assert.equal(canOpenAdminPath(['/properties'], '/properties/review'), false);
  assert.equal(canOpenAdminPath(['/properties/review'], '/properties/review?id=actual'), true);
});

test('independent recovery and missing authority expose no general administration', () => {
  assert.equal(canOpenAdminPath(['/security'], '/security'), true);
  for (const path of ['/', '/roles', '/financials', '/account-closure', '/support', '/unknown']) {
    assert.equal(canOpenAdminPath(['/security'], path), false);
    assert.equal(canOpenAdminPath(undefined, path), false);
  }
});
