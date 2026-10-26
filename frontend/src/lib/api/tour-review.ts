import { apiClient } from './client';

export interface TourReview {
  id: string; tour_id: string; asset_id: string; asset_kind: 'property' | 'building' | 'complex';
  title: string; kind: string; draft_version: number; source_hash: string;
  processing_state: string; review_state: string; stage: string; report: unknown;
  can_review: boolean; review_blocker: string;
  variants: { id: string; context: string; scope_fingerprint: string }[];
  history: { decision: string; reason: string; source_hash: string; created_at: string }[];
}
export interface ReviewPage { items: TourReview[]; count: number; page: number; has_next: boolean }
export interface TourPreview { session_id: string; viewer_url: string; bootstrap_token: string; bootstrap_expires_at: string }
export const reviewList = (state: string, page: number, signal?: AbortSignal) =>
  apiClient<ReviewPage>('/api/v1/admin/virtual-tours/reviews/', { params: { state, page }, signal });
export const reviewDetail = (id: string, signal?: AbortSignal) =>
  apiClient<TourReview>(`/api/v1/admin/virtual-tours/reviews/${id}/`, { signal });
const tourPath = (item: TourReview) => item.asset_kind === 'property'
  ? `/properties/${item.asset_id}/virtual-tours/${item.tour_id}/`
  : `/residential-assets/${item.asset_kind}/${item.asset_id}/virtual-tours/${item.tour_id}/`;
export const previewTour = (item: TourReview, context: string) =>
  apiClient<TourPreview>(`/api/v1${tourPath(item)}viewer-sessions/`, { method: 'POST', body: {
    preview: true, revision_id: item.id, context, supported_manifest_versions: [1, 2],
  } });
export const decideTour = (item: TourReview, decision: string, reason: string, key: string) =>
  apiClient(`/api/v1/admin${tourPath(item)}revisions/${item.id}/review-decisions/`, { method: 'POST',
    headers: { 'Idempotency-Key': key }, body: { decision, reason, expected_source_hash: item.source_hash } });
