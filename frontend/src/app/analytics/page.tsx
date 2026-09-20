'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { BarChartComponent } from '@/components/ui/BarChartComponent';
import { analyticsMetrics, monthlyUserChartData } from '@/data/mockData';
import { Calendar, CheckCircle2, Star, Users } from 'lucide-react';

export default function AnalyticsReportsPage() {
  const [period, setPeriod] = useState<'30' | '7' | '90'>('30');

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="التحليلات والتقارير"
        subtitle="تحليلات الأداء، المعدلات اليومية والتوزيع الجغرافي وحالات المنصة"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Header Period Filter */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-extrabold text-[var(--foreground)]">
            مؤشرات الأداء العامة
          </h3>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPeriod('7')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                period === '7'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              آخر 7 أيام
            </button>
            <button
              onClick={() => setPeriod('30')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                period === '30'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              30 يوم
            </button>
            <button
              onClick={() => setPeriod('90')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                period === '90'
                  ? 'bg-teal-700 text-white'
                  : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:bg-[var(--card-hover)] border border-[var(--card-border)]'
              }`}
            >
              90 يوم
            </button>
          </div>
        </div>

        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)]">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center border border-teal-100">
                <Calendar className="w-5 h-5" />
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200/60 dir-ltr">
                {analyticsMetrics.visitRequestsChange}
              </span>
            </div>
            <div className="text-2xl font-black text-[var(--foreground)] mb-1">
              {analyticsMetrics.visitRequests}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              طلبات الزيارة
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)]">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200/60 dir-ltr">
                {analyticsMetrics.completedVisitsChange}
              </span>
            </div>
            <div className="text-2xl font-black text-[var(--foreground)] mb-1">
              {analyticsMetrics.completedVisits}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              زيارات مكتملة
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)]">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100">
                <Star className="w-5 h-5" />
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200/60 dir-ltr">
                {analyticsMetrics.avgRatingChange}
              </span>
            </div>
            <div className="text-2xl font-black text-[var(--foreground)] mb-1">
              {analyticsMetrics.avgRating}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              متوسط التقييم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)]">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
                <Users className="w-5 h-5" />
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 border border-rose-200/60 dir-ltr">
                {analyticsMetrics.retentionRateChange}
              </span>
            </div>
            <div className="text-2xl font-black text-[var(--foreground)] mb-1">
              {analyticsMetrics.retentionRate}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              معدل الاحتفاظ
            </div>
          </div>
        </div>

        {/* Middle Row: Visit Requests Bar Chart & Most Demanded Areas */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-7">
            <BarChartComponent
              title="طلبات الزيارة اليومية"
              data={monthlyUserChartData}
              color="teal"
              periodLabel=""
            />
          </div>

          <div className="lg:col-span-5 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-5">
            <h3 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
              أكثر المناطق طلباً
            </h3>

            <div className="space-y-4">
              {analyticsMetrics.topRegions.map((region, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-[var(--foreground)]">{region.name}</span>
                    <span className="text-[var(--text-subtle)] font-medium">
                      {region.count} طلب
                    </span>
                  </div>
                  <div className="h-2.5 w-full bg-[var(--badge-bg-muted)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-teal-700 rounded-full"
                      style={{ width: `${(region.count / 400) * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Row: KYC Breakdown & Property Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* KYC Status Breakdown Card */}
          <div className="lg:col-span-6 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
            <h3 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
              حالة التوثيق
            </h3>

            <div className="space-y-3.5 divide-y divide-[var(--divider)] text-xs">
              {analyticsMetrics.kycBreakdown.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between pt-2.5"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${item.color}`}
                    ></span>
                    <span className="font-semibold text-[var(--foreground)]">
                      {item.label}
                    </span>
                  </div>
                  <div className="font-bold text-[var(--foreground)] font-mono">
                    {item.count}{' '}
                    <span className="text-[var(--text-subtle)] font-normal">
                      ({item.pct})
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Property Activity Breakdown Card */}
          <div className="lg:col-span-6 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
            <h3 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
              نشاط العقارات
            </h3>

            <div className="space-y-3.5 divide-y divide-[var(--divider)] text-xs">
              {analyticsMetrics.propertyActivity.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between pt-2.5"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${item.color}`}
                    ></span>
                    <span className="font-semibold text-[var(--foreground)]">
                      {item.label}
                    </span>
                  </div>
                  <div className="font-bold text-[var(--foreground)] font-mono">
                    {item.count}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
