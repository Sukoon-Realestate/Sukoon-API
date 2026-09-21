import { apiClient } from './client';
import { PlatformSettings } from './types';

export async function fetchPlatformSettings(): Promise<PlatformSettings> {
  return apiClient<PlatformSettings>('/api/v1/admin/settings/');
}

export async function updatePlatformSettings(settings: Partial<PlatformSettings>): Promise<PlatformSettings> {
  return apiClient<PlatformSettings>('/api/v1/admin/settings/', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}
