import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { test } from 'node:test';
import { sumAvailableCounts } from '../src/lib/admin-dashboard.ts';
import { adminNavigation, activeAdminHref, findAdminSection, searchAdminNavigation } from '../src/lib/admin-navigation.ts';

const items = adminNavigation.flatMap((group) => group.items);
test('every grouped navigation destination has an existing page', () => {
  for (const item of items) {
    const route = item.href === '/' ? '' : item.href;
    assert.ok(existsSync(new URL(`../src/app/(admin)/admin${route}/page.tsx`, import.meta.url)), item.href);
  }
});
test('all existing main sections appear exactly once', () => {
  const expected = ['/', '/executive', '/analytics', '/properties', '/properties/review', '/users', '/kyc', '/users/suspended', '/moderation', '/users/reports', '/support', '/reports/overview', '/reports/chat-policy', '/financials', '/financials/transactions', '/notifications', '/roles', '/system/logs', '/system/health', '/settings'];
  assert.deepEqual(items.map((item) => item.href).sort(), expected.sort());
  assert.equal(new Set(items.map((item) => item.href)).size, expected.length);
  assert.equal(adminNavigation.length, 6);
});
test('detail and review pages select the most specific destination', () => {
  assert.equal(activeAdminHref('/properties/review'), '/properties/review');
  assert.equal(activeAdminHref('/properties/prop-123'), '/properties');
  assert.equal(activeAdminHref('/users/suspended'), '/users/suspended');
  assert.equal(activeAdminHref('/users/reports'), '/users/reports');
  assert.equal(activeAdminHref('/users/user-123'), '/users');
  assert.equal(activeAdminHref('/kyc/review'), '/kyc');
  assert.equal(activeAdminHref('/support/SUP-201'), '/support');
});
test('unknown and login routes do not masquerade as overview', () => {
  assert.equal(activeAdminHref('/login'), undefined);
  assert.equal(activeAdminHref('/userstuff'), undefined);
  assert.equal(activeAdminHref('/'), '/');
});
test('cross-cutting reports live with safety and support', () => {
  assert.equal(findAdminSection('/users/reports')?.id, 'trust');
  assert.equal(findAdminSection('/reports/chat-policy')?.id, 'trust');
  assert.equal(findAdminSection('/users/suspended')?.id, 'community');
});
test('Arabic search matches normalized spelling and descriptions', () => {
  assert.ok(searchAdminNavigation('الاشعارات').some((item) => item.href === '/notifications'));
  assert.ok(searchAdminNavigation('التوثيق').some((item) => item.href === '/kyc'));
  assert.equal(searchAdminNavigation('KYC')[0]?.href, '/kyc');
  assert.equal(searchAdminNavigation('لايوجدقسمبهذاالاسم').length, 0);
});

test('incomplete workload inputs never look like a complete total', () => {
  assert.equal(sumAvailableCounts([487, 234, undefined]), null);
  assert.equal(sumAvailableCounts([undefined, undefined, undefined]), null);
  assert.equal(sumAvailableCounts([487, null, 31]), null);
  assert.equal(sumAvailableCounts([0, 0, 0]), 0);
  assert.equal(sumAvailableCounts([487, 234, 31]), 752);
});
