import { apiClient } from './client';
import { DashboardStatsResponse, ExecutiveDashboardStats } from './types';

export async function fetchDashboardStats(signal?: AbortSignal): Promise<DashboardStatsResponse> {
  const result = await apiClient<DashboardStatsResponse>('/api/v1/admin/dashboard/', { signal });
  if (!result || !Number.isFinite(Date.parse(result.period?.measured_at)) ||
      !Number.isFinite(Date.parse(result.period?.from)) || !Number.isFinite(Date.parse(result.period?.through)) ||
      ![result.metrics, result.chart_data, result.recent_activities].every(Array.isArray) || !result.user_distribution) {
    throw new Error('Invalid dashboard response');
  }
  return result;
}

export async function fetchExecutiveDashboardStats(signal?: AbortSignal): Promise<ExecutiveDashboardStats> {
  const result = await apiClient<ExecutiveDashboardStats>('/api/v1/admin/dashboard/executive/', { signal });
  if (!result || !Number.isFinite(Date.parse(result.period?.measured_at)) ||
    ![result.executiveMetrics, result.monthlyUserChartData, result.reportTrendData, result.executiveActivities].every(Array.isArray) ||
    !result.userDistribution) throw new Error('Invalid executive dashboard response');
  return result;
}
