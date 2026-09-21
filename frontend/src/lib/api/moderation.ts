import { apiClient } from './client';
import { ModerationItem, ModerationMetrics, PaginatedResponse } from './types';

export interface FetchModerationParams {
  [key: string]: string | number | boolean | null | undefined;
  page?: number;
  page_size?: number;
}

export async function fetchModerationItems(
  params?: FetchModerationParams
): Promise<PaginatedResponse<ModerationItem>> {
  return apiClient<PaginatedResponse<ModerationItem>>('/api/v1/admin/moderation/', {
    params,
  });
}

export async function fetchModerationMetrics(): Promise<ModerationMetrics> {
  return apiClient<ModerationMetrics>('/api/v1/admin/moderation/metrics/');
}

export async function deleteModerationItem(propertyId: string): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/moderation/${propertyId}/delete/`, {
    method: 'POST',
  });
}
