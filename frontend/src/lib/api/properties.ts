import { apiClient } from './client';
import { PropertyItem, PropertyMetrics, PropertyDetail, PaginatedResponse } from './types';

export interface FetchPropertiesParams {
  [key: string]: string | number | boolean | null | undefined;
  search?: string;
  property_type?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export async function fetchAdminProperties(
  params?: FetchPropertiesParams
): Promise<PaginatedResponse<PropertyItem>> {
  return apiClient<PaginatedResponse<PropertyItem>>('/api/v1/admin/properties/', { params });
}

export async function fetchAdminPropertyMetrics(): Promise<PropertyMetrics> {
  return apiClient<PropertyMetrics>('/api/v1/admin/properties/metrics/');
}

export async function fetchAdminPropertyDetail(propertyId: string): Promise<PropertyDetail> {
  return apiClient<PropertyDetail>(`/api/v1/admin/properties/${propertyId}/`);
}

export async function approveProperty(propertyId: string): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/properties/${propertyId}/approve/`, {
    method: 'POST',
  });
}

export async function rejectProperty(
  propertyId: string,
  reason?: string
): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/properties/${propertyId}/reject/`, {
    method: 'POST',
    body: { reason: reason || '' },
  });
}

export async function requestPropertyRevision(
  propertyId: string,
  reason?: string
): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/properties/${propertyId}/revision/`, {
    method: 'POST',
    body: { reason: reason || '' },
  });
}
