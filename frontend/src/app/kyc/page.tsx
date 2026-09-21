'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Eye, AlertTriangle, User } from 'lucide-react';
import { fetchKycQueue, fetchKycMetrics } from '@/lib/api/kyc';
import { KycRequest, KycMetrics } from '@/lib/api/types';

export default function KycReviewQueuePage() {
  const [activeTab, setActiveTab] = useState<'all' | 'pending' | 'tenants' | 'landlords'>('all');
  const [requests, setRequests] = useState<KycRequest[]>([]);
  const [metrics, setMetrics] = useState<KycMetrics>({
    pendingReview: 0,
    acceptedToday: 0,
    rejectedToday: 0,
    reviewedToday: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [queueRes, metricsRes] = await Promise.allSettled([
          fetchKycQueue(),
          fetchKycMetrics(),
        ]);
        if (queueRes.status === 'fulfilled' && queueRes.value?.results) {
          setRequests(queueRes.value.results);
        } else {
          setRequests([]);
        }
        if (metricsRes.status === 'fulfilled' && metricsRes.value) {
          setMetrics(metricsRes.value);
        }
      } catch (err) {
        console.error('KYC queue fetch failed:', err);
        setRequests([]);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredRequests = requests.filter((req) => {
    if (activeTab === 'tenants') return req.type === 'مستأجر';
    if (activeTab === 'landlords') return req.type === 'مالك';
    if (activeTab === 'pending') return req.status === 'pending' || req.statusDisplay === 'انتظار المراجعة';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="طابور مراجعة التوثيق KYC"
        subtitle="فحص المستندات والهويات الوطنية والتحقق من حسابات المستخدمين"
        lastUpdated="محدث الآن"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {metrics.rejectedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              مرفوض اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-emerald-400 mb-1">
              {metrics.acceptedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              مقبول اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-blue-400 mb-1">
              {metrics.reviewedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              مراجع اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-amber-400 mb-1">
              {metrics.pendingReview}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              انتظار المراجعة
            </div>
          </div>
        </div>

        {/* Queue Table Container */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] p-6 space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <h3 className="font-extrabold text-white text-base">
              قائمة طلبات التوثيق
            </h3>

            {/* Filter Tabs */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                  activeTab === 'all'
                    ? 'bg-teal-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                كل الطلبات ({requests.length})
              </button>
              <button
                onClick={() => setActiveTab('pending')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                  activeTab === 'pending'
                    ? 'bg-teal-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                مُعلّق ({requests.filter((r) => r.status === 'pending').length})
              </button>
              <button
                onClick={() => setActiveTab('tenants')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                  activeTab === 'tenants'
                    ? 'bg-teal-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                مستأجرون
              </button>
              <button
                onClick={() => setActiveTab('landlords')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                  activeTab === 'landlords'
                    ? 'bg-teal-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                ملاك
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            {isLoading ? (
              <div className="py-8 text-center text-xs text-slate-400">
                جاري تحميل طلبات التوثيق من الخادم...
              </div>
            ) : filteredRequests.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                لا توجد طلبات توثيق مطابقة.
              </div>
            ) : (
              <table className="w-full text-right border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-900/60 border-b border-[var(--card-border)] text-slate-400 font-bold">
                    <th className="py-3.5 px-4">المستخدم</th>
                    <th className="py-3.5 px-4">النوع</th>
                    <th className="py-3.5 px-4">البطاقة</th>
                    <th className="py-3.5 px-4">الحالة</th>
                    <th className="py-3.5 px-4 text-center">إجراء</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--divider)] font-medium">
                  {filteredRequests.map((req) => (
                    <tr
                      key={req.id}
                      className="hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="py-3.5 px-4 font-bold text-white flex items-center gap-2">
                        <User className="w-4 h-4 text-slate-400" />
                        <span>{req.user}</span>
                        {req.hasWarning && (
                          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge status={req.type} />
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs text-slate-400 font-semibold dir-ltr text-right">
                        {req.nationalIdMask || '–'}
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge status={req.statusDisplay || req.status} />
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <Link
                          href={`/kyc/review?id=${req.id}`}
                          className="inline-flex items-center gap-1 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>مراجعة</span>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
