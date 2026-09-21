'use client';

import React from 'react';
import { SearchX, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  onReset?: () => void;
  onAction?: () => void;
  resetText?: string;
  actionLabel?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'لا توجد نتائج تطابق بحثك',
  description = 'جرب تغيير كلمات البحث أو إعادة ضبط الفلاتر المطبقة لعرض جميع البيانات المتاحة.',
  icon,
  onReset,
  onAction,
  resetText = 'إعادة ضبط الفلاتر',
  actionLabel,
}) => {
  const handleAction = onReset || onAction;
  const buttonText = actionLabel || resetText;
  return (
    <div className="p-8 sm:p-12 text-center bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-[var(--shadow-card)] animate-fadeIn flex flex-col items-center justify-center my-4">
      <div className="w-16 h-16 rounded-3xl bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20 flex items-center justify-center mb-4 glow-teal-sm animate-breathe">
        {icon || <SearchX className="w-8 h-8" />}
      </div>

      <h4 className="text-base sm:text-lg font-black text-[var(--foreground)] mb-1">
        {title}
      </h4>
      <p className="text-xs sm:text-sm font-medium text-[var(--text-muted)] max-w-md leading-relaxed mb-5">
        {description}
      </p>

      {handleAction && (
        <button
          onClick={handleAction}
          className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl shadow-md transition-all cursor-pointer btn-press"
        >
          <RefreshCw className="w-4 h-4" />
          <span>{buttonText}</span>
        </button>
      )}
    </div>
  );
};
