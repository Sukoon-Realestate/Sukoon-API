'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Search, Download } from 'lucide-react';
import { mockAuditLogs } from '@/data/mockData';

export default function SystemAuditLogsPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'system' | 'users' | 'props' | 'kyc'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredLogs = mockAuditLogs.filter((log) => {
    const matchesSearch =
      log.action.includes(searchQuery) ||
      log.operator.includes(searchQuery) ||
      log.target.includes(searchQuery);

    if (!matchesSearch) return false;

    if (activeTab === 'system') return log.typeBadge === 'نظام';
    if (activeTab === 'users') return log.typeBadge === 'مستخدم';
    if (activeTab === 'props') return log.typeBadge === 'عقار';
    if (activeTab === 'kyc') return log.typeBadge === 'KYC';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="سجل النشاط – Activity Logs"
        subtitle="سجل العمليات والإجراءات الإدارية، التحركات الحية وتتبع المشرفين"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Control Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-72">
            <input
              type="text"
              placeholder="بحث في السجل..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-4 pr-10 py-2 bg-[var(--card-bg)] rounded-full border border-[var(--card-border)] text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-[#0D7C66] transition-all placeholder:text-[var(--text-subtle)]"
            />
            <Search className="w-4 h-4 text-[var(--text-subtle)] absolute right-3.5 top-2.5" />
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto justify-start md:justify-end">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'all'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              كل الإجراءات
            </button>
            <button
              onClick={() => setActiveTab('kyc')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'kyc'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              KYC
            </button>
            <button
              onClick={() => setActiveTab('props')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'props'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              عقارات
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'users'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              مستخدمون
            </button>
            <button
              onClick={() => setActiveTab('system')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === 'system'
                  ? 'bg-[#0D7C66] text-white shadow-[var(--shadow-card)]'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              نظام
            </button>
            <button className="flex items-center gap-1.5 bg-[var(--card-bg)] px-4 py-1.5 rounded-full border border-[var(--card-border)] text-xs font-bold text-[var(--foreground)] hover:bg-[var(--card-hover)] transition-colors shadow-[var(--shadow-card)]">
              <Download className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              <span>تصدير CSV</span>
            </button>
          </div>
        </div>

        {/* Audit Log Table Container */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-[var(--table-header-bg)] border-b border-slate-200 text-[var(--text-muted)] text-xs font-bold">
                  <th className="py-4 px-6">الوقت</th>
                  <th className="py-4 px-6">الإجراء</th>
                  <th className="py-4 px-6">النوع</th>
                  <th className="py-4 px-6">المستهدف</th>
                  <th className="py-4 px-6">المشرف</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--divider)] text-xs">
                {filteredLogs.map((log) => (
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
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
