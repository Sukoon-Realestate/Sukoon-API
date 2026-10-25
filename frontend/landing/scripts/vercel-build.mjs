import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { prepareDesignDocs } from './prepare-design-docs.mjs';

const require = createRequire(import.meta.url);

// NEXT_PUBLIC_* values are frozen during next build. This existing production
// project serves the live dashboard; its preview builds stay independently scoped.
export function deploymentEnvironment(source) {
  if (source.VERCEL_ENV !== 'production') return { ...source };
  return {
    ...source,
    NEXT_PUBLIC_ENABLE_BACKEND: 'true',
    NEXT_PUBLIC_USE_MOCK_DATA: 'false',
    NEXT_PUBLIC_API_URL: '',
    SOKOUN_API_PROXY_URL:
      source.SOKOUN_API_PROXY_URL || 'https://sukoon-app-y4j5r.ondigitalocean.app',
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  prepareDesignDocs();
  const result = spawnSync(process.execPath, [require.resolve('next/dist/bin/next'), 'build'], {
    stdio: 'inherit',
    env: deploymentEnvironment(process.env),
  });
  if (result.error) throw result.error;
  process.exitCode = result.status ?? 1;
}
