import { apiClient } from './client';
import {
  SystemHealth,
  AuditLogItem,
  PushCampaign,
  PaginatedResponse,
} from './types';

export async function fetchSystemHealth(signal?: AbortSignal): Promise<SystemHealth> {
  return apiClient<SystemHealth>('/api/v1/admin/system/health/', {signal});
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


export async function previewCampaign(payload: {title: string; body: string; audience: 'all' | 'tenants' | 'landlords' | 'verified'; request_key: string}): Promise<PushCampaign> {
  return apiClient<PushCampaign>('/api/v1/admin/system/notifications/preview/', {method: 'POST', body: payload});
}

export async function changeCampaign(campaign: PushCampaign, action: 'confirm' | 'cancel'): Promise<PushCampaign> {
  return apiClient<PushCampaign>(`/api/v1/admin/system/notifications/${encodeURIComponent(campaign.id)}/`, {method: 'POST', body: {action, expected_revision: campaign.revision, preview_digest: campaign.preview_digest}});
}
