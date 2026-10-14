import { apiClient } from './client';
import { SupportTicket, SupportMetrics, PaginatedResponse } from './types';

export interface FetchSupportTicketsParams {
  [key: string]: string | number | boolean | null | undefined;
  tab?: string;
  page?: number;
  page_size?: number;
}

export async function fetchSupportTickets(
  params?: FetchSupportTicketsParams
): Promise<PaginatedResponse<SupportTicket>> {
  return apiClient<PaginatedResponse<SupportTicket>>('/api/v1/admin/support/', {
    params,
  });
}

export async function fetchSupportMetrics(): Promise<SupportMetrics> {
  return apiClient<SupportMetrics>('/api/v1/admin/support/metrics/');
}
