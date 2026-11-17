import type { AuditLogItem, PaginatedResponse } from './types';

export type AuditLogPage = PaginatedResponse<AuditLogItem> & {
  page: number;
  per_page: number;
  total_pages: number;
};

export function auditLogPage(response: unknown, requestedPage: number): AuditLogPage {
  const value = response as Partial<AuditLogPage> | null;
  if (!value || !Array.isArray(value.results) ||
      !Number.isSafeInteger(value.page) || value.page !== requestedPage ||
      !Number.isSafeInteger(value.per_page) || value.per_page! < 1 ||
      !Number.isSafeInteger(value.count) || value.count! < 0 ||
      !Number.isSafeInteger(value.total_pages) || value.total_pages! < 1) {
    throw new Error('Invalid audit pagination');
  }
  const { page, per_page: perPage, count, total_pages: totalPages } = value as AuditLogPage;
  if (totalPages !== Math.max(1, Math.ceil(count / perPage)) || page > totalPages ||
      value.results.length !== Math.min(perPage, Math.max(0, count - (page - 1) * perPage)) ||
      value.next !== (page < totalPages ? `?page=${page + 1}` : null) ||
      value.previous !== (page > 1 ? `?page=${page - 1}` : null)) {
    throw new Error('Invalid audit pagination');
  }
  const ids = new Set<string>();
  for (const row of value.results) {
    if (!row || typeof row !== 'object' ||
        !(['id', 'time', 'action', 'typeBadge', 'target', 'operator'] as const)
          .every(field => typeof row[field] === 'string') || !row.id || ids.has(row.id)) {
      throw new Error('Invalid audit row');
    }
    ids.add(row.id);
  }
  return value as AuditLogPage;
}

function csvCell(value: string): string {
  // A quoted CSV cell can still be evaluated as a spreadsheet formula. Guard
  // leading whitespace/control/direction marks before formula metacharacters.
  const dangerous = /^[\s\u0000-\u001f\u007f\u200b-\u200f\u202a-\u202e\u2060-\u206f]*[=+\-@]/u.test(value) || /^[\t\r\n]/.test(value);
  return `"${(dangerous ? "'" + value : value).replaceAll('"', '""')}"`;
}

export function downloadAuditLogPage(value: AuditLogPage): void {
  const page = auditLogPage(value, value.page);
  if (page.results.length === 0) throw new Error('No displayed audit rows to export');
  const rows = [
    ['الوقت', 'الإجراء', 'النوع', 'المستهدف', 'المشرف', 'معرّف السجل'],
    ...page.results.map(row => [row.time, row.action, row.typeBadge, row.target, row.operator, row.id]),
  ];
  const csv = '\uFEFF' + rows.map(row => row.map(csvCell).join(',')).join('\r\n') + '\r\n';
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  try {
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `audit-logs-page-${page.page}.csv`;
    anchor.click();
  } catch (error) {
    URL.revokeObjectURL(url);
    throw error;
  }
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
