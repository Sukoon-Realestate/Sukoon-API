import { apiClient } from './client';
import { PropertyItem, PropertyMetrics, PropertyDetail, PaginatedResponse } from './types';

export interface FetchPropertiesParams {
  [key: string]: string | number | boolean | null | undefined;
  search?: string;
  property_type?: string;
  property_type_id?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export async function fetchAdminProperties(
  params?: FetchPropertiesParams, signal?: AbortSignal
): Promise<PaginatedResponse<PropertyItem>> {
  return apiClient<PaginatedResponse<PropertyItem>>('/api/v1/admin/properties/', { params, signal, headers: { 'Accept-Language': 'ar' } });
}

export async function fetchAdminPropertyMetrics(signal?: AbortSignal): Promise<PropertyMetrics> {
  return apiClient<PropertyMetrics>('/api/v1/admin/properties/metrics/', { signal, headers: { 'Accept-Language': 'ar' } });
}

export async function fetchAdminPropertyDetail(propertyId: string, signal?: AbortSignal): Promise<PropertyDetail> {
  return apiClient<PropertyDetail>(`/api/v1/admin/properties/${encodeURIComponent(propertyId)}/`, { signal });
}

export type PropertyDecision = 'approve' | 'reject' | 'request_revision' | 'block' | 'unblock';
export interface PropertyReviewCommand {
  expected_version: string; reason: string; internal_note: string;
}
export function moderateProperty(id: string, action: PropertyDecision, body: PropertyReviewCommand, key: string) {
  const endpoint = action === 'request_revision' ? 'revision' : action;
  return apiClient<{property_id: string; decision_id: string; revision: number}>(`/api/v1/admin/properties/${encodeURIComponent(id)}/${endpoint}/`, {
    method: 'POST', body, headers: { 'Idempotency-Key': key },
  });
}
export const recoverPropertyReview = (id: string, key: string, close = false) => apiClient<{
  status: 'confirmed' | 'unknown' | 'pending' | 'absent_final';
}>(`/api/v1/admin/properties/${encodeURIComponent(id)}/receipts/${encodeURIComponent(key)}/`, close ? { method: 'POST' } : {});

export async function exportProperty(id: string) {
  // Fetch again so current server authority, rather than a cached page, permits export.
  const value = await fetchAdminPropertyDetail(id);
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url; anchor.download = `property-${value.id}.json`; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
