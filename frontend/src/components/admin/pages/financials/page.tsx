'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { BarChartComponent } from '@/components/ui/BarChartComponent';
import { fetchFinancialSummary } from '@/lib/api/financials';
import { FinancialSummary } from '@/lib/api/types';

export default function FinancialDashboardPage() {
  const [data, setData] = useState<FinancialSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadSummary() {
      try {
        const res = await fetchFinancialSummary();
        setData(res);
      } catch (err) {
        console.error('Failed to load financial summary:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadSummary();
  }, []);

  const chartData = data?.sixMonthTrend
    ? data.sixMonthTrend.map((item, idx) => ({
        day: idx + 1,
        value: item.value,
        isCurrent: item.isCurrent,
      }))
    : [];

  const metrics = data?.metrics || {
    avgRent: '–',
    activeTransactions: '–',
    platformFees: '–',
    totalRevenueMonth: '–',
  };

  const revenueBreakdown = data?.revenueBreakdown || {
    platformFees: { value: '–', percent: 0 },
    subscriptions: { value: '–', percent: 0 },
    advertising: { value: '–', percent: 0 },
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="لوحة الإيرادات والمالية"
        subtitle="متابعة الإيرادات الشهرية، رسوم المنصة والمعاملات المالية"
      />

      <div className="admin-page-body min-w-0 w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <p role="note">الإيرادات المثبتة في السجل بالجنيه المصري فقط، دون التزامات الإيجار والتأمين والعمولات غير المستحقة. تسوية مزود الدفع مستقلة.</p>
        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-amber-500 mb-1 dir-ltr font-mono">
              {isLoading ? '...' : metrics.avgRent}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              متوسط الإيجار
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-blue-600 mb-1 font-mono">
              {isLoading ? '...' : metrics.activeTransactions}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              معاملات نشطة
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-teal-600 mb-1 dir-ltr font-mono">
              {isLoading ? '...' : metrics.platformFees}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              رسوم المنصة
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1 dir-ltr font-mono">
              {isLoading ? '...' : metrics.totalRevenueMonth}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
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
          <div className="lg:col-span-5 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-6">
            <h3 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
              توزيع الإيرادات
            </h3>

            <div className="space-y-6">
              {/* Row 1: Platform Fees */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-[var(--foreground)]">Earned commission (posted ledger)</span>
                  <span className="text-[var(--text-muted)] font-mono">
                    {revenueBreakdown.platformFees.value}
                  </span>
                </div>
                <div className="h-3 w-full bg-[var(--badge-bg-muted)] rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-teal-600 rounded-full transition-all duration-500"
                    style={{ width: `${revenueBreakdown.platformFees.percent}%` }}
                  ></div>
                </div>
              </div>

              {/* Row 2: Managed Rentals */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-[var(--foreground)]">Subscription revenue</span>
                  <span className="text-[var(--text-muted)] font-mono">
                    {revenueBreakdown.subscriptions.value}
                  </span>
                </div>
                <div className="h-3 w-full bg-[var(--badge-bg-muted)] rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-blue-600 rounded-full transition-all duration-500"
                    style={{ width: `${revenueBreakdown.subscriptions.percent}%` }}
                  ></div>
                </div>
              </div>

              {/* Row 3: KYC Fees */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-[var(--foreground)]">Advertising revenue</span>
                  <span className="text-[var(--text-muted)] font-mono">
                    {revenueBreakdown.advertising.value}
                  </span>
                </div>
                <div className="h-3 w-full bg-[var(--badge-bg-muted)] rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-amber-500 rounded-full transition-all duration-500"
                    style={{ width: `${revenueBreakdown.advertising.percent}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
