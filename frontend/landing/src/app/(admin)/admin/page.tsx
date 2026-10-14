'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { ArrowUpLeft, Building2, ShieldCheck, Headphones, RotateCw, AlertCircle, Users, Wallet } from 'lucide-react';
import { Header } from '@/components/layout/Header';
import Link from '@/components/ui/AdminLink';
import { MetricCard } from '@/components/ui/MetricCard';
import { BarChartComponent } from '@/components/ui/BarChartComponent';
import { ActivityFeed } from '@/components/ui/ActivityFeed';
import { QuickActionsToolbar } from '@/components/ui/QuickActionsToolbar';
import { SkeletonLoader } from '@/components/ui/SkeletonLoader';
import { sumAvailableCounts } from '@/lib/admin-dashboard';
import { fetchDashboardStats } from '@/lib/api/dashboard';
import { fetchAdminPropertyMetrics } from '@/lib/api/properties';
import { fetchSupportMetrics } from '@/lib/api/support';
import { fetchFinancialSummary } from '@/lib/api/financials';
import type { DashboardStatsResponse, PropertyMetrics, SupportMetrics, FinancialSummary } from '@/lib/api/types';

export default function OverviewDashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardStatsResponse | null>(null);
  const [properties, setProperties] = useState<PropertyMetrics | null>(null);
  const [support, setSupport] = useState<SupportMetrics | null>(null);
  const [financials, setFinancials] = useState<FinancialSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  const load = useCallback(async () => {
    const [stats, propertyStats, supportStats, financialStats] = await Promise.allSettled([
      fetchDashboardStats(), fetchAdminPropertyMetrics(), fetchSupportMetrics(), fetchFinancialSummary(),
    ]);
    setDashboard(stats.status === 'fulfilled' ? stats.value : null);
    setProperties(propertyStats.status === 'fulfilled' ? propertyStats.value : null);
    setSupport(supportStats.status === 'fulfilled' ? supportStats.value : null);
    setFinancials(financialStats.status === 'fulfilled' ? financialStats.value : null);
    setFailed([stats, propertyStats, supportStats, financialStats].some((result) => result.status === 'rejected'));
    setLoading(false);
  }, []);
  useEffect(() => { void Promise.resolve().then(load); }, [load]);

  const distribution = dashboard?.user_distribution;
  const total = distribution?.total || 0;
  const percent = (value: number) => total ? Math.min(100, Math.round(value / total * 100)) : 0;
  const pendingTotal = sumAvailableCounts([distribution?.pending, properties?.pending, support?.openTickets]);
  const display = (value?: number) => loading ? '…' : value === undefined ? '—' : value.toLocaleString('en-US');
  const queue = [
    { title: 'عقارات بانتظار المراجعة', description: 'راجع التفاصيل والصور قبل النشر', href: '/properties/review', icon: Building2, value: properties?.pending },
    { title: 'طلبات توثيق الهوية', description: 'تحقق من مستندات الملاك والمستأجرين', href: '/kyc', icon: ShieldCheck, value: distribution?.pending },
    { title: 'تذاكر دعم مفتوحة', description: 'تابع أسئلة ومشكلات المستخدمين', href: '/support', icon: Headphones, value: support?.openTickets },
  ];

  return <div className="flex-1 flex flex-col pb-10">
    <Header title="ملخص المنصة" subtitle="أداء الأعمال وما يحتاج إلى متابعة، في مكان واحد." />
    <div className="admin-page-body space-y-6">
      <div className="admin-overview-intro"><p>تابع نمو سكون، ثم انتقل إلى العمل الأهم.</p><button className="admin-button admin-button-secondary" onClick={() => { setLoading(true); setFailed(false); void load(); }} disabled={loading}><RotateCw size={15} className={loading ? 'animate-spin' : ''} aria-hidden />{loading ? 'جاري التحديث' : 'تحديث البيانات'}</button></div>
      {failed && <div role="alert" className="admin-error"><AlertCircle size={19} aria-hidden /><p>تعذر تحميل بعض المؤشرات. البيانات المتاحة ما زالت ظاهرة؛ جرّب تحديث البيانات.</p><button onClick={() => { setLoading(true); setFailed(false); void load(); }} disabled={loading}>إعادة المحاولة</button></div>}
      {loading && !dashboard ? <SkeletonLoader variant="metric" count={4} /> : dashboard?.metrics.length ? <section aria-label="مؤشرات الأداء" className="admin-metrics-grid">{dashboard.metrics.map((metric) => <MetricCard key={`${metric.icon}-${metric.title}`} metric={metric} />)}</section> : <div className="admin-panel admin-inline-empty">لا تتوفر مؤشرات أداء حالياً. استخدم تحديث البيانات للمحاولة مجدداً.</div>}
      <div className="admin-overview-grid">
        <OverviewDataState title="نمو المستخدمين" loading={loading} available={Boolean(dashboard)}><BarChartComponent title="نمو المستخدمين" data={dashboard?.chart_data || []} periodLabel="آخر 30 يوماً" /></OverviewDataState>
        <section className="admin-panel admin-queue"><div className="admin-panel-heading"><div><h2>يحتاج إلى متابعة</h2><p>المراجعات والتذاكر المفتوحة</p></div><span className="admin-queue-total">{loading ? '…' : pendingTotal === null ? '—' : pendingTotal.toLocaleString('en-US')}</span></div>
          <div className="admin-queue-list">{queue.map((item) => { const Icon = item.icon; return <Link href={item.href} key={item.href}><span className="admin-queue-icon"><Icon size={19} strokeWidth={1.7} aria-hidden /></span><span className="min-w-0 flex-1"><strong>{item.title}</strong><small>{item.description}</small></span><b>{display(item.value)}</b><ArrowUpLeft size={16} aria-hidden /></Link>; })}</div>
          <Link href="/reports/overview" className="admin-queue-footer">متابعة البلاغات وتسويتها<ArrowUpLeft size={16} aria-hidden /></Link>
        </section>
      </div>
      <div className="admin-overview-secondary">
        <section className="admin-panel admin-community"><div className="admin-panel-heading"><div><h2>مجتمع سكون</h2><p>توزيع الحسابات وحالة التوثيق</p></div><Users size={21} strokeWidth={1.5} aria-hidden /></div>
          <div className="admin-community-total"><strong>{display(distribution?.total)}</strong><span>مستخدم على المنصة</span></div>
          {distribution && <div className="admin-composition-bar" role="img" aria-label={`المستأجرون ${percent(distribution?.tenants || 0)}٪، الملاك ${percent(distribution?.landlords || 0)}٪`}><span style={{ width: `${percent(distribution?.tenants || 0)}%` }} /><span style={{ width: `${percent(distribution?.landlords || 0)}%` }} /></div>}
          <div className="admin-composition-legend"><span><i />مستأجرون <strong>{display(distribution?.tenants)}</strong></span><span><i />ملاك <strong>{display(distribution?.landlords)}</strong></span></div>
          <dl className="admin-status-summary"><div><dt>موثقون</dt><dd>{display(distribution?.verified)}</dd></div><div><dt>قيد التوثيق</dt><dd>{display(distribution?.pending)}</dd></div><div><dt>موقوفون</dt><dd>{display(distribution?.suspended)}</dd></div></dl>
        </section>
        <section className="admin-panel admin-business-summary"><div className="admin-panel-heading"><div><h2>الأداء المالي</h2><p>ملخص إيرادات الشهر</p></div><Wallet size={21} strokeWidth={1.5} aria-hidden /></div><div className="admin-revenue-value" dir="auto">{loading ? '…' : financials?.metrics.totalRevenueMonth || '—'}</div><span className="text-sm text-[var(--text-muted)]">إجمالي إيرادات الشهر</span><dl><div><dt>رسوم المنصة</dt><dd dir="auto">{financials?.metrics.platformFees || '—'}</dd></div><div><dt>المعاملات النشطة</dt><dd dir="auto">{financials?.metrics.activeTransactions || '—'}</dd></div></dl><Link href="/financials" className="admin-text-link">عرض تفاصيل الإيرادات<ArrowUpLeft size={16} aria-hidden /></Link></section>
      </div>
      <OverviewDataState title="آخر الأنشطة" loading={loading} available={Boolean(dashboard)}><ActivityFeed activities={dashboard?.recent_activities || []} /></OverviewDataState>
      <QuickActionsToolbar />
    </div>
  </div>;
}

function OverviewDataState({ title, loading, available, children }: { title: string; loading: boolean; available: boolean; children: ReactNode }) {
  if (available) return children;
  return <section className="admin-panel" aria-busy={loading}><div className="admin-panel-heading"><h2>{title}</h2></div>{loading ? <div className="px-6 pb-6 space-y-3 animate-pulse" role="status"><span className="sr-only">جاري تحميل {title}</span><div className="h-4 w-1/2 rounded bg-[var(--card-hover)]" /><div className="h-40 rounded bg-[var(--card-hover)]" /></div> : <p role="status" className="admin-inline-empty">تعذر تحميل هذا القسم. استخدم تحديث البيانات لإعادة المحاولة.</p>}</section>;
}
