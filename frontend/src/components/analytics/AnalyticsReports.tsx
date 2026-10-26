'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { BarChartComponent } from '../ui/BarChartComponent';
import { fetchAnalyticsStats } from '../../lib/api/analytics';
import type { AnalyticsPeriod, AnalyticsStats } from '../../lib/api/types';

type Result = { key: string; data: AnalyticsStats | null; error: string };
const panel = 'rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5';

function measuredAt(value: string) {
  return new Date(value).toLocaleString('ar-EG');
}

export default function AnalyticsReports() {
  const [period, setPeriod] = useState<AnalyticsPeriod>('30');
  const [refresh, setRefresh] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const key = `${period}:${refresh}`;
  const current = result?.key === key ? result : null;
  const stats = current?.data;
  const busy = current === null;

  useEffect(() => {
    const controller = new AbortController();
    void fetchAnalyticsStats(period, controller.signal).then(data => {
      if (!controller.signal.aborted) setResult({ key, data, error: '' });
    }).catch(() => {
      if (!controller.signal.aborted) setResult({ key, data: null, error: 'تعذر تحميل التحليلات لهذه الفترة. أعد المحاولة.' });
    });
    return () => controller.abort();
  }, [period, key]);

  return <div dir="rtl" className="flex-1 pb-12">
    <Header title="التحليلات والتقارير" subtitle="طلبات المعاينة والتقييمات خلال الفترة، وحالة الحسابات والعقارات الحالية"
      lastUpdated={stats ? measuredAt(stats.snapshot_measured_at) : 'لم تُحمّل البيانات'} />
    <main className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-bold">مؤشرات الأداء</h1>
        <div className="flex flex-wrap gap-2" aria-label="فترة التحليلات">
          {(['7', '30', '90'] as const).map(value => <button key={value} aria-pressed={period === value}
            className={`rounded-lg border px-3 py-2 ${period === value ? 'bg-teal-700 text-white' : ''}`}
            onClick={() => setPeriod(value)}>آخر {value} أيام</button>)}
          <button className="rounded-lg border px-3 py-2" disabled={busy} onClick={() => setRefresh(value => value + 1)}>تحديث</button>
        </div>
      </div>
      {busy && <p role="status">جارٍ تحميل التحليلات…</p>}
      {current?.error && <div role="alert" className={panel}><p>{current.error}</p>
        <button className="mt-3 rounded border px-3 py-2" onClick={() => setRefresh(value => value + 1)}>إعادة المحاولة</button></div>}
      {stats && <>
        <p className="text-sm text-[var(--text-muted)]">من {measuredAt(stats.period.from)} إلى {measuredAt(stats.period.through)}.
          تُحسب الطلبات حسب تاريخ إنشائها، والمكتملة منها حسب إفادة حضور محفوظة حتى وقت القياس. التقييمات حسب تاريخ تسجيلها.</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ['طلبات المعاينة', stats.visitRequests, stats.visitRequestsChange],
            ['طلبات الفترة ذات حضور مؤكد', stats.completedVisits, stats.completedVisitsChange],
            ['متوسط التقييم المسجل', stats.avgRating, stats.avgRatingChange],
            ['معدل الاحتفاظ', stats.retentionRate, stats.retentionRateChange],
          ].map(([label, value, change]) => <dl key={label} className={panel}>
            <dt className="text-sm">{label}</dt><dd className="my-2 text-2xl font-bold">{value}</dd>
            <dd className="text-xs text-[var(--text-muted)]">التغير: {change}</dd>
          </dl>)}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="min-w-0">
            <BarChartComponent title="طلبات المعاينة خلال الفترة" data={stats.dailyChart} periodLabel={`${stats.period.days} أيام`} />
            <p className="mt-2 text-xs text-[var(--text-muted)]">كل عمود يمثل 24 ساعة بدءًا من بداية الفترة المعروضة.</p>
            <details className="mt-3"><summary className="cursor-pointer">عرض أعداد الطلبات بالتاريخ</summary>
              <div className="max-h-72 overflow-auto"><table className="mt-2 w-full text-right text-sm"><caption>بداية كل فترة وعدد الطلبات</caption>
                <thead><tr><th scope="col">البداية</th><th scope="col">الطلبات</th></tr></thead><tbody>
                  {stats.dailyChart.map(row => <tr key={row.from}><th scope="row" className="font-normal">{measuredAt(row.from)}</th><td>{row.value}</td></tr>)}
                </tbody></table></div>
            </details>
          </section>
          <section className={panel}>
            <h2 className="mb-4 font-bold">أكثر المناطق طلبًا للمعاينة</h2>
            <p className="mb-4 text-xs text-[var(--text-muted)]">حسب طلبات الفترة والمنطقة المسجلة حاليًا للعقار. الطلبات دون منطقة لا تدخل هذا التوزيع.</p>
            {stats.topRegions.length === 0 && <p>لا توجد طلبات ذات منطقة مسجلة خلال الفترة.</p>}
            <ul className="space-y-4">{stats.topRegions.map(region => <li key={region.name}>
              <div className="mb-2 flex justify-between gap-3"><span>{region.name}</span><span>{region.count} طلب</span></div>
              <div className="h-2 rounded bg-[var(--badge-bg-muted)]" aria-hidden="true"><div className="h-full rounded bg-teal-700"
                style={{ width: `${region.count / Math.max(1, ...stats.topRegions.map(item => item.count)) * 100}%` }} /></div>
            </li>)}</ul>
          </section>
        </div>
        <section className="space-y-4"><h2 className="font-bold">الحالة الحالية عند القياس — لا تتقيد بالفترة المختارة</h2>
          <div className="grid gap-6 md:grid-cols-2">
            <section className={panel}><h3 className="mb-4 font-bold">آخر حالة توثيق لكل حساب</h3><dl className="space-y-3">
              {stats.kycBreakdown.map(item => <div className="flex justify-between gap-3" key={item.label}><dt>{item.label}</dt><dd>{item.count} ({item.pct})</dd></div>)}
            </dl></section>
            <section className={panel}><h3 className="mb-4 font-bold">حالات مراجعة العقارات</h3><dl className="space-y-3">
              {stats.propertyActivity.map(item => <div className="flex justify-between gap-3" key={item.label}><dt>{item.label}</dt><dd>{item.count}</dd></div>)}
            </dl><p className="mt-4 text-xs text-[var(--text-muted)]">الاعتماد حالة مراجعة، ولا يثبت إتاحة السكن للحجز.</p></section>
          </div>
        </section>
      </>}
    </main>
  </div>;
}
