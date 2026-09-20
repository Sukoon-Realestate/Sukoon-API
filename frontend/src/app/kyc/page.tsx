'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ShieldCheck, Eye, AlertTriangle, User } from 'lucide-react';
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

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {kycMetrics.rejectedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              مرفوض اليوم
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1">
              {kycMetrics.acceptedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              مقبول اليوم
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-blue-600 mb-1">
              {kycMetrics.reviewedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              مراجع اليوم
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {kycMetrics.pendingReview}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              انتظار المراجعة
            </div>
          </div>
        </div>

        {/* Queue Table Container */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <h3 className="font-extrabold text-slate-800 text-base">
              قائمة طلبات التوثيق
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
                كل الطلبات
              </button>
              <button
                onClick={() => setActiveTab('pending')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'pending'
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                مُعلّق
              </button>
              <button
                onClick={() => setActiveTab('tenants')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'tenants'
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                مستأجرون
              </button>
              <button
                onClick={() => setActiveTab('landlords')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'landlords'
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
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
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs font-bold">
                  <th className="py-4 px-6">المستخدم</th>
                  <th className="py-4 px-6">النوع</th>
                  <th className="py-4 px-6">البطاقة</th>
                  <th className="py-4 px-6">الانتظار</th>
                  <th className="py-4 px-6 text-center">إجراء</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {filteredRequests.map((req) => (
                  <tr
                    key={req.id}
                    className="hover:bg-slate-50/70 transition-colors"
                  >
                    <td className="py-4 px-6 font-bold text-slate-800 flex items-center gap-2">
                      <User className="w-4 h-4 text-slate-400" />
                      <span>{req.user}</span>
                      {req.hasWarning && (
                        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <StatusBadge type="userType" value={req.type} />
                    </td>
                    <td className="py-4 px-6 font-mono text-xs text-slate-500 font-semibold dir-ltr text-right">
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
