// The merged app owns both public pages and the /admin route group.
// Next.js does not automatically add a basePath in this app.
export const BASE_PATH = '/admin';

export function adminPath(path: string): string {
  if (!path.startsWith('/') || path.startsWith('//')) return path;
  if (path === BASE_PATH || /^\/admin(?:\/|\?|#)/.test(path)) return path;
  return path === '/' ? BASE_PATH : `${BASE_PATH}${path}`;
}

// Dashboard navigation compares paths relative to its own root.
export function adminRelativePath(pathname: string): string {
  if (pathname === BASE_PATH) return '/';
  return pathname.startsWith(`${BASE_PATH}/`)
    ? pathname.slice(BASE_PATH.length)
    : pathname;
}
