import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { extname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const source = fileURLToPath(new URL('../../../docs/design/mobile-identity-proposal/', import.meta.url));
const destination = fileURLToPath(new URL('../public/docs/design/mobile-identity-proposal/', import.meta.url));
const publishedExtensions = new Set(['.html', '.css', '.js', '.png', '.woff2', '.zip', '.md', '.json']);

export function prepareDesignDocs() {
  if (!existsSync(`${source}/index.html`)) {
    throw new Error('Mobile design proposal is missing from the deployment checkout.');
  }
  rmSync(destination, { recursive: true, force: true });
  mkdirSync(destination, { recursive: true });
  cpSync(source, destination, {
    recursive: true,
    filter: (path) => !extname(path) || publishedExtensions.has(extname(path)),
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  prepareDesignDocs();
}
