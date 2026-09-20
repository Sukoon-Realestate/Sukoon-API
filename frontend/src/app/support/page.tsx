'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Headphones, ExternalLink } from 'lucide-react';
import { mockSupportTickets, supportMetrics } from '@/data/mockData';

export default function SupportTicketsPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'high' | 'landlord' | 'tenant'>('all');

  const filteredTickets = mockSupportTickets.filter((t) => {
    if (activeTab === 'high') return t.priority === 'عالي';
    if (activeTab === 'landlord') return t.userType === 'مالك';
    if (activeTab === 'tenant') return t.userType === 'مستأجر';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="دعم العملاء – تذاكر الدعم"
        subtitle="متابعة استفسارات ومشاكل المستأجرين والملاك والرد الفوري"
        lastUpdated="9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-blue-600 mb-1">
              {supportMetrics.avgResolutionTime}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              متوسط الحل
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1">
              {supportMetrics.solvedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              محلولة اليوم
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {supportMetrics.inProgress}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              قيد المعالجة
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {supportMetrics.openTickets}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              مفتوحة
            </div>
          </div>
        </div>

        {/* Tickets Queue Container */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <h3 className="font-extrabold text-slate-800 text-base">
              تذاكر الدعم
            </h3>

            {/* Filter Tabs */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'all'
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                كل التذاكر
              </button>
              <button
                onClick={() => setActiveTab('high')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'high'
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                أولوية عالية
              </button>
              <button
                onClick={() => setActiveTab('landlord')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'landlord'
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                مالك
              </button>
              <button
                onClick={() => setActiveTab('tenant')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'tenant'
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                مستأجر
              </button>
            </div>
          </div>

          {/* Ticket Rows */}
          <div className="divide-y divide-slate-100 space-y-2">
            {filteredTickets.map((t) => (
              <div
                key={t.id}
                className="py-4 px-3 flex flex-col sm:flex-row items-center justify-between gap-4 hover:bg-slate-50/70 rounded-xl transition-colors"
              >
                <div className="flex items-center gap-4 w-full sm:w-auto">
                  <div className="font-mono font-bold text-teal-700 text-xs dir-ltr shrink-0">
                    {t.id}
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">
                      {t.subject}
                    </h4>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {t.user} • {t.timeAgo}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                  <StatusBadge type="userType" value={t.userType} />

                  {t.priority === 'عالي' && (
                    <span className="text-xs font-bold text-rose-600">عالي</span>
                  )}
                  {t.priority === 'متوسط' && (
                    <span className="text-xs font-bold text-amber-600">متوسط</span>
                  )}
                  {t.priority === 'منخفض' && (
                    <span className="text-xs font-bold text-emerald-600">منخفض</span>
                  )}

                  <Link
                    href={`/support/${t.id}`}
                    className="inline-flex items-center gap-1 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-4 py-1.5 rounded-lg transition-colors"
                  >
                    <span>فتح</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
