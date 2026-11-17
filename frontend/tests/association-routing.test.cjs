/* eslint-disable @typescript-eslint/no-require-imports -- Node CommonJS test harness. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const ts = require('typescript');

function config(origin) {
  const exports = {};
  const filename = path.resolve('landing/next.config.ts');
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS },
  }).outputText, {
    exports, require, URL, __dirname: path.dirname(filename),
    process: { env: { SOKOUN_API_PROXY_URL: origin } },
  });
  return exports.default;
}

test('public link host proxies both exact association paths without a redirect or added slash', async () => {
  const routes = await config('https://api.example.test/').rewrites();
  for (const name of ['assetlinks.json', 'apple-app-site-association']) {
    const source = `/.well-known/${name}`;
    assert.equal(routes.find(route => route.source === source)?.destination, `https://api.example.test${source}`);
  }
  assert.equal(routes.find(route => route.source === '/api/v1/:path*')?.destination, 'https://api.example.test/api/v1/:path*/');
});

test('association proxy preserves isolated and invalid-origin behavior', async () => {
  assert.equal((await config(undefined).rewrites()).length, 0);
  for (const origin of ['https://user:secret@example.test', 'https://example.test/api', 'file:///tmp/api']) {
    await assert.rejects(() => config(origin).rewrites(), /must be an HTTP/);
  }
});
