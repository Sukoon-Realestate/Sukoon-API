import { readFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, extname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Script } from 'node:vm';
import ts from 'typescript';

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
export const source = (path) => loadSource(resolve(project, 'src', path));
