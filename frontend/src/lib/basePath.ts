// Compatibility standalone dashboard. The merged app owns its own /admin routes.
export const BASE_PATH = '/admin';

// Next's standalone router already adds/removes its configured basePath.
export const adminPath = (path: string) => path;
export const adminRelativePath = (path: string) => path;

export const assetPath = (path: string) => path.startsWith(BASE_PATH) ? path : `${BASE_PATH}${path}`;
