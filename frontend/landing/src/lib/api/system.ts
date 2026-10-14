import { apiClient } from './client';
import {
  SystemHealth,
  AuditLogItem,
  PushCampaign,
  PaginatedResponse,
} from './types';

export async function fetchSystemHealth(): Promise<SystemHealth> {
  return apiClient<SystemHealth>('/api/v1/admin/system/health/');
}

export async function fetchAuditLogs(params?: {
  type?: string;
  search?: string;
  page?: number;
}): Promise<PaginatedResponse<AuditLogItem>> {
  return apiClient<PaginatedResponse<AuditLogItem>>('/api/v1/admin/system/logs/', {
    params: {
      type: params?.type && params.type !== 'all' ? params.type : undefined,
      search: params?.search || undefined,
      page: params?.page,
    },
  });
}

export async function fetchPushCampaigns(): Promise<PushCampaign[]> {
  return apiClient<PushCampaign[]>('/api/v1/admin/system/notifications/');
}

export async function sendPushNotification(payload: {
  title: string;
  body: string;
  audience?: 'all' | 'tenants' | 'landlords' | 'verified';
}): Promise<PushCampaign> {
  return apiClient<PushCampaign>('/api/v1/admin/system/notifications/send/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
