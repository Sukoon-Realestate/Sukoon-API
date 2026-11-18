const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const ts = require('typescript');

for (const file of ['next.config.ts', 'landing/next.config.ts']) {
  test(`${file}: admin documents prohibit framing in both application layouts`, async () => {
    const exports = {};
    const filename = path.resolve(file);
    vm.runInNewContext(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS },
    }).outputText, {
      exports, URL, __dirname: path.dirname(filename), process: { env: {} },
      require: name => name === './src/lib/basePath' ? { BASE_PATH: '/admin' } : require(name),
    });
    const config = exports.default;
    const rules = await config.headers();
    assert.equal(rules.length, 1);
    // Next automatically prefixes standalone rules with its /admin basePath.
    assert.equal((config.basePath || '') + rules[0].source, '/admin/:path*');
    const headers = Object.fromEntries(rules[0].headers.map(h => [h.key, h.value]));
    assert.equal(headers['Content-Security-Policy'], "frame-ancestors 'none'");
    assert.equal(headers['X-Frame-Options'], 'DENY');
    assert.equal(headers['X-Content-Type-Options'], 'nosniff');
  });
}
