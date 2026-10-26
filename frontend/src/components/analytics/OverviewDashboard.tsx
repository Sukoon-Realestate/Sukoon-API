'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import Link from '@/components/ui/AdminLink';
import { useAuth } from '@/context/AuthContext';
import { BarChartComponent } from '../ui/BarChartComponent';
import { fetchDashboardStats } from '../../lib/api/dashboard';
import { fetchAdminFollowups, type AdminFollowups } from '../../lib/api/followups';
import { fetchFinancialSummary } from '../../lib/api/financials';
import { canOpenAdminPath } from '../../lib/admin-access';
import type { DashboardStatsResponse, FinancialSummary } from '../../lib/api/types';

const panel = 'min-w-0 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 space-y-3';
const destinations = { users: '/users', building: '/properties', clock: '/kyc', revenue: '/financials', calendar: '/analytics', alert: '/users/reports' };
const date = (value: string) => new Date(value).toLocaleString('ar-EG');
type Result = { key: string; dashboard: DashboardStatsResponse | null; followups: AdminFollowups | null; financials: FinancialSummary | null; errors: string[] };

export default function OverviewDashboard() {
  const { user } = useAuth();
  const [refresh, setRefresh] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const canFinance = canOpenAdminPath(user?.allowedPaths, '/financials');
  const key = `${user?.id}:${canFinance}:${refresh}`;
  const current = result?.key === key ? result : null;
  const loading = current === null;
  useEffect(() => {
    const controller = new AbortController();
    void Promise.allSettled([fetchDashboardStats(controller.signal), fetchAdminFollowups(controller.signal),
      canFinance ? fetchFinancialSummary(controller.signal) : Promise.resolve(null)]).then(([dashboard, followups, financials]) => {
      if (controller.signal.aborted) return;
      setResult({ key, dashboard: dashboard.status === 'fulfilled' ? dashboard.value : null,
        followups: followups.status === 'fulfilled' ? followups.value : null,
        financials: financials.status === 'fulfilled' ? financials.value : null,
        errors: [dashboard.status === 'rejected' ? 'ملخص المنصة' : '', followups.status === 'rejected' ? 'مهام المتابعة' : '',
          financials.status === 'rejected' ? 'الملخص المالي' : ''].filter(Boolean) });
    });
    return () => controller.abort();
  }, [key, canFinance]);
  const dashboard = current?.dashboard;
  const followups = current?.followups;
  const finance = current?.financials;
  return <div dir="rtl" className="min-w-0 flex-1 pb-12 [overflow-wrap:anywhere]">
    <Header title="ملخص المنصة" subtitle="مؤشرات المنصة والمهام المتاحة لصلاحياتك الحالية"
      lastUpdated={dashboard ? date(dashboard.period.measured_at) : 'لم تكتمل القراءة'} />
    <main className="mx-auto w-full max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8" aria-busy={loading}>
      <button className="min-h-12 rounded-xl border px-4 py-3" disabled={loading} onClick={() => setRefresh(value => value + 1)}>{loading ? 'جارٍ تحديث البيانات…' : 'تحديث البيانات'}</button>
      {!!current?.errors.length && <p role="alert">تعذر تحميل: {current.errors.join('، ')}. أعد المحاولة لتحديث هذه الأقسام.</p>}
      {dashboard && <>
        <section aria-label="مؤشرات المنصة" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {dashboard.metrics.map(metric => <article className={panel} key={`${metric.icon}:${metric.title}`}>
            <h2>{metric.title}</h2><p className="text-3xl font-bold">{metric.value}</p>
            <p className="text-sm">التغير: {metric.change}</p>
            {canOpenAdminPath(user?.allowedPaths, destinations[metric.icon]) && <Link className="inline-block min-h-12 py-3 underline" href={destinations[metric.icon]}>فتح القسم</Link>}
          </article>)}
        </section>
        <section aria-label="تسجيل الحسابات" className="space-y-3">
          <p>من {date(dashboard.period.from)} إلى {date(dashboard.period.through)}. يمثل كل عمود خمسة أيام.</p>
          <BarChartComponent title="الحسابات الجديدة" data={dashboard.chart_data} periodLabel="آخر 30 يومًا" />
        </section>
      </>}
      {followups && <section className={panel} aria-label="مهام المتابعة">
        <h2 className="font-bold">يحتاج إلى متابعة</h2><p className="text-sm">قراءة المهام: {date(followups.measured_at)}</p>
        {!followups.results.length && <p>لا توجد قوائم متابعة متاحة لهذا الدور.</p>}
        <ul className="grid gap-3 sm:grid-cols-2">{followups.results.map(row => <li key={row.id}>
          <Link href={row.href.replace(/^\/admin/, '') || '/'} className="flex min-h-12 items-center justify-between gap-3 rounded-xl border border-[var(--card-border)] p-4"><span>{row.title}</span><strong>{row.count}</strong></Link>
        </li>)}</ul>
      </section>}
      {dashboard && <section className={panel} aria-label="توزيع الحسابات">
        <h2 className="font-bold">توزيع الحسابات</h2>
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[
          ['إجمالي الحسابات', dashboard.user_distribution.total], ['أصحاب عقارات مدرجة', dashboard.user_distribution.landlords],
          ['الحسابات الأخرى', dashboard.user_distribution.tenants], ['حسابات موثقة الهوية', dashboard.user_distribution.verified],
          ['طلبات توثيق معلقة', dashboard.user_distribution.pending], ['حسابات موقوفة', dashboard.user_distribution.suspended],
        ].map(([label, count]) => <div key={label}><dt>{label}</dt><dd className="text-xl font-bold">{count}</dd></div>)}</dl>
      </section>}
      {canFinance && finance && <section className={panel} aria-label="الملخص المالي">
        <h2 className="font-bold">الإيرادات المسجلة لهذا الشهر</h2><p className="text-2xl font-bold">{finance.metrics.totalRevenueMonth}</p>
        <p>الإيراد المرحّل في السجل المحاسبي بالجنيه المصري. مستحقات الإيجار والتأمين والعمولات غير المكتسبة منفصلة.</p>
        <Link className="inline-block min-h-12 py-3 underline" href="/financials">تفاصيل الإيرادات</Link>
      </section>}
      {dashboard && <section className={panel} aria-label="آخر الأنشطة">
        <h2 className="font-bold">آخر الأنشطة المسجلة</h2>
        {!dashboard.recent_activities.length ? <p>لا توجد أنشطة مسجلة.</p> : <ul className="divide-y divide-[var(--divider)]">{dashboard.recent_activities.map(item => <li key={item.id} className="space-y-1 py-3">
          <p>{item.title}</p><p className="text-sm text-[var(--text-muted)]">{item.time}</p>
        </li>)}</ul>}
        {canOpenAdminPath(user?.allowedPaths, '/system/logs') && <Link className="inline-block min-h-12 py-3 underline" href="/system/logs">سجل التدقيق</Link>}
      </section>}
    </main>
  </div>;
}
