import { apiClient } from './client';

export interface AdminFollowups {
  measured_at: string;
  results: Array<{ id: string; title: string; count: number; href: string }>;
}
const destinations = new Set(['/admin/kyc', '/admin/properties/review', '/admin/support', '/admin/account-closure']);

export async function fetchAdminFollowups(signal?: AbortSignal): Promise<AdminFollowups> {
  const data = await apiClient<AdminFollowups>('/api/v1/admin/followups/', { signal });
  if (!data || !Number.isFinite(Date.parse(data.measured_at)) || !Array.isArray(data.results) ||
    data.results.some(row => !row || typeof row.id !== 'string' || typeof row.title !== 'string' ||
      !Number.isSafeInteger(row.count) || row.count < 0 || !destinations.has(row.href))) {
    throw new Error('Invalid administrative follow-up response');
  }
  return data;
}
