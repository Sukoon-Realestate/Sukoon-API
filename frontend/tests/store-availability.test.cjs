/* eslint-disable @typescript-eslint/no-require-imports -- Node CommonJS test harness. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function load(file, modules = {}) {
  const exports = {};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText, { exports, require: id => modules[id] ?? require(id) });
  return exports;
}
function elements(node) {
  if (!node || typeof node !== 'object') return [];
  return [node, ...[node.props?.children].flat(Infinity).flatMap(elements)];
}
for (const language of ['ar', 'en']) {
  test(`unconfigured store badges explain unavailable downloads in ${language}`, () => {
    const { getDictionary } = load('landing/src/i18n/dictionaries.ts', { './features': { featuresAr: {}, featuresEn: {} } });
    const dict = getDictionary(language);
    const { StoreButtons } = load('landing/src/components/ui/StoreButtons.tsx');
    const nodes = elements(StoreButtons({ dict }));
    const badges = nodes.filter(n => n.props?.['aria-disabled'] === true);
    assert.equal(badges.length, 2);
    assert.ok(badges.every(n => n.props['aria-label'].includes(dict.store.unavailable)));
    assert.ok(!dict.hero.badge.includes(language === 'en' ? 'Available on' : 'متاح على'));
    assert.ok(dict.faq.items.at(-1).answer.includes(dict.store.unavailable));
  });
}
