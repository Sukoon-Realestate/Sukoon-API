import { apiClient } from './client';
import { AnalyticsStats } from './types';

export async function fetchAnalyticsStats(period: '7' | '30' | '90' = '30'): Promise<AnalyticsStats> {
  return apiClient<AnalyticsStats>('/api/v1/admin/analytics/', {
    params: { period },
  });
}
