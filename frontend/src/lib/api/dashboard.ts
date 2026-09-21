import { apiClient } from './client';
import { DashboardStatsResponse } from './types';

export async function fetchDashboardStats(): Promise<DashboardStatsResponse> {
  return apiClient<DashboardStatsResponse>('/api/v1/admin/dashboard/');
}
