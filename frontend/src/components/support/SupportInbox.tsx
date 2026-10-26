'use client';

import { Header } from '@/components/layout/Header';

import { useEffect, useState } from 'react';
import Link from '@/components/ui/AdminLink';
import { fetchSupportMetrics, fetchSupportTickets } from '../../lib/api/support';
import { SupportMetrics, SupportTicket } from '../../lib/api/types';

export default function SupportInbox() {
  const [tab, setTab] = useState('all');
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [metrics, setMetrics] = useState<SupportMetrics | null>(null);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const queryKey = JSON.stringify([tab, page, refresh]);
  const [loadedKey, setLoadedKey] = useState('');
  const busy = loadedKey !== queryKey;
  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([fetchSupportTickets({ tab, page, page_size: 20 }, controller.signal), fetchSupportMetrics(controller.signal)])
      .then(([result, values]) => {
        if (controller.signal.aborted) return;
        setTickets(result.results); setCount(result.count); setMetrics(values); setError('');
      }).catch(e => { if (!controller.signal.aborted) { setTickets([]); setMetrics(null); setError(e.message); } })
      .finally(() => { if (!controller.signal.aborted) setLoadedKey(queryKey); });
    return () => controller.abort();
  }, [tab, page, refresh, queryKey]);
  return <>
    <Header title="تذاكر الدعم" />
    <section dir="rtl" className="mx-auto w-full max-w-5xl space-y-5 p-4 sm:p-8">
    <p>المحادثات المحفوظة وإسناد المسؤول ومتابعة التصعيد.</p>
    <button className="border rounded px-4 py-2" disabled={busy} onClick={() => setRefresh(value => value + 1)}>تحديث القائمة</button>
    {!busy && error && <p role="alert">{error}</p>}
    {!busy && metrics && <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">{[['مفتوحة', metrics.openTickets], ['قيد المعالجة', metrics.inProgress], ['محلولة اليوم', metrics.solvedToday], ['متوسط مدة الحل المسجلة', metrics.avgResolutionTime]].map(([label, value]) => <div className="rounded border p-4" key={label}><dt>{label}</dt><dd className="text-xl font-bold">{value}</dd></div>)}</dl>}
    <nav aria-label="تصفية التذاكر" className="flex flex-wrap gap-2">{[['all', 'كل التذاكر'], ['high', 'قائمة تصعيد المشرفين'], ['landlord', 'مساحة المالك'], ['tenant', 'مساحات الباحثين']].map(([value, label]) => <button className="rounded border px-4 py-2" aria-pressed={tab === value} key={value} onClick={() => { setTab(value); setPage(1); }}>{label}</button>)}</nav>
    {busy ? <p role="status">جارٍ تحميل التذاكر…</p> : <section className="space-y-3">{tickets.length === 0 && !error && <p>لا توجد تذاكر ضمن هذا القسم.</p>}{tickets.map(ticket => <article key={ticket.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4"><div><h2 className="font-bold">{ticket.subject}</h2><p>{ticket.user} · {ticket.status}</p><p>المسؤول: {ticket.assignedTo || 'لم تُسند بعد'}</p></div><Link className="underline" href={`/support/${encodeURIComponent(ticket.rawId || ticket.id)}`}>فتح التذكرة</Link></article>)}</section>}
    <div className="flex gap-3"><button disabled={busy || page <= 1} onClick={() => setPage(value => value - 1)}>السابق</button><span>{page}</span><button disabled={busy || page * 20 >= count} onClick={() => setPage(value => value + 1)}>التالي</button></div>
  </section></>;
}
