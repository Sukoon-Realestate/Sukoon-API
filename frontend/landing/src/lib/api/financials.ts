import { apiClient } from './client';
import { FinancialSummary, TransactionItem, PaginatedResponse } from './types';

export async function fetchFinancialSummary(): Promise<FinancialSummary> {
  return apiClient<FinancialSummary>('/api/v1/admin/financials/summary/');
}

export async function fetchTransactions(params?: {
  status?: string;
  search?: string;
  page?: number;
}): Promise<PaginatedResponse<TransactionItem>> {
  return apiClient<PaginatedResponse<TransactionItem>>('/api/v1/admin/financials/transactions/', {
    params: {
      status: params?.status && params.status !== 'all' ? params.status : undefined,
      search: params?.search || undefined,
      page: params?.page,
    },
  });
}
