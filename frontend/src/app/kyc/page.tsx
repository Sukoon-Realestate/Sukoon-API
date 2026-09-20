'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Eye, AlertTriangle, User } from 'lucide-react';
import { mockKycRequests, kycMetrics } from '@/data/mockData';

export default function KycReviewQueuePage() {
  const [activeTab, setActiveTab] = useState<'all' | 'pending' | 'tenants' | 'landlords'>('all');

  const filteredRequests = mockKycRequests.filter((req) => {
    if (activeTab === 'tenants') return req.type === 'مستأجر';
    if (activeTab === 'landlords') return req.type === 'مالك';
    if (activeTab === 'pending') return req.status === 'انتظار المراجعة';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="طابور مراجعة التوثيق KYC"
        subtitle="فحص المستندات والهويات الوطنية والتحقق من حسابات المستخدمين"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {kycMetrics.rejectedToday}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              مرفوض اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1">
              {kycMetrics.acceptedToday}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              مقبول اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-blue-600 mb-1">
              {kycMetrics.reviewedToday}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              مراجع اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {kycMetrics.pendingReview}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              انتظار المراجعة
            </div>
          </div>
        </div>

        {/* Queue Table Container */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] p-6 space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <h3 className="font-extrabold text-[var(--foreground)] text-base">
              قائمة طلبات التوثيق
            </h3>

            {/* Filter Tabs */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'all'
                    ? 'bg-teal-700 text-white'
                    : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                كل الطلبات
              </button>
              <button
                onClick={() => setActiveTab('pending')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'pending'
                    ? 'bg-teal-700 text-white'
                    : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                مُعلّق
              </button>
              <button
                onClick={() => setActiveTab('tenants')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'tenants'
                    ? 'bg-teal-700 text-white'
                    : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                مستأجرون
              </button>
              <button
                onClick={() => setActiveTab('landlords')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'landlords'
                    ? 'bg-teal-700 text-white'
                    : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                ملاك
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-[var(--table-header-bg)] border-b border-slate-200 text-[var(--text-muted)] text-xs font-bold">
                  <th className="py-4 px-6">المستخدم</th>
                  <th className="py-4 px-6">النوع</th>
                  <th className="py-4 px-6">البطاقة</th>
                  <th className="py-4 px-6">الانتظار</th>
                  <th className="py-4 px-6 text-center">إجراء</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--divider)] text-sm">
                {filteredRequests.map((req) => (
                  <tr
                    key={req.id}
                    className="hover:bg-[var(--table-row-hover)] transition-colors"
                  >
                    <td className="py-4 px-6 font-bold text-[var(--foreground)] flex items-center gap-2">
                      <User className="w-4 h-4 text-[var(--text-subtle)]" />
                      <span>{req.user}</span>
                      {req.hasWarning && (
                        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <StatusBadge type="userType" value={req.type} />
                    </td>
                    <td className="py-4 px-6 font-mono text-xs text-[var(--text-muted)] font-semibold dir-ltr text-right">
                      {req.nationalIdMask}
                    </td>
                    <td className="py-4 px-6 text-xs text-amber-600 font-bold">
                      {req.waitTime}
                    </td>
                    <td className="py-4 px-6 text-center">
                      <Link
                        href="/users/sara-ahmed"
                        className="inline-flex items-center gap-1 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-4 py-1.5 rounded-lg transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>مراجعة</span>
                      </Link>
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
