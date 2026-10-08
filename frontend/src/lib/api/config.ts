/**
 * Sukoon API Configuration & Backend Feature Switch
 *
 * Environment variable switch:
 * - NEXT_PUBLIC_ENABLE_BACKEND: 'true' to connect to live backend API, 'false' for static dummy JSON data.
 * - NEXT_PUBLIC_USE_MOCK_DATA: 'false' to enable live backend, 'true' for mock data (alternative alias).
 *
 * Fallback value:
 * If the environment variable is not found / undefined / empty, it falls back to
 * `FALLBACK_ENABLE_BACKEND = false`, which enables the static dummy JSON data.
 */

// Fallback value when the .env var is not found (enables static dummy data by default)
export const FALLBACK_ENABLE_BACKEND = false;

export function isBackendEnabled(): boolean {
  // Read environment variable with fallback that enables static dummy data
  const rawEnv =
    typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_ENABLE_BACKEND !== undefined
      ? process.env.NEXT_PUBLIC_ENABLE_BACKEND
      : undefined;

  // Fallback: if .env var is not found or empty, fallback to false (enabling static data)
  if (rawEnv === undefined || rawEnv === null || rawEnv.trim() === '') {
    // Check alternative alias NEXT_PUBLIC_USE_MOCK_DATA if present
    const aliasEnv =
      typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_USE_MOCK_DATA !== undefined
        ? process.env.NEXT_PUBLIC_USE_MOCK_DATA
        : undefined;

    if (aliasEnv !== undefined && aliasEnv !== null && aliasEnv.trim() !== '') {
      const aliasVal = aliasEnv.trim().toLowerCase();
      return !(aliasVal === 'true' || aliasVal === '1' || aliasVal === 'yes');
    }

    // Default fallback value: enables static dummy data
    return FALLBACK_ENABLE_BACKEND;
  }

  const val = rawEnv.trim().toLowerCase();
  return val === 'true' || val === '1' || val === 'yes';
}

export const API_BASE_URL =
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) || 'http://localhost:8000';
