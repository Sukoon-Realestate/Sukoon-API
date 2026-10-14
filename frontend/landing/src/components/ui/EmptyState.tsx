'use client';
import type { ReactNode } from 'react';
import { SearchX, RotateCcw } from 'lucide-react';
interface EmptyStateProps { title?: string; description?: string; icon?: ReactNode; onReset?: () => void; onAction?: () => void; resetText?: string; actionLabel?: string }
export function EmptyState({ title = 'لا توجد نتائج', description = 'جرّب تغيير كلمات البحث أو إعادة ضبط الفلاتر لعرض البيانات المتاحة.', icon, onReset, onAction, resetText = 'إعادة ضبط الفلاتر', actionLabel }: EmptyStateProps) {
  const action = onReset || onAction;
  return <div className="admin-inline-empty my-3"><span className="mb-1 text-[var(--text-subtle)]">{icon || <SearchX size={30} strokeWidth={1.4} aria-hidden />}</span><h3 className="text-base font-medium text-[var(--foreground)]">{title}</h3><p className="max-w-md leading-7">{description}</p>{action && <button type="button" onClick={action} className="admin-button admin-button-secondary mt-2"><RotateCcw size={15} aria-hidden />{actionLabel || resetText}</button>}</div>;
}
