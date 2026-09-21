'use client';

import React from 'react';
import { ChevronRight, ChevronLeft } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages?: number;
  totalItems: number;
  itemsPerPage?: number;
  pageSize?: number;
  onPageChange: (page: number) => void;
  onItemsPerPageChange?: (size: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage = 1,
  totalPages,
  totalItems = 0,
  itemsPerPage,
  pageSize,
  onPageChange,
  onItemsPerPageChange,
}) => {
  const safeTotalItems = Number.isFinite(totalItems) ? Math.max(0, totalItems) : 0;
  if (safeTotalItems === 0) return null;

  const finalItemsPerPage = Math.max(1, Number.isFinite(itemsPerPage) && itemsPerPage ? itemsPerPage : (pageSize || 10));
  const calculatedTotalPages = Math.max(1, Math.ceil(safeTotalItems / finalItemsPerPage));
  const finalTotalPages = Number.isFinite(totalPages) && (totalPages as number) > 0
    ? (totalPages as number)
    : calculatedTotalPages;

  const validCurrentPage = Number.isFinite(currentPage) ? Math.max(1, Math.min(currentPage, finalTotalPages)) : 1;
  const startItem = (validCurrentPage - 1) * finalItemsPerPage + 1;
  const endItem = Math.min(validCurrentPage * finalItemsPerPage, safeTotalItems);

  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    if (!Number.isFinite(finalTotalPages) || finalTotalPages <= 1) {
      return [1];
    }
    if (finalTotalPages <= 5) {
      for (let i = 1; i <= finalTotalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (validCurrentPage > 3) pages.push('...');
      const start = Math.max(2, validCurrentPage - 1);
      const end = Math.min(finalTotalPages - 1, validCurrentPage + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (validCurrentPage < finalTotalPages - 2) pages.push('...');
      pages.push(finalTotalPages);
    }
    return pages.filter((p) => typeof p === 'string' || Number.isFinite(p));
  };

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-[var(--divider)] bg-[var(--card-bg)] text-xs font-bold text-[var(--text-muted)] rounded-b-2xl">
      {/* Range summary */}
      <div className="flex items-center gap-3">
        <span>
          عرض <span className="font-extrabold text-[var(--foreground)]">{startItem}–{endItem}</span> من أصل{' '}
          <span className="font-extrabold text-[var(--foreground)]">{totalItems}</span> سجل
        </span>

        {onItemsPerPageChange && (
          <div className="flex items-center gap-1.5 border-r border-[var(--divider)] pr-3">
            <span>صفوف:</span>
            <select
              value={itemsPerPage}
              onChange={(e) => onItemsPerPageChange(Number(e.target.value))}
              className="bg-[var(--card-hover)] border border-[var(--card-border)] text-[var(--foreground)] text-xs font-bold rounded-lg px-2 py-1 cursor-pointer focus:outline-hidden focus:ring-1 focus:ring-teal-500"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
          </div>
        )}
      </div>

      {/* Page controls */}
      <div className="flex items-center gap-1">
        {/* Next page in RTL means ChevronRight */}
        <button
          onClick={() => onPageChange(validCurrentPage - 1)}
          disabled={validCurrentPage <= 1}
          className="p-1.5 rounded-lg border border-[var(--card-border)] bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          title="الصفحة السابقة"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        {getPageNumbers().map((page, idx) => (
          <React.Fragment key={idx}>
            {typeof page === 'number' && Number.isFinite(page) ? (
              <button
                onClick={() => onPageChange(page)}
                className={`w-8 h-8 rounded-lg text-xs font-extrabold transition-all cursor-pointer ${
                  validCurrentPage === page
                    ? 'bg-teal-600 text-white shadow-xs glow-teal-sm'
                    : 'bg-[var(--card-bg)] border border-[var(--card-border)] text-[var(--foreground)] hover:bg-[var(--card-hover)]'
                }`}
              >
                {page}
              </button>
            ) : (
              <span className="px-1 text-[var(--text-subtle)]">...</span>
            )}
          </React.Fragment>
        ))}

        <button
          onClick={() => onPageChange(validCurrentPage + 1)}
          disabled={validCurrentPage >= finalTotalPages}
          className="p-1.5 rounded-lg border border-[var(--card-border)] bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          title="الصفحة التالية"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
