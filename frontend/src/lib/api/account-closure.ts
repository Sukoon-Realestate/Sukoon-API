import { apiClient } from './client';
import { Challenge } from './security';

export interface ClosureRequest {
  id: string; user_id: string; account_name: string; revision: number;
  status: 'in_review' | 'awaiting_settlement' | 'withdrawn' | 'rejected' | 'completed';
  active: boolean; reason: string; decision_reason: string; erasure_pending: boolean;
  blockers: { code: string; label: string; count: number }[];
  history: { action: string; revision: number; reason: string; at: string }[];
}
export interface ClosureDecision { expected_revision: number; decision: 'wait' | 'reject' | 'complete'; reason: string; }
export const canReviewClosure = (role?: string) => role === 'system_owner' || role === 'account_closure_reviewer';
const base = '/api/v1/auth/account-closure/';
export const closureQueue = (page: number, history: boolean, signal?: AbortSignal) => apiClient<{results: ClosureRequest[]; total_pages: number}>(`${base}review/`, {params: {page, history}, signal});
export const closureDetail = (id: string, signal?: AbortSignal) => apiClient<ClosureRequest>(`${base}${encodeURIComponent(id)}/review/`, {signal});
export const closureChallenge = (item: ClosureRequest, body: ClosureDecision) => apiClient<Challenge>('/api/v1/auth/security/challenges/', {
  method: 'POST', body: {action: 'account.closure.review', resource_id: item.id, resource_revision: item.revision, payload: body},
});
export const closureDecide = (id: string, body: ClosureDecision, proof: string, key: string) => apiClient<ClosureRequest>(`${base}${encodeURIComponent(id)}/review/`, {
  method: 'POST', body, headers: {'X-Sokoun-Authorization': proof, 'Idempotency-Key': key},
});
export const closureRecover = (id: string, key: string) => apiClient<{state: 'confirmed' | 'absent_final' | 'pending'}>(`${base}receipt/`, {
  method: 'POST', body: {operation: `account.closure.review:${id}`}, headers: {'Idempotency-Key': key},
});
