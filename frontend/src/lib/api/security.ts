import { apiClient } from './client';

export interface RecoveryRequest {
  id: string; revision: number; status: string; reason: string; decision_reason: string;
  created_at: string; completed_at: string | null;
  review_available?: boolean;
  email?: string; identity_reference?: string; known_channel_reference?: string;
  decisions: { decision: string; reason: string; revision: number; created_at: string }[];
}
export interface SecurityStatus {
  configured: boolean; restricted: boolean; recovery: RecoveryRequest | null;
  initial_setup: { identity_documented: boolean; available: boolean; requires_recovery: boolean };
  can_document_staff_identity: boolean;
}
export interface StaffIdentity {
  user_id: string; email: string; name: string; documented: boolean;
  configured: boolean; recovery_pending: boolean;
  identity_reference: string; known_channel_reference: string;
}
export interface StaffIdentityBody {
  person_reference: string; evidence_reference: string; known_channel_reference: string;
  verification_method: 'in_person' | 'known_channel_video'; identity_matched: boolean;
}
export interface Enrollment { id: string; expires_at: string; secret: string; uri: string; }
export interface RecoveryDecision {
  expected_revision: number; decision: 'approve' | 'reject' | 'request_information' | 'renew_enrollment';
  reason: string; verification_method: 'in_person' | 'known_channel_video';
  verification_reference: string; identity_matched: boolean;
}
export interface Challenge { id: string; expires_at: string; verification: { type: string; instructions: string }; }
const base = '/api/v1/auth/security/';
export const fetchSecurity = (signal?: AbortSignal) => apiClient<SecurityStatus>(`${base}totp/`, { signal });
export const beginInitialEnrollment = () => apiClient<Enrollment>(`${base}totp/initial-enrollment/`, { method: 'POST' });
export const fetchStaffIdentities = (signal?: AbortSignal) => apiClient<{ results: StaffIdentity[] }>(`${base}totp/staff-identities/`, { signal });
export const beginIdentityReview = (userId: string, body: StaffIdentityBody) => apiClient<Challenge>(`${base}challenges/`, {
  method: 'POST', body: { action: 'account.mfa.manage', resource_id: userId, resource_revision: 0, payload: body },
});
export const documentStaffIdentity = (userId: string, body: StaffIdentityBody, proof: string) => apiClient<StaffIdentity>(`${base}totp/staff-identities/${encodeURIComponent(userId)}/document/`, {
  method: 'POST', body, headers: { 'X-Sokoun-Authorization': proof },
});
export const requestRecovery = (reason: string) => apiClient<RecoveryRequest>(`${base}totp/recoveries/`, { method: 'POST', body: { reason } });
export const respondRecovery = (item: RecoveryRequest, reason: string) => apiClient<RecoveryRequest>(`${base}totp/recoveries/${encodeURIComponent(item.id)}/respond/`, { method: 'POST', body: { reason, expected_revision: item.revision } });
export const fetchRecoveryQueue = (signal?: AbortSignal) => apiClient<{ results: RecoveryRequest[] }>(`${base}totp/review/`, { signal });
export const enrollFactor = (id: string) => apiClient<Enrollment>(`${base}totp/recoveries/${encodeURIComponent(id)}/enroll/`, { method: 'POST' });
export const confirmFactor = (id: string, code: string) => apiClient<RecoveryRequest | SecurityStatus>(`${base}totp/enrollments/${encodeURIComponent(id)}/confirm/`, { method: 'POST', body: { code } });
export const beginReview = (item: RecoveryRequest, body: RecoveryDecision) => apiClient<Challenge>(`${base}challenges/`, {
  method: 'POST', body: { action: 'account.totp.recovery.review', resource_id: item.id, resource_revision: item.revision, payload: body },
});
export const verifyReview = (id: string, assertion: string) => apiClient<{ proof: string; expires_at: string }>(`${base}challenges/${encodeURIComponent(id)}/verify/`, { method: 'POST', body: { assertion } });
export const decideRecovery = (id: string, body: RecoveryDecision, proof: string) => apiClient<RecoveryRequest>(`${base}totp/recoveries/${encodeURIComponent(id)}/review/`, { method: 'POST', body, headers: { 'X-Sokoun-Authorization': proof } });
