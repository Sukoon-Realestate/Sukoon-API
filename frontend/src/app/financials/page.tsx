'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import { BarChartComponent } from '@/components/ui/BarChartComponent';
import {
  financialMetrics,
  revenueBreakdownData,
  sixMonthRevenueTrend,
} from '@/data/mockData';

export default function FinancialDashboardPage() {
  const chartData = sixMonthRevenueTrend.map((item, idx) => ({
    day: idx + 1,
    value: item.value,
    isCurrent: item.isCurrent,
  }));

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="لوحة الإيرادات والمالية"
        subtitle="متابعة الإيرادات الشهيرة، رسوم المنصة والمعاملات الملاية"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-amber-500 mb-1 dir-ltr font-mono">
              {financialMetrics.avgRent}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              متوسط الإيجار
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-blue-600 mb-1 font-mono">
              {financialMetrics.activeTransactions}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              معاملات نشطة
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-teal-600 mb-1 dir-ltr font-mono">
              {financialMetrics.platformFees}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              رسوم المنصة
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1 dir-ltr font-mono">
              {financialMetrics.totalRevenueMonth}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              إجمالي الإيرادات هذا الشهر
            </div>
          </div>
        </div>

        {/* Charts & Revenue Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* 6 Months Revenue Bar Chart (7 cols) */}
          <div className="lg:col-span-7">
            <BarChartComponent
              title="إيرادات آخر 6 أشهر"
              data={chartData}
              color="teal"
              periodLabel="6 أشهر"
            />
          </div>

          {/* Revenue Breakdown Card (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-6">
            <h3 className="font-extrabold text-slate-800 text-base border-b border-slate-100 pb-3">
              توزيع الإيرادات
            </h3>

            <div className="space-y-6">
              {/* Row 1: Platform Fees */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-slate-700">رسوم المنصة (5%)</span>
                  <span className="text-slate-500 font-mono">
                    {revenueBreakdownData.platformFees.value}
                  </span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden p-0.5">
                  <div className="h-full bg-teal-600 rounded-full w-[45%]"></div>
                </div>
              </div>

              {/* Row 2: Managed Rentals */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-slate-700">إيجارات مُدارة</span>
                  <span className="text-slate-500 font-mono">
                    {revenueBreakdownData.managedRentals.value}
                  </span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden p-0.5">
                  <div className="h-full bg-blue-600 rounded-full w-[85%]"></div>
                </div>
              </div>

              {/* Row 3: KYC Fees */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-slate-700">رسوم توثيق</span>
                  <span className="text-slate-500 font-mono">
                    {revenueBreakdownData.kycFees.value}
                  </span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden p-0.5">
                  <div className="h-full bg-amber-500 rounded-full w-[30%]"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
