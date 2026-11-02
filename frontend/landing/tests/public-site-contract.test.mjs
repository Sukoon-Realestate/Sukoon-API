import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, extname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Script } from 'node:vm';
import { test } from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ts from 'typescript';

// Use the existing node:test runner. Compile actual TSX modules in memory so
// these contract checks need neither a Next build nor a browser. Only build
// artifacts (CSS, images and next/font) are substituted; page, layout, routing,
// dictionaries, sections, header, footer and form implementations execute.
const project = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const cache = new Map();
function loadSource(filename) {
  if (cache.has(filename)) return cache.get(filename).exports;
  const compiledModule = { exports: {} };
  cache.set(filename, compiledModule);
  const native = createRequire(filename);
  const localRequire = (name) => {
    if (name === 'next/font/google') {
      return new Proxy({}, { get: (_, key) => key === '__esModule' ? false : () => ({ variable: 'test-font' }) });
    }
    if (name.endsWith('.css')) return {};
    if (/\.(png|jpg|webp|svg)$/.test(name)) return { src: '/test-asset.png', width: 200, height: 100 };
    if (name.startsWith('@/') || name.startsWith('.')) {
      const sourceRoot = filename.startsWith(resolve(project, '../src') + '/')
        ? resolve(project, '../src') : resolve(project, 'src');
      const base = name.startsWith('@/') ? resolve(sourceRoot, name.slice(2)) : resolve(dirname(filename), name);
      const path = [base, `${base}.ts`, `${base}.tsx`, `${base}.js`, resolve(base, 'index.ts')]
        .find((candidate) => existsSync(candidate) && extname(candidate));
      if (!path) throw new Error(`Cannot resolve ${name} from ${filename}`);
      if (/\.tsx?$/.test(path)) return loadSource(path);
      return native(path);
    }
    return native(name);
  };
  const { outputText } = ts.transpileModule(readFileSync(filename, 'utf8'), {
    fileName: filename,
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  });
  new Script(`(function(require,module,exports){${outputText}\n})`, { filename })
    .runInThisContext()(localRequire, compiledModule, compiledModule.exports);
  return compiledModule.exports;
}
const source = (path) => loadSource(resolve(project, 'src', path));
const page = source('app/(landing)/[lang]/page.tsx');
const layout = source('app/(landing)/[lang]/layout.tsx');
const { proxy } = source('proxy.ts');
const { NextRequest } = createRequire(import.meta.url)('next/server');
const { getDictionary } = source('i18n/dictionaries.ts');
const { TestSubscription } = source('components/sections/TestSubscription.tsx');
const { SiteFooter } = source('components/layout/SiteFooter.tsx');
const params = (lang) => ({ params: Promise.resolve({ lang }) });
const attrs = (tag) => Object.fromEntries([...tag.matchAll(/([\w-]+)="([^"]*)"/g)].map((m) => [m[1], m[2]]));
const tags = (html, name) => [...html.matchAll(new RegExp(`<${name}\\b[^>]*>`, 'g'))].map((m) => attrs(m[0]));
function withEnvironment(values, action) {
  const original = Object.fromEntries(Object.keys(values).map((key) => [key, process.env[key]]));
  try {
    for (const [key, value] of Object.entries(values)) {
      if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
    return action();
  } finally {
    for (const [key, value] of Object.entries(original)) {
      if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
  }
}

for (const [lang, direction, other] of [['ar', 'rtl', 'en'], ['en', 'ltr', 'ar']]) {
  test(`public ${lang} page and layout agree on language, direction, navigation and form`, async () => {
    const tree = await page.default(params(lang));
    const html = renderToStaticMarkup(tree);
    const document = await layout.default({ ...params(lang), children: tree });
    assert.equal(document.type, 'html');
    assert.equal(document.props.lang, lang);
    assert.equal(document.props.dir, direction);
    const links = tags(html, 'a');
    assert.ok(links.some((link) => link.href === `/${lang}`), 'home keeps current language');
    assert.ok(links.some((link) => link.href === `/${other}` && link.hrefLang === other && link.lang === other), 'language switch leads to the other public route');
    assert.ok(links.some((link) => link.href === '/admin'), 'admin destination stays unlocalized');
    const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]);
    assert.equal(new Set(ids).size, ids.length, 'public targets have unique IDs');
    const anchors = links.filter((link) => link.href?.startsWith('#'));
    assert.ok(anchors.length > 5);
    for (const link of anchors) assert.ok(ids.includes(link.href.slice(1)), `missing target ${link.href}`);
    const form = tags(html, 'form');
    assert.equal(form.length, 1);
    assert.equal(form[0].method, 'post');
    assert.equal(tags(html, 'input').find((input) => input.name === 'language')?.value, lang);
    assert.ok(!links.some((link) => /^(javascript:|http:|#$)/i.test(link.href ?? '')), 'no unsafe or fake navigation destination');
  });

  test(`public ${lang} metadata advertises only valid canonical and translated routes`, async () => {
    const metadata = await layout.generateMetadata(params(lang));
    assert.equal(metadata.alternates.canonical, `/${lang}`);
    assert.deepEqual(metadata.alternates.languages, { ar: '/ar', en: '/en', 'x-default': '/ar' });
    assert.ok(metadata.title && metadata.description);
    assert.equal(metadata.openGraph.url, `/${lang}`);
  });
}

test('only supported public locales are generated; unsupported input does not render a page', async () => {
  assert.deepEqual(layout.generateStaticParams(), [{ lang: 'ar' }, { lang: 'en' }]);
  assert.equal(layout.dynamicParams, false);
  for (const invalid of ['fr', 'AR', '', '../admin']) {
    await assert.rejects(page.default(params(invalid)), /NEXT_HTTP_ERROR_FALLBACK;404/);
    await assert.rejects(layout.default({ ...params(invalid), children: null }), /NEXT_HTTP_ERROR_FALLBACK;404/);
    assert.deepEqual(await layout.generateMetadata(params(invalid)), {});
  }
});

test('locale proxy preserves query parameters and never redirects API methods or admin paths', () => {
  for (const [header, locale] of [['en-US,en;q=0.9', 'en'], ['ar-EG', 'ar'], ['fr-FR', 'ar'], ['', 'ar']]) {
    const response = proxy(new NextRequest('https://sukoon.rent/?source=mail', { headers: { 'accept-language': header } }));
    assert.equal(response.status, 307);
    assert.equal(response.headers.get('location'), `https://sukoon.rent/${locale}?source=mail`);
  }
  for (const path of ['/api', '/api/v1/payments/paymob/test-checkout/', '/admin', '/admin/login', '/ar', '/en']) {
    const request = new NextRequest(`https://sukoon.rent${path}?keep=1`, { method: 'POST', body: 'original-body' });
    assert.equal(proxy(request), undefined, path);
    assert.equal(request.nextUrl.pathname, path);
    assert.equal(request.bodyUsed, false);
  }
});

test('test checkout form carries billing constraints and language without client-controlled price or provider credentials', () => {
  withEnvironment({ NEXT_PUBLIC_API_URL: 'https://isolated.example.test/' }, () => {
    for (const lang of ['ar', 'en']) {
      const html = renderToStaticMarkup(React.createElement(TestSubscription, { lang }));
      assert.equal(tags(html, 'form')[0].action, 'https://isolated.example.test/api/v1/payments/paymob/test-checkout/');
      const fields = Object.fromEntries(tags(html, 'input').map((field) => [field.name, field]));
      assert.deepEqual(Object.keys(fields).sort(), ['email', 'first_name', 'language', 'last_name', 'phone_number']);
      assert.equal(fields.language.value, lang);
      assert.equal(fields.email.type, 'email');
      assert.equal(fields.email.maxLength, '254');
      assert.equal(fields.first_name.maxLength, '100');
      assert.equal(fields.phone_number.type, 'tel');
      assert.equal(fields.phone_number.maxLength, '14');
      const phone = new RegExp(`^(?:${fields.phone_number.pattern})$`);
      for (const valid of ['+201012345678', '201012345678']) assert.ok(phone.test(valid), valid);
      for (const invalid of ['01012345678', '+1234', '+2010123456789', '']) assert.ok(!phone.test(invalid), invalid);
      for (const name of ['email', 'first_name', 'last_name', 'phone_number']) {
        assert.match(html, new RegExp(`<input(?=[^>]*name="${name}")(?=[^>]*required="")[^>]*>`));
      }
      assert.equal(tags(html, 'button').find((button) => button.type === 'submit')?.type, 'submit');
      assert.doesNotMatch(html, /sk_test_|sk_live_|clientSecret/);
    }
  });
});

test('unconfigured checkout origin uses the canonical API with one path separator', () => {
  withEnvironment({ NEXT_PUBLIC_API_URL: undefined }, () => {
    const html = renderToStaticMarkup(React.createElement(TestSubscription, { lang: 'ar' }));
    assert.equal(tags(html, 'form')[0].action, 'https://api.sukoon.rent/api/v1/payments/paymob/test-checkout/');
  });
});

test('footer exposes only configured HTTPS legal destinations and a real contact; unavailable links stay inert', () => {
  for (const lang of ['ar', 'en']) {
    const dict = getDictionary(lang);
    for (const invalid of [undefined, 'http://unsafe.test', 'javascript:alert(1)', '/privacy']) {
      withEnvironment({ NEXT_PUBLIC_PRIVACY_URL: invalid, NEXT_PUBLIC_TERMS_URL: invalid }, () => {
        const html = renderToStaticMarkup(React.createElement(SiteFooter, { dict }));
        const links = tags(html, 'a');
        assert.equal((html.match(/aria-disabled="true"/g) ?? []).length, 2);
        assert.ok(links.some((link) => link.href === 'mailto:info@sukoon.rent'));
        assert.ok(!links.some((link) => link.href === invalid));
      });
    }
    withEnvironment({ NEXT_PUBLIC_PRIVACY_URL: 'https://legal.example.test/privacy', NEXT_PUBLIC_TERMS_URL: 'https://legal.example.test/terms' }, () => {
      const links = tags(renderToStaticMarkup(React.createElement(SiteFooter, { dict })), 'a');
      assert.ok(links.some((link) => link.href === 'https://legal.example.test/privacy'));
      assert.ok(links.some((link) => link.href === 'https://legal.example.test/terms'));
      for (const link of links.filter((link) => link.target === '_blank')) {
        assert.ok(link.rel.split(' ').includes('noopener'));
        assert.ok(link.rel.split(' ').includes('noreferrer'));
      }
    });
  }
});
