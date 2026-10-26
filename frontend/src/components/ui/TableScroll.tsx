'use client';

import { useId, type ReactNode } from 'react';
import { MoveHorizontal } from 'lucide-react';

export function TableScroll({ label = 'جدول البيانات', children }: { label?: string; children: ReactNode }) {
  const hint = useId();
  return <div className="min-w-0">
    <p id={hint} className="flex items-center gap-2 border-b border-[var(--card-border)] bg-[var(--table-header-bg)] px-4 py-3 text-xs text-[var(--text-muted)] md:hidden">
      <MoveHorizontal size={16} className="shrink-0" aria-hidden />مرّر الجدول أفقياً لعرض بقية التفاصيل والإجراءات.
    </p>
    <div className="max-w-full overflow-x-auto focus-visible:outline-offset-[-3px]" role="region" tabIndex={0} aria-label={label} aria-describedby={hint}>{children}</div>
  </div>;
}
