'use client';
import { useId, type ReactNode } from 'react';
import { MoveHorizontal } from 'lucide-react';
export function TableScroll({ label = 'جدول البيانات', children }: { label?: string; children: ReactNode }) {
  const hint = useId();
  return <div><p id={hint} className="admin-table-hint"><MoveHorizontal size={16} aria-hidden />مرّر الجدول أفقياً لعرض بقية التفاصيل والإجراءات.</p><div className="admin-table-scroll" role="region" tabIndex={0} aria-label={label} aria-describedby={hint}>{children}</div></div>;
}
