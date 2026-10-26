import { apiClient } from './client';
import { isBackendEnabled } from './config';
import type { Challenge } from './security';
import type { PayoutMoney, PayoutPage } from './payouts';

export interface RefundResource {
  id: string; lease_id: string; payment_attempt_id: string; revision: number; status: string;
  amount: PayoutMoney; reason: string; failure_code: string; provider_refund_id: string;
  allocations: Record<string, number>; purpose: string;
  history: { action: string; occurred_at: string }[];
  attempts: { id: string; current: boolean; retry_of: string | null; status: string; created_at: string; submitted_at: string | null; resolved_at: string | null }[];
}
export interface RefundReview {
  resource: RefundResource; instruction_status: string | null; provider_reference: string | null;
  submitted_at: string | null; instruction_id: string | null; can_execute: boolean; can_reauthorize: boolean; can_retry: boolean;
  allowed_actions: string[]; blocking_reasons: string[]; authorization_details: Record<string, unknown>;
}
export interface RefundApproval {
  kind: 'execute' | 'reauthorize' | 'retry'; review: RefundReview;
  command: { request_key: string; expected_revision: number; failed_instruction_id?: string };
}
const base = '/api/v1/features/v1/';
function live() { if (!isBackendEnabled()) throw new Error('متابعة الاسترداد تحتاج إلى اتصال بالسجلات الفعلية.'); }
export const refundStatus: Record<string, string> = {
  requested: 'بانتظار مراجعة الطلب', approved: 'اعتُمد الطلب وبقي إذن الإرسال', rejected: 'رُفض الطلب',
  queued: 'بانتظار الإرسال', submitting: 'أُرسلت المحاولة وبانتظار نتيجتها', processing: 'بانتظار تأكيد النتيجة',
  held: 'متوقف للمراجعة', unknown: 'نتيجة غير محسومة', confirmed: 'تأكد الاسترداد لدى المزود', succeeded: 'تم الاسترداد', failed: 'فشل الاسترداد',
};
export async function fetchRefunds(page: number, signal?: AbortSignal) {
  live(); return apiClient<PayoutPage<RefundReview>>(`${base}operations/refunds/`, { params: { page }, signal, cache: 'no-store' });
}
export async function fetchRefund(id: string, signal?: AbortSignal) {
  live(); return apiClient<RefundReview>(`${base}operations/refunds/${encodeURIComponent(id)}/review/`, { signal, cache: 'no-store' });
}
export function prepareRefund(review: RefundReview, kind: RefundApproval['kind']): RefundApproval {
  if (kind === 'retry' && !review.instruction_id) throw new Error('حدّث المحاولة الفاشلة قبل مراجعة إذن جديد.');
  return { kind, review, command: { request_key: crypto.randomUUID(), expected_revision: review.resource.revision, ...(kind === 'retry' ? { failed_instruction_id: review.instruction_id! } : {}) } };
}
export async function beginRefundApproval(value: RefundApproval) {
  live(); return apiClient<Challenge>('/api/v1/auth/security/challenges/', { method: 'POST', body: {
    action: 'refund.execute', resource_id: value.review.resource.id, resource_revision: value.review.resource.revision,
    payload: { command: value.command, ...value.review.authorization_details, ...(value.kind !== 'execute' ? { approval_kind: value.kind } : {}) },
  } });
}
export async function confirmRefundApproval(value: RefundApproval, proof: string) {
  live(); const path = value.kind === 'execute' ? `refund-requests/${encodeURIComponent(value.review.resource.id)}/execute/` : `operations/refunds/${encodeURIComponent(value.review.resource.id)}/${value.kind}/`;
  return apiClient<{ resource: RefundResource }>(base + path, { method: 'POST', headers: { 'X-Sokoun-Authorization': proof }, body: value.command });
}
export async function respondRefund(review: RefundReview, action: 'approve' | 'reject', key: string) {
  live(); return apiClient<{ resource: RefundResource }>(`${base}refund-requests/${encodeURIComponent(review.resource.id)}/respond/`, { method: 'POST', body: { action, request_key: key, expected_revision: review.resource.revision } });
}
export async function reconcileRefund(id: string, candidate?: string) {
  live(); return apiClient<RefundReview>(`${base}operations/refunds/${encodeURIComponent(id)}/reconcile/`, { method: 'POST', body: candidate ? { provider_transaction_id: candidate } : {} });
}
