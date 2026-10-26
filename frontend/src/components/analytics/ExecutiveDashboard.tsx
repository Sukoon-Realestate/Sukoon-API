'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { BarChartComponent } from '../ui/BarChartComponent';
import { fetchExecutiveDashboardStats } from '../../lib/api/dashboard';
import type { ExecutiveDashboardStats } from '../../lib/api/types';

export default function ExecutiveDashboard() {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<{ attempt: number; data: ExecutiveDashboardStats | null; error: string } | null>(null);
  const current = result?.attempt === attempt ? result : null;
  const data = current?.data;
  useEffect(() => {
    const controller = new AbortController();
    void fetchExecutiveDashboardStats(controller.signal).then(data => {
      if (!controller.signal.aborted) setResult({ attempt, data, error: '' });
    }).catch(() => {
      if (!controller.signal.aborted) setResult({ attempt, data: null, error: 'تعذر تحميل مؤشرات الإدارة. أعد المحاولة.' });
    });
    return () => controller.abort();
  }, [attempt]);
  return <div dir="rtl" className="flex-1 pb-12">
    <Header title="لوحة التحكم التنفيذية" subtitle="مؤشرات من السجلات الحالية والنشاط المسجل خلال آخر 30 يومًا"
      lastUpdated={data ? new Date(data.period.measured_at).toLocaleString('ar-EG') : 'لم تُحمّل البيانات'} />
    <main className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
      <button className="rounded border px-4 py-2" disabled={!current} onClick={() => setAttempt(value => value + 1)}>{current?.error ? 'إعادة المحاولة' : 'تحديث المؤشرات'}</button>
      {!current && <p role="status">جارٍ تحميل المؤشرات…</p>}
      {current?.error && <p role="alert">{current.error}</p>}
      {data && <>
        <section aria-label="مؤشرات الإدارة" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {data.executiveMetrics.map(metric => <dl key={metric.title} className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5">
            <dt className="text-sm">{metric.title}</dt><dd className="my-3 text-2xl font-bold">{metric.value}</dd>
            <dd className="text-xs text-[var(--text-muted)]">التغير: {metric.change}</dd>
          </dl>)}
        </section>
        <p className="text-sm text-[var(--text-muted)]">الفترة من {data.period.from} إلى {data.period.through} بتوقيت النظام، واليوم الحالي حتى وقت القياس. الحساب المفعّل لا يعني أنه متصل الآن، واعتماد العقار لا يثبت إتاحته للحجز.</p>
        <div className="grid gap-6 lg:grid-cols-2">
          <BarChartComponent title="تسجيل الحسابات خلال الفترة" data={data.monthlyUserChartData} periodLabel="30 يومًا" />
          <BarChartComponent title="البلاغات المسجلة خلال الفترة" data={data.reportTrendData} color="red" periodLabel="30 يومًا" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5"><h2 className="mb-4 font-bold">حالة الحسابات الحالية</h2><dl className="space-y-3">
            {[
              ['إجمالي الحسابات', data.userDistribution.total],
              ['حسابات لها عقارات مدرجة', data.userDistribution.landlords],
              ['حسابات دون عقار مدرج', data.userDistribution.tenants],
              ['حسابات موثقة الهوية', data.userDistribution.verified],
              ['حسابات موقوفة', data.userDistribution.suspended],
            ].map(([label, value]) => <div key={label} className="flex justify-between gap-4"><dt>{label}</dt><dd>{value.toLocaleString()}</dd></div>)}
          </dl></section>
          <section className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5"><h2 className="mb-4 font-bold">آخر أنشطة التسجيل والعقارات والتوثيق</h2>
            {data.executiveActivities.length === 0 ? <p>لا توجد أنشطة مسجلة.</p> : <ul className="space-y-4">
              {data.executiveActivities.map(item => <li key={item.id} className="border-b border-[var(--divider)] pb-3"><p className="break-words">{item.title}</p><p className="mt-1 text-xs text-[var(--text-muted)]">{item.time} · {item.role}</p></li>)}
            </ul>}
          </section>
        </div>
      </>}
    </main>
  </div>;
}
