'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import {
  reportsOverviewMetrics,
  mockOverviewTickets,
  disputeReasonsData,
  bookingLogData,
} from '@/data/mockData';

export default function ReportsOverviewPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'disputes' | 'props' | 'users'>('all');

  const filteredTickets = mockOverviewTickets.filter((t) => {
    if (activeTab === 'disputes') return t.type === 'خلاف';
    if (activeTab === 'props') return t.type === 'بلاغ عقار';
    if (activeTab === 'users') return t.type === 'بلاغ مستخدم';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="التقارير والتذاكر"
        subtitle="نظرة عامة على بلاغات المستخدمين، تتبع الخلافات وتوزيع الحجوزات"
        lastUpdated="9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-blue-600 mb-1">
              {reportsOverviewMetrics.avgResolutionTime}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              متوسط وقت الحل
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {reportsOverviewMetrics.activeDisputes}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              خلافات نشطة
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1">
              {reportsOverviewMetrics.solvedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              حُلت اليوم
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {reportsOverviewMetrics.openTickets}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              تذاكر مفتوحة
            </div>
          </div>
        </div>

        {/* Main Section Split */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Main Table Column (8 cols) */}
          <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <h3 className="font-extrabold text-slate-800 text-base">
                سجل التذاكر • Ticket ID
              </h3>

              {/* Filter Tabs */}
              <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
                <button
                  onClick={() => setActiveTab('all')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors whitespace-nowrap ${
                    activeTab === 'all'
                      ? 'bg-teal-700 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  كل التذاكر
                </button>
                <button
                  onClick={() => setActiveTab('disputes')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors whitespace-nowrap ${
                    activeTab === 'disputes'
                      ? 'bg-teal-700 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  خلافات
                </button>
                <button
                  onClick={() => setActiveTab('props')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors whitespace-nowrap ${
                    activeTab === 'props'
                      ? 'bg-teal-700 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  بلاغات عقارات
                </button>
                <button
                  onClick={() => setActiveTab('users')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors whitespace-nowrap ${
                    activeTab === 'users'
                      ? 'bg-teal-700 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  بلاغات مستخدمين
                </button>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-right border-collapse">
                <thead>
                  <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs font-bold">
                    <th className="py-4 px-4">Ticket ID</th>
                    <th className="py-4 px-4">الموضوع</th>
                    <th className="py-4 px-4">المُبلِّغ</th>
                    <th className="py-4 px-4">النوع</th>
                    <th className="py-4 px-4">الحالة</th>
                    <th className="py-4 px-4">المراجع</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {filteredTickets.map((ticket) => (
                    <tr
                      key={ticket.id}
                      className="hover:bg-slate-50/70 transition-colors"
                    >
                      <td className="py-4 px-4 font-mono font-bold text-teal-700 dir-ltr text-right">
                        <Link href="/support/SUP-201" className="hover:underline">
                          {ticket.id}
                        </Link>
                      </td>
                      <td className="py-4 px-4 font-bold text-slate-800">
                        {ticket.subject}
                      </td>
                      <td className="py-4 px-4 text-slate-600">{ticket.reporter}</td>
                      <td className="py-4 px-4">
                        <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
                          {ticket.type}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        {ticket.status === 'مفتوح' && (
                          <span className="text-rose-600 font-bold">مفتوح</span>
                        )}
                        {ticket.status === 'قيد المراجعة' && (
                          <span className="text-amber-600 font-bold">
                            قيد المراجعة
                          </span>
                        )}
                        {ticket.status === 'محلول' && (
                          <span className="text-emerald-600 font-bold">
                            محلول
                          </span>
                        )}
                        {ticket.status === 'مغلق' && (
                          <span className="text-slate-400 font-bold">مغلق</span>
                        )}
                      </td>
                      <td className="py-4 px-4 text-slate-500 font-medium">
                        {ticket.reviewer}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Sidebar Column (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            {/* Dispute Reasons Card */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
              <h3 className="font-extrabold text-slate-800 text-sm border-b border-slate-100 pb-3">
                توزيع أسباب الخلافات – Dispute Reason
              </h3>

              <div className="space-y-3.5 text-xs">
                {disputeReasonsData.map((item, idx) => (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between font-bold">
                      <span className="text-slate-700">{item.title}</span>
                      <span className="text-slate-500 font-medium">
                        {item.count} حالة
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${item.color} rounded-full`}
                        style={{ width: `${(item.count / 15) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Booking Log Card */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
              <h3 className="font-extrabold text-slate-800 text-sm border-b border-slate-100 pb-3">
                سجل الحجوزات – Booking Log
              </h3>

              <div className="space-y-3 text-xs">
                {bookingLogData.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-center justify-between py-1.5 border-b border-slate-50"
                  >
                    <div>
                      <div className="font-mono font-bold text-slate-800 dir-ltr text-right text-[11px]">
                        {log.id}
                      </div>
                      <div className="text-slate-500 font-medium">{log.title}</div>
                    </div>

                    <div>
                      {log.status === 'مكتمل' ? (
                        <span className="text-emerald-600 font-bold">مكتمل</span>
                      ) : (
                        <span className="text-rose-600 font-bold">ملغي</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
