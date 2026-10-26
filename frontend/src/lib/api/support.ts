import { apiClient } from './client';
import { SupportTicket, SupportMetrics, PaginatedResponse } from './types';
import { API_BASE_URL } from './config';

export interface FetchSupportTicketsParams {
  [key: string]: string | number | boolean | null | undefined;
  tab?: string;
  page?: number;
  page_size?: number;
}

export async function fetchSupportTickets(
  params?: FetchSupportTicketsParams, signal?: AbortSignal
): Promise<PaginatedResponse<SupportTicket>> {
  return apiClient<PaginatedResponse<SupportTicket>>('/api/v1/admin/support/', {
    params, signal,
  });
}

export async function fetchSupportMetrics(signal?: AbortSignal): Promise<SupportMetrics> {
  return apiClient<SupportMetrics>('/api/v1/admin/support/metrics/', { signal });
}

export type SupportAction = 'reply' | 'resolve' | 'claim' | 'assign' | 'escalate' | 'note';
export interface SupportCommand {
  expected_revision: number; action: SupportAction; reason: string;
  body?: string; assignee_id?: string; acknowledge_resolution?: boolean;
}
export interface SupportDetail extends SupportTicket {
  reference: string; workspace: string; revision: number; escalated: boolean;
  assigned_to_id: string | null;
  messages: { id: string; sender: string; body: string; created_at: string; attachments: {id: string; name: string; url: string}[] }[];
  internal_notes: { id: string; actor: string; body: string; created_at: string }[];
  transitions: { id: string; revision: number; action: string; reason: string; actor: string; assignee: string | null; created_at: string }[];
  actions: Record<SupportAction, boolean>;
  rental_context: Record<string, string>;
}
export const fetchSupportDetail = (id: string, signal?: AbortSignal) => apiClient<SupportDetail>(`/api/v1/admin/support/${encodeURIComponent(id)}/`, { signal });
export const fetchSupportTeam = (signal?: AbortSignal) => apiClient<{ results: {id: string; name: string}[] }>('/api/v1/admin/support/team/', { signal });
export const commandSupport = (id: string, body: SupportCommand, key: string) => apiClient<{ ticket_id: string; revision: number }>(`/api/v1/admin/support/${encodeURIComponent(id)}/`, { method: 'POST', body, headers: { 'Idempotency-Key': key } });
export const recoverSupport = (id: string, key: string, action: SupportAction, close = false) => apiClient<{ status: 'confirmed' | 'unknown' | 'pending' | 'absent_final' }>(`/api/v1/admin/support/${encodeURIComponent(id)}/receipts/${encodeURIComponent(key)}/`, close ? { method: 'POST', body: { action } } : { params: { action } });

export async function downloadSupportAttachment(path: string, name: string) {
  const base = new URL(API_BASE_URL || '/', window.location.origin);
  const url = new URL(path, base);
  if (url.origin !== base.origin || !url.pathname.startsWith('/api/v1/support/attachments/')) {
    throw new Error('رابط المرفق غير متاح. حدّث التذكرة.');
  }
  const token = localStorage.getItem('sukoon_access_token');
  const response = await fetch(url, { credentials: 'include', headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!response.ok || localStorage.getItem('sukoon_access_token') !== token) throw new Error('تعذّر تنزيل المرفق بالصلاحيات الحالية.');
  const blob = await response.blob();
  if (localStorage.getItem('sukoon_access_token') !== token) throw new Error('تغيّر الحساب. أعد فتح المرفق بالصلاحية الحالية.');
  const file = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = file; anchor.download = name; anchor.click();
  setTimeout(() => URL.revokeObjectURL(file), 1000);
}
