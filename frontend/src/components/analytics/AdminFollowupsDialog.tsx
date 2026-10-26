'use client';

import { useEffect, useRef, useState } from 'react';
import { fetchAdminFollowups, type AdminFollowups } from '../../lib/api/followups';

export function AdminFollowupsDialog({ onClose }: { onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<{ attempt: number; data: AdminFollowups | null; error: string } | null>(null);
  const current = result?.attempt === attempt ? result : null;
  useEffect(() => {
    const element = dialog.current;
    const opener = document.activeElement;
    element?.showModal();
    return () => {
      element?.close();
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus({ preventScroll: true });
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void fetchAdminFollowups(controller.signal).then(data => {
      if (!controller.signal.aborted) setResult({ attempt, data, error: '' });
    }).catch(() => {
      if (!controller.signal.aborted) setResult({ attempt, data: null, error: 'تعذر تحميل المتابعات. تحقق من الاتصال وصلاحية الحساب ثم أعد المحاولة.' });
    });
    return () => controller.abort();
  }, [attempt]);
  return <dialog ref={dialog} onCancel={event => { event.preventDefault(); onClose(); }} aria-labelledby="admin-followups-title" dir="rtl"
    className="m-auto max-h-[85dvh] w-[calc(100%_-_2rem)] max-w-lg overflow-y-auto rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 text-[var(--foreground)] shadow-xl backdrop:bg-black/40">
    <div className="flex flex-wrap items-center justify-between gap-3"><h2 id="admin-followups-title" className="text-lg font-bold">متابعات الإدارة</h2>
      <button className="rounded border px-3 py-2" onClick={onClose} aria-label="إغلاق المتابعات">إغلاق</button></div>
    <p className="my-4 text-sm text-[var(--text-muted)]">أعداد المهام الحالية ضمن صلاحياتك. فتح القائمة لا يحسم مهمة ولا يسندها إليك.</p>
    {!current && <p role="status">جارٍ تحميل المتابعات…</p>}
    {current?.error && <p role="alert">{current.error}</p>}
    {current?.data && <>
      <p className="mb-4 text-xs">وقت القياس: {new Date(current.data.measured_at).toLocaleString('ar-EG')}</p>
      {current.data.results.length === 0 ? <p>لا توجد قوائم متابعة متاحة لهذا الدور.</p> : <ul className="space-y-3">
        {current.data.results.map(row => <li key={row.id} className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-[var(--card-border)] p-3">
          <a className="min-w-0 break-words underline underline-offset-4" href={row.href}>{row.title}</a><span className="font-bold">{row.count}</span>
        </li>)}
      </ul>}
      <p className="mt-4 text-xs text-[var(--text-muted)]">قد تتداخل تذاكر التصعيد مع التذاكر المسندة، لذلك لا تُجمع هذه الأعداد.</p>
    </>}
    <button className="mt-4 rounded border px-4 py-2" disabled={!current} onClick={() => setAttempt(value => value + 1)}>{current?.error ? 'إعادة المحاولة' : 'تحديث المتابعات'}</button>
  </dialog>;
}
