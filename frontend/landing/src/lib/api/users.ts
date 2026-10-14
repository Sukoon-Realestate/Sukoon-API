import { apiClient } from './client';
import { UserItem, PaginatedResponse } from './types';

export interface FetchUsersParams {
  [key: string]: string | number | boolean | null | undefined;
  search?: string;
  role?: string;
  status?: string;
  kyc_status?: string;
  page?: number;
  page_size?: number;
}

export async function fetchUsers(params?: FetchUsersParams): Promise<PaginatedResponse<UserItem>> {
  return apiClient<PaginatedResponse<UserItem>>('/api/v1/admin/users/', { params });
}

export async function fetchUserDetail(userId: string): Promise<UserItem> {
  return apiClient<UserItem>(`/api/v1/admin/users/${userId}/`);
}

export async function suspendUser(userId: string, reason?: string): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/users/${userId}/suspend/`, {
    method: 'POST',
    body: JSON.stringify({ reason: reason || 'إيقاف إداري' }),
  });
}

export async function unsuspendUser(userId: string): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/users/${userId}/unsuspend/`, {
    method: 'POST',
  });
}
