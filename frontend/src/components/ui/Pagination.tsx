'use client';

import React from 'react';
import { ChevronRight, ChevronLeft } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  onItemsPerPageChange?: (size: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  onItemsPerPageChange,
}) => {
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push('...');
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (currentPage < totalPages - 2) pages.push('...');
      pages.push(totalPages);
    }
    return pages;
  };

  if (totalItems === 0) return null;

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
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="p-1.5 rounded-lg border border-[var(--card-border)] bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          title="الصفحة السابقة"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        {getPageNumbers().map((page, idx) => (
          <React.Fragment key={idx}>
            {typeof page === 'number' ? (
              <button
                onClick={() => onPageChange(page)}
                className={`w-8 h-8 rounded-lg text-xs font-extrabold transition-all cursor-pointer ${
                  currentPage === page
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
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="p-1.5 rounded-lg border border-[var(--card-border)] bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          title="الصفحة التالية"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
