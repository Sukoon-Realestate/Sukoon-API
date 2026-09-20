'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Search, ShieldAlert, Eye, UserX } from 'lucide-react';
import { mockReports } from '@/data/mockData';

export default function ReportsQueuePage() {
  const [activeTab, setActiveTab] = useState<'active' | 'suspended' | 'banned'>('active');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredReports = mockReports.filter((report) => {
    const matchesSearch =
      report.reportedUser.includes(searchQuery) ||
      report.reason.includes(searchQuery) ||
      report.reporter.includes(searchQuery);

    if (!matchesSearch) return false;

    if (activeTab === 'suspended') return report.status === 'موقوف مؤقتاً';
    if (activeTab === 'banned') return report.status === 'محظور نهائياً';
    return report.status === 'نشط';
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="إدارة المستخدمين – طابور البلاغات"
        subtitle="مراجعة البلاغات الصادرة من المستخدمين والنظام والتحقق الإداري"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Control Bar: Tabs & Search */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 animate-fadeInUp">
          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
            <button
              onClick={() => setActiveTab('active')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-[var(--shadow-card)] ${
                activeTab === 'active'
                  ? 'bg-rose-600 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              بلاغات نشطة (31)
            </button>
            <button
              onClick={() => setActiveTab('suspended')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-[var(--shadow-card)] ${
                activeTab === 'suspended'
                  ? 'bg-amber-600 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              موقوف مؤقتاً
            </button>
            <button
              onClick={() => setActiveTab('banned')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-[var(--shadow-card)] ${
                activeTab === 'banned'
                  ? 'bg-slate-800 dark:bg-slate-600 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--foreground)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              محظور نهائياً
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
        <div className="bg-amber-50/80 dark:bg-amber-500/10 border border-amber-200/80 dark:border-amber-500/20 rounded-2xl p-4 flex items-center gap-3 text-amber-900 dark:text-amber-300 text-xs font-semibold shadow-[var(--shadow-card)] animate-fadeInUp" style={{ animationDelay: '50ms' }}>
          <ShieldAlert className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0" />
          <span>
            النظام الآلي يكشف البريد المزعج والاحتيال واللغة المسيئة. كل البلاغات تحتاج مراجعة بشرية قبل اتخاذ إجراء.
          </span>
        </div>

        {/* Reports Data Table */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden animate-fadeInUp" style={{ animationDelay: '100ms' }}>
          <div className="overflow-x-auto">
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
                          value={report.automationLevel}
                        />
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center justify-center gap-2">
                          <Link
                            href="/users/sara-ahmed"
                            className="inline-flex items-center gap-1 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>مراجعة</span>
                          </Link>
                          <button className="inline-flex items-center gap-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors">
                            <UserX className="w-3.5 h-3.5" />
                            <span>إيقاف</span>
                          </button>
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
                      لا توجد بلاغات تطابق البحث الحالي.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
