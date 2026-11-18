'use client';

import React, { useState, useEffect, useRef } from 'react';
import { TableScroll } from '@/components/ui/TableScroll';
import { Header } from '@/components/layout/Header';
import { Search, Download } from 'lucide-react';
import { fetchAuditLogs } from '@/lib/api/system';
import { Pagination } from '@/components/ui/Pagination';
import { auditLogPage, downloadAuditLogPage, type AuditLogPage } from '@/lib/api/auditLogs';

export default function SystemAuditLogsPage() {
  type AuditType = 'all' | 'system' | 'users' | 'props' | 'kyc';
  const [query, setQuery] = useState({ type: 'all' as AuditType, search: '', page: 1 });
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ key: string; page: AuditLogPage | null; failed: boolean }>({
    key: '', page: null, failed: false,
  });
  const [exportMessage, setExportMessage] = useState('');
  const [exportFailed, setExportFailed] = useState(false);
  const version = useRef(0);
  const requestKey = JSON.stringify([query.type, query.search, query.page, retry]);
  const activeTab = query.type;
  const searchQuery = query.search;
  const isLoading = result.key !== requestKey;
  const hasError = !isLoading && result.failed;
  const currentPage = !isLoading && !hasError ? result.page : null;
  const logs = currentPage?.results ?? [];

  function filter(type: AuditType, search: string) {
    if (type === query.type && search === query.search) return;
    version.current += 1;
    setExportMessage('');
    setQuery({ type, search, page: 1 });
  }

  function changePage(page: number) {
    if (!currentPage || !Number.isSafeInteger(page) || page < 1 ||
        page > currentPage.total_pages || page === query.page) return;
    version.current += 1;
    setExportMessage('');
    setQuery({ ...query, page });
  }

  function exportPage() {
    if (!currentPage || logs.length === 0) return;
    try {
      downloadAuditLogPage(currentPage);
      setExportFailed(false);
      setExportMessage(`تم تجهيز ${logs.length} سجل من الصفحة ${query.page} للتنزيل.`);
    } catch {
      setExportFailed(true);
      setExportMessage('تعذر تجهيز ملف CSV. أعد المحاولة.');
    }
  }

  useEffect(() => {
    let cancelled = false;
    const requestVersion = ++version.current;
    const timer = setTimeout(async () => {
      try {
        const response = await fetchAuditLogs({
          type: query.type,
          search: query.search.trim() || undefined,
          page: query.page,
        });
        const page = auditLogPage(response, query.page);
        if (!cancelled && requestVersion === version.current) {
          setResult({ key: requestKey, page, failed: false });
        }
      } catch {
        if (!cancelled && requestVersion === version.current) {
          setResult({ key: requestKey, page: null, failed: true });
        }
      }
    }, 300);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [query.type, query.search, query.page, requestKey]);

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="سجل النشاط – Activity Logs"
        subtitle="سجل العمليات والإجراءات الإدارية، التحركات الحية وتتبع المشرفين"
      />

      <div className="admin-page-body min-w-0 w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Top Control Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-72">
            <input
              type="text"
              placeholder="بحث في السجل..."
              value={searchQuery}
              onChange={(e) => filter(query.type, e.target.value)}
              className="w-full pl-4 pr-10 py-2 bg-[var(--card-bg)] rounded-full border border-[var(--card-border)] text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-[#0D7C66] transition-all placeholder:text-[var(--text-subtle)] text-[var(--foreground)]"
            />
            <Search className="w-4 h-4 text-[var(--text-subtle)] absolute right-3.5 top-2.5" />
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto justify-start md:justify-end">
            <button
              onClick={() => filter('all', query.search)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'all'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              كل الإجراءات
            </button>
            <button
              onClick={() => filter('kyc', query.search)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'kyc'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              KYC
            </button>
            <button
              onClick={() => filter('props', query.search)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'props'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              عقارات
            </button>
            <button
              onClick={() => filter('users', query.search)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'users'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              مستخدمون
            </button>
            <button
              onClick={() => filter('system', query.search)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'system'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              نظام
            </button>
            <button onClick={exportPage} disabled={!currentPage || logs.length === 0} className="disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 bg-[var(--card-bg)] px-4 py-1.5 rounded-full border border-[var(--card-border)] text-xs font-bold text-[var(--foreground)] hover:bg-[var(--card-hover)] transition-colors shadow-[var(--shadow-card)] cursor-pointer">
              <Download className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              <span>تصدير الصفحة CSV</span>
            </button>
          </div>
        </div>

        <p className="text-xs text-[var(--text-muted)]">
          تصدير CSV يشمل سجلات الصفحة المعروضة فقط وفق البحث والتصفية الحاليين، وليس جميع صفحات السجل.
        </p>
        {exportMessage && <p role={exportFailed ? 'alert' : 'status'}>{exportMessage}</p>}
        {/* Audit Log Table Container */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden">
          <TableScroll>
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-[var(--table-header-bg)] border-b border-[var(--card-border)] text-[var(--text-muted)] text-xs font-bold">
                  <th className="py-4 px-6">الوقت</th>
                  <th className="py-4 px-6">الإجراء</th>
                  <th className="py-4 px-6">النوع</th>
                  <th className="py-4 px-6">المستهدف</th>
                  <th className="py-4 px-6">المشرف</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--divider)] text-xs">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-[var(--text-subtle)] font-medium">
                      جاري تحميل السجل...
                    </td>
                  </tr>
                ) : hasError ? (
                  <tr><td colSpan={5} className="py-8 text-center">
                    <div role="alert">تعذر تحميل سجل النشاط. لا يمكن تأكيد النتائج.</div>
                    <button onClick={() => { setExportMessage(''); setRetry(value => value + 1); }}
                      className="mt-3 rounded-lg border px-4 py-2">إعادة المحاولة</button>
                  </td></tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-[var(--text-subtle)] font-medium">
                      لا توجد سجلات مطابقة
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr
                      key={log.id}
                      className="hover:bg-[var(--table-row-hover)] transition-colors"
                    >
                      <td className="py-4 px-6 font-mono text-[var(--text-subtle)] font-semibold dir-ltr text-right">
                        {log.time}
                      </td>
                      <td className="py-4 px-6 font-bold text-[var(--foreground)]">
                        {log.action}
                      </td>
                      <td className="py-4 px-6">
                        {log.typeBadge === 'KYC' && (
                          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800">
                            KYC
                          </span>
                        )}
                        {log.typeBadge === 'عقار' && (
                          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800">
                            عقار
                          </span>
                        )}
                        {log.typeBadge === 'مستخدم' && (
                          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800">
                            مستخدم
                          </span>
                        )}
                        {log.typeBadge === 'دور' && (
                          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-blue-100 text-blue-800">
                            دور
                          </span>
                        )}
                        {log.typeBadge === 'دعم' && (
                          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800">
                            دعم
                          </span>
                        )}
                        {log.typeBadge === 'بلاغ' && (
                          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-[var(--badge-bg-muted)] text-[var(--foreground)]">
                            بلاغ
                          </span>
                        )}
                        {log.typeBadge === 'نظام' && (
                          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-teal-100 text-teal-800">
                            نظام
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-[var(--text-muted)] font-medium">
                        {log.target}
                      </td>
                      <td className="py-4 px-6 font-bold text-[var(--foreground)]">
                        {log.operator}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </TableScroll>
          {currentPage && <Pagination currentPage={currentPage.page}
            totalPages={currentPage.total_pages} totalItems={currentPage.count}
            itemsPerPage={currentPage.per_page} onPageChange={changePage} />}
        </div>
      </div>
    </div>
  );
}
