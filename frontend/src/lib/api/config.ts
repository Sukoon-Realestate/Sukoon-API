/** Demo data requires an explicit configuration; live failures never use fixtures. */
export const FALLBACK_ENABLE_BACKEND = true;
export function isBackendEnabled(): boolean {
  const primary = process.env.NEXT_PUBLIC_ENABLE_BACKEND?.trim().toLowerCase();
  if (primary) return !['false', '0', 'no'].includes(primary);
  const demo = process.env.NEXT_PUBLIC_USE_MOCK_DATA?.trim().toLowerCase();
  return !demo || !['true', '1', 'yes'].includes(demo);
}
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
