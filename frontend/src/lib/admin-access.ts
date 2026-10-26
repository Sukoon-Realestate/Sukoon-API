export const ADMIN_ROUTE_PATHS = [
  '/', '/executive', '/analytics', '/properties', '/properties/review', '/properties/tours', '/moderation',
  '/users', '/users/suspended', '/users/reports', '/kyc', '/support', '/reports/overview',
  '/reports/chat-policy', '/financials', '/financials/transactions', '/financials/payouts', '/financials/refunds', '/notifications',
  '/settings', '/system/health', '/system/logs', '/roles', '/security', '/account-closure',
] as const;

/** Presentation only. Every API read and command rechecks current server authority. */
export function canOpenAdminPath(allowed: readonly string[] | undefined, path: string): boolean {
  const pathname = path.split(/[?#]/)[0];
  if (pathname === '/reports') return allowed?.includes('/reports/overview') ?? false;
  const destination = [...ADMIN_ROUTE_PATHS]
    .filter(route => route === pathname || (route !== '/' && pathname.startsWith(`${route}/`)))
    .sort((a, b) => b.length - a.length)[0];
  return destination !== undefined && (allowed?.includes(destination) ?? false);
}
