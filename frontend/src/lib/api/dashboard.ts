import { apiClient } from './client';
import { DashboardStatsResponse, ExecutiveDashboardStats } from './types';

export async function fetchDashboardStats(): Promise<DashboardStatsResponse> {
  return apiClient<DashboardStatsResponse>('/api/v1/admin/dashboard/');
}

export async function fetchExecutiveDashboardStats(): Promise<ExecutiveDashboardStats> {
  return apiClient<ExecutiveDashboardStats>('/api/v1/admin/dashboard/executive/');
}
