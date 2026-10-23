import assert from 'node:assert/strict';
import { test } from 'node:test';
import { deploymentEnvironment } from './vercel-build.mjs';

test('production cannot inherit demo switches or a direct browser API origin', () => {
  const source = {
    VERCEL_ENV: 'production', NEXT_PUBLIC_ENABLE_BACKEND: 'false',
    NEXT_PUBLIC_USE_MOCK_DATA: 'true', NEXT_PUBLIC_API_URL: 'https://old.invalid',
  };
  const result = deploymentEnvironment(source);
  assert.equal(result.NEXT_PUBLIC_ENABLE_BACKEND, 'true');
  assert.equal(result.NEXT_PUBLIC_USE_MOCK_DATA, 'false');
  assert.equal(result.NEXT_PUBLIC_API_URL, '');
  assert.equal(result.SOKOUN_API_PROXY_URL, 'https://sukoon-app-y4j5r.ondigitalocean.app');
  assert.equal(source.NEXT_PUBLIC_ENABLE_BACKEND, 'false');
});

test('an explicit production server origin remains authoritative', () => {
  const result = deploymentEnvironment({ VERCEL_ENV: 'production', SOKOUN_API_PROXY_URL: 'https://api.example.test' });
  assert.equal(result.SOKOUN_API_PROXY_URL, 'https://api.example.test');
});

test('preview and local builds retain their isolated configuration', () => {
  for (const environment of ['preview', 'development', undefined]) {
    const source = { VERCEL_ENV: environment, NEXT_PUBLIC_USE_MOCK_DATA: 'true', SOKOUN_API_PROXY_URL: 'http://127.0.0.1:8048' };
    assert.deepEqual(deploymentEnvironment(source), source);
  }
});
