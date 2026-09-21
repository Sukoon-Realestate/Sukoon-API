import { apiClient } from './client';
import { ReportItem, PaginatedResponse } from './types';

export interface FetchReportsParams {
  [key: string]: string | number | boolean | null | undefined;
  status?: string;
  automation_level?: string;
  reason_type?: string;
  page?: number;
  page_size?: number;
}

export async function fetchReports(params?: FetchReportsParams): Promise<PaginatedResponse<ReportItem>> {
  return apiClient<PaginatedResponse<ReportItem>>('/api/v1/admin/reports/', { params });
}

export async function takeReportAction(
  reportId: string,
  action: 'suspend_user' | 'ban_user' | 'dismiss' | 'mark_active',
  notes?: string
): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/reports/${reportId}/action/`, {
    method: 'POST',
    body: JSON.stringify({ action, notes }),
  });
}

export async function fetchReportMetrics(): Promise<{
  active: number;
  suspended: number;
  banned: number;
  dismissed: number;
  total: number;
}> {
  return apiClient('/api/v1/admin/reports/metrics/');
}

export async function fetchReportsOverview(): Promise<import('./types').ReportsOverviewStats> {
  return apiClient('/api/v1/admin/reports/overview/');
}

