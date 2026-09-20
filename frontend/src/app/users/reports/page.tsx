'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Search, ShieldAlert, Eye, UserX, AlertTriangle } from 'lucide-react';
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

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Control Bar: Tabs & Search */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
            <button
              onClick={() => setActiveTab('active')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-xs ${
                activeTab === 'active'
                  ? 'bg-rose-600 text-white shadow-rose-200'
                  : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'
              }`}
            >
              بلاغات نشطة (31)
            </button>
            <button
              onClick={() => setActiveTab('suspended')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-xs ${
                activeTab === 'suspended'
                  ? 'bg-amber-600 text-white'
                  : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'
              }`}
            >
              موقوف مؤقتاً
            </button>
            <button
              onClick={() => setActiveTab('banned')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-xs ${
                activeTab === 'banned'
                  ? 'bg-slate-800 text-white'
                  : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'
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
              className="w-full pl-4 pr-10 py-2 bg-white rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30 focus:border-rose-500 transition-all placeholder:text-slate-400"
            />
            <Search className="w-4 h-4 text-slate-400 absolute right-3.5 top-3" />
          </div>
        </div>

        {/* AI System Warning Banner */}
        <div className="bg-amber-50/80 border border-amber-200/80 rounded-2xl p-4 flex items-center gap-3 text-amber-900 text-xs font-semibold shadow-xs">
          <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0" />
          <span>
            النظام الآلي يكشف البريد المزعج والاحتيال واللغة المسيئة. كل البلاغات تحتاج مراجعة بشرية قبل اتخاذ إجراء.
          </span>
        </div>

        {/* Reports Data Table */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs font-bold">
                  <th className="py-4 px-6">المستخدم المُبلّغ عنه</th>
                  <th className="py-4 px-6">النوع</th>
                  <th className="py-4 px-6">سبب البلاغ</th>
                  <th className="py-4 px-6">المُبلِّغ</th>
                  <th className="py-4 px-6">التاريخ</th>
                  <th className="py-4 px-6">الأتمتة</th>
                  <th className="py-4 px-6 text-center">إجراء</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {filteredReports.length > 0 ? (
                  filteredReports.map((report) => (
                    <tr
                      key={report.id}
                      className="hover:bg-slate-50/70 transition-colors"
                    >
                      <td className="py-4 px-6 font-bold text-slate-800">
                        {report.reportedUser}
                      </td>
                      <td className="py-4 px-6">
                        <StatusBadge type="userType" value={report.userType} />
                      </td>
                      <td className="py-4 px-6 text-slate-700 font-medium">
                        {report.reason}
                      </td>
                      <td className="py-4 px-6 text-slate-500 font-medium text-xs">
                        {report.reporter}
                      </td>
                      <td className="py-4 px-6 text-xs text-slate-400 font-medium">
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
                      className="py-12 text-center text-slate-400 font-medium"
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
