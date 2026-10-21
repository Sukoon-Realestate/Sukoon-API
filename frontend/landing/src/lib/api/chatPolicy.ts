import { apiClient, type RequestOptions } from './client';
import { isBackendEnabled } from './config';
import type { PaginatedResponse } from './types';

export interface PolicyCase {
  id: string; state: string; revision: number; policy_version: string;
  created_at: string; appeal_submitted: boolean; review_overdue: boolean;
  subject_id?: string; conversation_id?: string;
  evidence?: {
    verdict?: { label: string; confidence: number; evidence: { message_id: string; source: string; quote: string }[] };
    verification?: { label: string; confidence: number };
    messages?: { message_id: string; actor_id: string; text: string; media: { source: string; kind: string; text: string; uncertain: boolean }[] }[];
  };
  appeal?: { text: string } | null;
  actions?: { action: string; notes: string; revision: number; actor_id: string }[];
}
export type PolicyAction = 'dismiss' | 'release' | 'keep_restricted' | 'ban';
export interface PolicyCommand { client_id: string; expected_revision: number; action: PolicyAction; notes: string }
const base = '/api/v1/chat/admin/policy-cases/';
function requireBackend() {
  if (!isBackendEnabled()) throw new Error('مراجعة الحسابات تحتاج اتصالًا بالخادم الفعلي.');
}
async function privateRequest<T>(endpoint: string, options: RequestOptions): Promise<T> {
  requireBackend();
  const token = typeof window === 'undefined' ? null : localStorage.getItem('sukoon_access_token');
  const result = await apiClient<T>(endpoint, options);
  if (typeof window !== 'undefined' && localStorage.getItem('sukoon_access_token') !== token) {
    throw new Error('انتهت جلسة المراجع. أعد فتح الحالة من الحساب الحالي.');
  }
  return result;
}
export function fetchPolicyCases(page = 1) { return privateRequest<PaginatedResponse<PolicyCase>>(base, { params: { page }, cache: 'no-store' }); }
export function fetchPolicyCase(id: string) { return privateRequest<PolicyCase>(base + id + '/', { cache: 'no-store' }); }
export function reviewPolicyCase(id: string, command: PolicyCommand) { return privateRequest<PolicyCase>(base + id + '/', { method: 'POST', body: command }); }

export interface PolicyStatus {
  mode: string; model: string; private_inputs_approved: boolean; provider_configured: boolean;
  daily_requests: number; daily_limit: number; pending: { count: number; oldest: string | null };
  last_success_at: string | null; last_failure_code: string; overdue_reviews: number;
}
export function fetchPolicyStatus() { return privateRequest<PolicyStatus>('/api/v1/chat/admin/policy-status/', { cache: 'no-store' }); }
