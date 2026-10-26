import { apiClient } from './client';
import type { AnalyticsPeriod, AnalyticsStats } from './types';

export async function fetchAnalyticsStats(period: AnalyticsPeriod = '30', signal?: AbortSignal): Promise<AnalyticsStats> {
  const data = await apiClient<AnalyticsStats>('/api/v1/admin/analytics/', {
    params: { period }, signal,
  });
  if (!data || data.period?.days !== Number(period) ||
      !Number.isFinite(Date.parse(data.period.from)) || !Number.isFinite(Date.parse(data.period.through)) ||
      !Number.isFinite(Date.parse(data.snapshot_measured_at)) ||
      ![data.dailyChart, data.topRegions, data.kycBreakdown, data.propertyActivity].every(Array.isArray)) {
    throw new Error('Invalid analytics response');
  }
  return data;
}
