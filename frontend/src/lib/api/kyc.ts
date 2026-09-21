import { apiClient } from './client';
import { KycRequest, KycMetrics, KycDetail, PaginatedResponse } from './types';

export interface FetchKycParams {
  [key: string]: string | number | boolean | null | undefined;
  status?: string;
  user_type?: string;
  page?: number;
  page_size?: number;
}

export async function fetchKycQueue(params?: FetchKycParams): Promise<PaginatedResponse<KycRequest>> {
  return apiClient<PaginatedResponse<KycRequest>>('/api/v1/admin/kyc/', { params });
}

export async function fetchKycMetrics(): Promise<KycMetrics> {
  return apiClient<KycMetrics>('/api/v1/admin/kyc/metrics/');
}

export async function fetchKycDetail(submissionId: string): Promise<KycDetail> {
  return apiClient<KycDetail>(`/api/v1/admin/kyc/${submissionId}/`);
}

export async function approveKyc(submissionId: string): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/kyc/${submissionId}/approve/`, {
    method: 'POST',
  });
}

export async function rejectKyc(submissionId: string, reason: string): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/kyc/${submissionId}/reject/`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}
