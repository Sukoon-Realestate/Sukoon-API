'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { canOpenAdminPath } from '../../../../../lib/admin-access';
import Link from '@/components/ui/AdminLink';
import { TableScroll } from '@/components/ui/TableScroll';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useToast } from '@/components/ui/Toast';
import { Search, ShieldAlert, Eye, UserX } from 'lucide-react';
import { fetchReports, fetchReportMetrics, takeReportAction } from '@/lib/api/reports';
import { ReportItem, ReportMetrics } from '@/lib/api/types';

function ReportsQueue() {
  const reportId = useSearchParams().get('id');
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'active' | 'suspended' | 'banned'>('active');
  const [searchQuery, setSearchQuery] = useState('');
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [metrics, setMetrics] = useState<ReportMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const { showToast } = useToast();

  useEffect(() => {
    async function loadMetrics() {
      try {
        const res = await fetchReportMetrics();
        if (res) setMetrics(res);
      } catch (err) {
        console.error('Failed to load report metrics:', err);
      }
    }
    loadMetrics();
  }, [refresh]);

  useEffect(() => {
    const controller = new AbortController();
    async function loadReports() {
      setIsLoading(true);
      setError('');
      setReports([]);
      try {
        if (reportId !== null && !/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(reportId)) throw new Error('Invalid report identifier');
        const res = await fetchReports(reportId !== null ? { id: reportId } : { status: activeTab }, controller.signal);
        if (!controller.signal.aborted && res?.results) {
          if (reportId !== null && res.results.some(item => item.id !== reportId)) throw new Error('Unexpected report identity');
          setReports(res.results);
        }
      } catch {
        if (!controller.signal.aborted) setError('تعذر تحميل البلاغات المطلوبة. تحقق من المعرف والصلاحية ثم أعد المحاولة.');
      } finally {
        if (!controller.signal.aborted) setIsLoading(false);
      }
    }
    loadReports();
    return () => controller.abort();
  }, [activeTab, reportId, refresh]);

  const filteredReports = reports.filter((report) => {
    const matchesSearch =
      report.reportedUser.includes(searchQuery) ||
      report.reason.includes(searchQuery) ||
      report.reporter.includes(searchQuery);

    if (!matchesSearch) return false;
    if (reportId !== null) return report.id === reportId;

    if (activeTab === 'suspended') return report.status === 'موقوف مؤقتاً' || report.status === 'suspended';
    if (activeTab === 'banned') return report.status === 'محظور نهائياً' || report.status === 'banned';
    return report.status === 'نشط' || report.status === 'active';
  });

  const handleSuspendUser = async (report: ReportItem) => {
    try {
      await takeReportAction(report.id, 'suspend_user', 'إيقاف بناء على بلاغ مخالفة');
      setReports((prev) =>
        prev.map((r) => (r.id === report.id ? { ...r, status: 'موقوف مؤقتاً' } : r))
      );
      showToast(`تم إيقاف حساب ${report.reportedUser} وتحديث حالة البلاغ`, 'success');
      setRefresh(value => value + 1);
    } catch { showToast('The result was not confirmed. Refresh the original record before retrying.', 'error'); }
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="إدارة المستخدمين – طابور البلاغات"
        subtitle="مراجعة البلاغات الصادرة من المستخدمين والنظام والتحقق الإداري"
      />

      <div className="admin-page-body min-w-0 w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <button className="min-h-12 rounded border px-4 py-3" disabled={isLoading} onClick={() => setRefresh(value => value + 1)}>تحديث البلاغات</button>
        {error && <p role="alert">{error}</p>}
        {isLoading && <p role="status">جارٍ تحميل البلاغات…</p>}
        {reportId !== null && <p>متابعة البلاغ المحدد: <bdi>{reportId}</bdi> · <Link className="underline" href="/users/reports">عرض قائمة البلاغات</Link></p>}
        {/* Top Control Bar: Tabs & Search */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className={`flex items-center gap-2 overflow-x-auto w-full md:w-auto ${reportId !== null ? 'hidden' : ''}`}>
            <button
              onClick={() => setActiveTab('active')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-[var(--shadow-card)] cursor-pointer ${
                activeTab === 'active'
                  ? 'bg-rose-600 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              بلاغات نشطة ({metrics?.active ?? 'غير متاح'})
            </button>
            <button
              onClick={() => setActiveTab('suspended')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-[var(--shadow-card)] cursor-pointer ${
                activeTab === 'suspended'
                  ? 'bg-amber-600 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              موقوف مؤقتاً ({metrics?.suspended ?? 'غير متاح'})
            </button>
            <button
              onClick={() => setActiveTab('banned')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-[var(--shadow-card)] cursor-pointer ${
                activeTab === 'banned'
                  ? 'bg-[var(--card-hover)] dark:bg-slate-600 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              محظور نهائياً ({metrics?.banned ?? 'غير متاح'})
            </button>
          </div>

          <div className="relative w-full md:w-72">
            <input
              type="text"
              placeholder="بحث..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-4 pr-10 py-2 bg-[var(--input-bg)] rounded-xl border border-[var(--input-border)] text-sm text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-rose-500/30 focus:border-rose-500 transition-all placeholder:text-[var(--text-subtle)]"
            />
            <Search className="w-4 h-4 text-[var(--text-subtle)] absolute right-3.5 top-3" />
          </div>
        </div>

        {/* AI System Warning Banner */}
        <div
          className="bg-amber-50/80 dark:bg-amber-500/10 border border-amber-200/80 dark:border-amber-500/20 rounded-2xl p-4 flex items-center gap-3 text-amber-900 dark:text-amber-300 text-xs font-semibold shadow-[var(--shadow-card)]"
          style={{ animationDelay: '50ms' }}
        >
          <ShieldAlert className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0" />
          <span>
            النظام الآلي يكشف البريد المزعج والاحتيال واللغة المسيئة. كل البلاغات تحتاج مراجعة بشرية قبل اتخاذ إجراء.
          </span>
        </div>

        {/* Reports Data Table */}
        <div
          className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden"
          style={{ animationDelay: '100ms' }}
        >
          <TableScroll>
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-[var(--table-header-bg)] border-b border-[var(--card-border)] text-[var(--text-muted)] text-xs font-bold">
                  <th className="py-4 px-6">المستخدم المُبلّغ عنه</th>
                  <th className="py-4 px-6">النوع</th>
                  <th className="py-4 px-6">سبب البلاغ</th>
                  <th className="py-4 px-6">المُبلِّغ</th>
                  <th className="py-4 px-6">التاريخ</th>
                  <th className="py-4 px-6">الأتمتة</th>
                  <th className="py-4 px-6 text-center">إجراء</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--table-border)] text-sm">
                {filteredReports.length > 0 ? (
                  filteredReports.map((report) => (
                    <tr
                      key={report.id}
                      className="hover:bg-[var(--table-row-hover)] transition-colors"
                    >
                      <td className="py-4 px-6 font-bold text-[var(--foreground)]">
                        {report.reportedUser}
                      </td>
                      <td className="py-4 px-6">
                        <StatusBadge type="userType" value={report.userType} />
                      </td>
                      <td className="py-4 px-6 text-[var(--foreground)] font-medium">
                        {report.reason}
                      </td>
                      <td className="py-4 px-6 text-[var(--text-muted)] font-medium text-xs">
                        {report.reporter}
                      </td>
                      <td className="py-4 px-6 text-xs text-[var(--text-subtle)] font-medium">
                        {report.date}
                      </td>
                      <td className="py-4 px-6">
                        <StatusBadge
                          type="automation"
                          value={report.automationLevelDisplay || report.automation_level}
                        />
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center justify-center gap-2">
                          {canOpenAdminPath(user?.allowedPaths, report.chatPolicyCaseId ? '/reports/chat-policy' : '/users') && <Link
                            href={report.chatPolicyCaseId ? '/reports/chat-policy' : `/users/${report.reportedUserId}`}
                            className="inline-flex items-center gap-1 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>مراجعة</span>
                          </Link>}
                          {!report.chatPolicyCaseId && canOpenAdminPath(user?.allowedPaths, '/users') && <button
                            onClick={() => handleSuspendUser(report)}
                            className="inline-flex items-center gap-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                          >
                            <UserX className="w-3.5 h-3.5" />
                            <span>إيقاف</span>
                          </button>}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={7}
                      className="py-12 text-center text-[var(--text-subtle)] font-medium"
                    >
                      {isLoading ? 'جارٍ التحميل…' : error ? 'لم تتأكد نتيجة القراءة.' : reportId !== null ? 'البلاغ المحدد غير متاح. لم يُفتح بلاغ بديل.' : 'لا توجد بلاغات تطابق البحث الحالي.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </TableScroll>
        </div>
      </div>
    </div>
  );
}

export default function ReportsQueuePage() {
  return <Suspense fallback={<p role="status">جارٍ تحميل البلاغات…</p>}><ReportsQueue /></Suspense>;
}
