import assert from 'node:assert/strict';
import { test } from 'node:test';
import { adminPath, adminRelativePath } from '../src/lib/basePath.ts';

for (const [input, expected] of [
  ['/', '/admin'],
  ['/login', '/admin/login'],
  ['/users', '/admin/users'],
  ['/users/user-123', '/admin/users/user-123'],
  ['/properties/review?id=prop-123#photos', '/admin/properties/review?id=prop-123#photos'],
  ['/reports/overview', '/admin/reports/overview'],
  ['/admin', '/admin'],
  ['/admin/users', '/admin/users'],
  ['/admin?tab=overview', '/admin?tab=overview'],
  ['/admin#activity', '/admin#activity'],
  ['/administrator', '/admin/administrator'],
  ['#forgot', '#forgot'],
  ['https://example.com/help', 'https://example.com/help'],
  ['//example.com/help', '//example.com/help'],
  ['mailto:support@example.com', 'mailto:support@example.com'],
]) {
  test(`dashboard destination: ${input}`, () => {
    assert.equal(adminPath(input), expected);
  });
}

for (const [input, expected] of [
  ['/admin', '/'],
  ['/admin/', '/'],
  ['/admin/login', '/login'],
  ['/admin/users/user-123', '/users/user-123'],
  ['/administrator', '/administrator'],
  ['/ar', '/ar'],
]) {
  test(`dashboard route matching: ${input}`, () => {
    assert.equal(adminRelativePath(input), expected);
  });
}
