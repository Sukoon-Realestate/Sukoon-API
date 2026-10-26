import { apiClient } from './client';
import { isBackendEnabled } from './config';
import type { Challenge } from './security';

export interface PayoutMoney { amount_minor: number; currency: string; exponent: number }
export interface PayoutResource {
  id: string; lease_id: string; revision: number; status: string; amount: PayoutMoney;
  masked_beneficiary: string; reason: string; submitted_at: string | null; succeeded_at: string | null;
  history: { action: string; occurred_at: string }[];
}
export interface PayoutRow { resource: PayoutResource; instruction_status: string }
export interface PayoutReview extends PayoutRow {
  provider_reference: string | null; allowed_actions: string[];
  can_reauthorize: boolean; can_retry: boolean; reauthorize_reason: string;
  attempts: { id: string; status: string; current: boolean; provider_reference: string | null; created_at: string; retry_of: string | null }[];
  authorization_details: Record<string, unknown>;
}
export interface PayableRow {
  id: string; lease_id: string; invoice_id: string; revision: number; amount: PayoutMoney;
  status: string; masked_beneficiary: string; blocking_reasons: string[];
  can_execute: boolean; can_prepare: boolean; provider_ready: boolean;
}
export interface PayoutPage<T> { results: T[]; page: number; total_pages: number; count: number }
export interface PayoutApproval {
  kind: 'create' | 'reauthorize' | 'retry'; resourceId: string; revision: number; payoutId?: string;
  command: { request_key: string; payable_ids?: string[]; expected_revision?: number };
  details: Record<string, unknown>; maskedBeneficiary: string;
}
const base = '/api/v1/features/v1/operations/';
function live() { if (!isBackendEnabled()) throw new Error('المتابعة المالية تحتاج إلى اتصال بالسجلات الفعلية.'); }
export function money(value: PayoutMoney): string {
  return new Intl.NumberFormat('ar-EG', { style: 'currency', currency: value.currency }).format(value.amount_minor / 10 ** value.exponent);
}
export const payoutStatus: Record<string, string> = {
  created: 'معتمد ولم يُرسل بعد', queued: 'بانتظار الإرسال', submitting: 'جارٍ إرسال المحاولة',
  processing: 'بانتظار تأكيد النتيجة', unknown: 'نتيجة المحاولة غير محسومة', held: 'يحتاج إلى مراجعة',
  paid: 'تأكد التحويل', confirmed: 'تأكد التحويل لدى المزود', failed: 'فشل مؤكد لدى المزود',
  ready: 'متاح للاعتماد', pending_eligibility: 'بانتظار شروط الاستحقاق',
};
export async function fetchPayoutQueue(page: number, signal?: AbortSignal) {
  live(); return apiClient<PayoutPage<PayoutRow>>(`${base}payouts/`, { params: { page }, signal, cache: 'no-store' });
}
export async function fetchPayableQueue(page: number, signal?: AbortSignal) {
  live(); return apiClient<PayoutPage<PayableRow>>(`${base}payables/`, { params: { page }, signal, cache: 'no-store' });
}
export async function fetchPayoutReview(id: string, signal?: AbortSignal) {
  live(); return apiClient<PayoutReview>(`${base}payouts/${encodeURIComponent(id)}/review/`, { signal, cache: 'no-store' });
}
export async function preparePayout(item: PayableRow): Promise<PayoutApproval> {
  live();
  const value = await apiClient<{ resource_id: string; resource_revision: number; masked_beneficiary: string; authorization_details: Record<string, unknown> }>(`${base}payouts/preview/`, { params: { payable_id: item.id }, cache: 'no-store' });
  return { kind: 'create', resourceId: value.resource_id, revision: value.resource_revision, command: { request_key: crypto.randomUUID(), payable_ids: [item.id] }, details: value.authorization_details, maskedBeneficiary: value.masked_beneficiary };
}
export function prepareReauthorization(item: PayoutReview, retry = false): PayoutApproval {
  return { kind: retry ? 'retry' : 'reauthorize', resourceId: item.resource.id, revision: item.resource.revision, payoutId: item.resource.id, command: { request_key: crypto.randomUUID(), expected_revision: item.resource.revision }, details: { ...item.authorization_details, approval_kind: retry ? 'retry' : 'reauthorize' }, maskedBeneficiary: item.resource.masked_beneficiary };
}
export async function beginPayoutApproval(value: PayoutApproval) {
  live(); return apiClient<Challenge>('/api/v1/auth/security/challenges/', { method: 'POST', body: { action: 'payout.execute', resource_id: value.resourceId, resource_revision: value.revision, payload: { command: value.command, ...value.details } } });
}
export async function confirmPayoutApproval(value: PayoutApproval, proof: string) {
  live(); return apiClient<{ resource: PayoutResource }>(value.kind === 'create' ? `${base}payouts/execute/` : `${base}payouts/${encodeURIComponent(value.payoutId!)}/${value.kind === 'retry' ? 'retry' : 'reauthorize'}/`, { method: 'POST', headers: { 'X-Sokoun-Authorization': proof }, body: value.command });
}
export async function reconcilePayout(id: string) {
  live(); return apiClient<{ resource: PayoutResource }>(`${base}payouts/${encodeURIComponent(id)}/reconcile/`, { method: 'POST', body: { request_key: crypto.randomUUID() } });
}
