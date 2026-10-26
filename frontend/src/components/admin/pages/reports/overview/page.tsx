'use client';

import { useEffect, useState } from 'react';
import Link from '@/components/ui/AdminLink';
import { TableScroll } from '@/components/ui/TableScroll';
import { Header } from '@/components/layout/Header';
import { fetchReportsOverview } from '@/lib/api/reports';
import type { ReportsOverviewStats } from '@/lib/api/types';

const panel = 'min-w-0 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4 sm:p-5 space-y-3';
const tabs = [['all', 'كل البلاغات'], ['خلاف', 'خلاف'], ['بلاغ عقار', 'بلاغ عقار'], ['بلاغ مستخدم', 'بلاغ مستخدم']];
export default function ReportsOverviewPage() {
  const [tab, setTab] = useState('all');
  const [refresh, setRefresh] = useState(0);
  const [result, setResult] = useState<{ key: number; data: ReportsOverviewStats | null } | null>(null);
  const current = result?.key === refresh ? result : null;
  const loading = !current;
  const data = current?.data;
  useEffect(() => {
    const controller = new AbortController();
    void fetchReportsOverview(controller.signal).then(data => {
      if (!controller.signal.aborted) setResult({ key: refresh, data });
    }).catch(() => { if (!controller.signal.aborted) setResult({ key: refresh, data: null }); });
    return () => controller.abort();
  }, [refresh]);
  const tickets = data?.tickets.filter(item => tab === 'all' || item.type === tab) ?? [];
  const reasonsTotal = data?.disputeReasons.reduce((sum, item) => sum + item.count, 0) ?? 0;
  return <div dir="rtl" className="min-w-0 flex-1 pb-12 [overflow-wrap:anywhere]">
    <Header title="متابعة البلاغات" subtitle="بلاغات المستخدمين ونتائج مراجعتها وسجل المعاينات"
      lastUpdated={data ? new Date(data.measured_at).toLocaleString('ar-EG') : 'لم تكتمل القراءة'} />
    <main className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8" aria-busy={loading}>
      <button className="min-h-12 rounded-xl border px-4 py-3" disabled={loading} onClick={() => setRefresh(value => value + 1)}>{loading ? 'جارٍ تحديث البلاغات…' : 'تحديث البلاغات'}</button>
      {current && !data && <p role="alert">تعذر تحميل البلاغات. أعد المحاولة للتحقق من حالتها الحالية.</p>}
      {data && <>
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="مؤشرات البلاغات">
          {[
            ['متوسط وقت الحل', data.metrics.avgResolutionTime], ['بلاغات نشطة: الاحتيال والوصف وأسباب أخرى', data.metrics.activeDisputes],
            ['بلاغات حُسمت اليوم', data.metrics.solvedToday], ['البلاغات النشطة', data.metrics.openTickets],
          ].map(([label, count]) => <dl className={panel} key={label}><dt>{label}</dt><dd className="text-2xl font-bold">{count}</dd></dl>)}
        </section>
        <section className={panel} aria-label="البلاغات الحالية">
          <h2 className="font-bold">أحدث 20 بلاغًا</h2>
          <div className="flex flex-wrap gap-2">{tabs.map(([value, label]) => <button key={value} className="min-h-12 rounded-lg border px-3 py-2" aria-pressed={tab === value} onClick={() => setTab(value)}>{label}</button>)}</div>
          {!tickets.length ? <p>لا توجد بلاغات مطابقة في هذه القراءة.</p> : <TableScroll label="أحدث البلاغات"><table className="w-full text-start text-sm">
            <thead><tr>{['البلاغ', 'الموضوع', 'المبلغ', 'النوع', 'الحالة', 'المراجع'].map(label => <th className="p-3 text-start" scope="col" key={label}>{label}</th>)}</tr></thead>
            <tbody>{tickets.map(ticket => <tr className="border-t border-[var(--divider)]" key={ticket.rawId ?? ticket.id}>
              <th className="p-3 text-start" scope="row">{ticket.rawId ? <Link className="inline-block min-h-12 py-3 underline" href={`/users/reports?id=${encodeURIComponent(ticket.rawId)}`}>{ticket.id}</Link> : ticket.id}</th>
              <td className="p-3">{ticket.subject}</td><td className="p-3">{ticket.reporter}</td><td className="p-3">{ticket.type}</td><td className="p-3">{ticket.status}</td><td className="p-3">{ticket.reviewer}</td>
            </tr>)}</tbody>
          </table></TableScroll>}
        </section>
        <section className={panel} aria-label="أسباب البلاغات">
          <h2 className="font-bold">أسباب البلاغات المسجلة</h2><p>جميع الحالات، بما فيها المغلقة. الإجمالي: {reasonsTotal}</p>
          <ul className="space-y-4">{data.disputeReasons.map(item => <li key={item.title}><p>{item.title}: {item.count}</p>
            <div className="mt-2 h-2 overflow-hidden rounded bg-[var(--card-hover)]" aria-hidden="true"><div className="h-full bg-teal-700" style={{ width: `${reasonsTotal ? item.count / reasonsTotal * 100 : 0}%` }} /></div>
          </li>)}</ul>
        </section>
        <section className={panel} aria-label="سجل المعاينات">
          <h2 className="font-bold">آخر المعاينات المسجلة</h2>
          {!data.bookingLog.length ? <p>لا توجد معاينات مسجلة.</p> : <ul className="space-y-4">{data.bookingLog.map(item => <li key={item.id}><p>{item.title} · {item.status}</p><bdi className="text-xs">{item.id}</bdi></li>)}</ul>}
        </section>
      </>}
    </main>
  </div>;
}
