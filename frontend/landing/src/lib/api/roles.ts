import { apiClient } from './client';
import { AdminUserItem, AdminRoleItem, PermissionsMatrixRow, PaginatedResponse } from './types';

export async function fetchStaffList(): Promise<PaginatedResponse<AdminUserItem>> {
  return apiClient<PaginatedResponse<AdminUserItem>>('/api/v1/admin/staff/');
}

export async function fetchRolesSummary(): Promise<AdminRoleItem[]> {
  return apiClient<AdminRoleItem[]>('/api/v1/admin/staff/roles/');
}

export async function inviteStaff(data: { name: string; email: string; role_name?: string }): Promise<{ message: string }> {
  return apiClient<{ message: string }>('/api/v1/admin/staff/invite/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteStaff(staffId: string): Promise<{ message: string }> {
  return apiClient<{ message: string }>(`/api/v1/admin/staff/${staffId}/`, {
    method: 'DELETE',
  });
}

export async function fetchPermissionsMatrix(): Promise<PermissionsMatrixRow[]> {
  return apiClient<PermissionsMatrixRow[]>('/api/v1/admin/permissions/');
}

export async function updatePermissionsMatrix(matrix: PermissionsMatrixRow[]): Promise<{ message: string; matrix: PermissionsMatrixRow[] }> {
  return apiClient<{ message: string; matrix: PermissionsMatrixRow[] }>('/api/v1/admin/permissions/', {
    method: 'PATCH',
    body: JSON.stringify(matrix),
  });
}
