import { apiClient } from './client';

export type ContentValue = string | number | boolean | null;
export type ContentValues = Record<string, ContentValue>;
export interface ContentField {
  name: string; label: string; type: 'text' | 'email' | 'multiline' | 'integer' | 'boolean' | 'choice' | 'datetime' | 'date' | 'decimal' | 'relation';
  required: boolean; fixed: boolean; max_length: number | null;
  choices: { value: string; label: string }[];
  relation?: string | null;
  nullable?: boolean;
}
export interface ContentSchema { kind: string; label: string; fields: ContentField[]; revision_type?: 'integer' | 'opaque'; guidance?: string; allow_create?: boolean; }
export interface ContentItem {
  id: string; revision: number | string; values: ContentValues;
  relation_labels?: Record<string, string>;
  selection_available?: boolean;
  history?: { revision: number; reason: string; created_at: string; before: Omit<ContentItem, 'history'>; after: Omit<ContentItem, 'history'> }[];
}
export interface ContentPage { results: ContentItem[]; count: number; page: number; total_pages: number; }
export interface ContentIntent { key: string; kind: string; identity: string | null; }
const base = '/api/v1/admin/content/';
export const canEditContent = (role?: string) => role === 'system_owner';
export const contentSchema = (signal?: AbortSignal) => apiClient<{catalogs: ContentSchema[]; can_edit: boolean; blocking_reason: string}>(base, {signal});
export const contentList = (kind: string, page: number, signal?: AbortSignal, search?: string) => apiClient<ContentPage>(`${base}${encodeURIComponent(kind)}/`, {params: {page, search}, signal});
export const contentDetail = (kind: string, id: string, signal?: AbortSignal) => apiClient<ContentItem>(`${base}${encodeURIComponent(kind)}/${encodeURIComponent(id)}/`, {signal});
export const saveContent = (intent: ContentIntent, expected_revision: number | string, values: ContentValues, reason: string) => apiClient<ContentItem>(
  `${base}${encodeURIComponent(intent.kind)}/${intent.identity ? `${encodeURIComponent(intent.identity)}/` : ''}`,
  {method: 'POST', body: {expected_revision, values, reason}, headers: {'Idempotency-Key': intent.key}},
);
export const recoverContent = (intent: ContentIntent) => apiClient<{status: 'confirmed' | 'absent_final'; receipt: ContentItem | null}>(
  `${base}${encodeURIComponent(intent.kind)}/receipts/${encodeURIComponent(intent.key)}/`, {method: 'POST', body: {identity: intent.identity}},
);

export function contentTitle(item: ContentItem): string {
  if (item.relation_labels?.plan && item.relation_labels?.feature) return `${item.relation_labels.plan} — ${item.relation_labels.feature}`;
  return String(item.values.title_ar || item.values.question_ar || item.values.name_ar || item.values.name_en || item.values.label_ar || item.values.label_en || item.values.name || item.values.version || item.values.workspace || item.id);
}
