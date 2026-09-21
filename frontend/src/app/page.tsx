'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { MetricCard } from '@/components/ui/MetricCard';
import { BarChartComponent } from '@/components/ui/BarChartComponent';
import { ActivityFeed } from '@/components/ui/ActivityFeed';
import { QuickActionsToolbar } from '@/components/ui/QuickActionsToolbar';
import { fetchDashboardStats } from '@/lib/api/dashboard';
import {
  DashboardMetric,
  UserDistribution,
  ActivityItem,
} from '@/lib/api/types';

export default function OverviewDashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetric[]>([]);
  const [chartData, setChartData] = useState<Array<{ label: string; value: number }>>([]);
  const [distribution, setDistribution] = useState<UserDistribution>({
    total: 0,
    tenants: 0,
    landlords: 0,
    verified: 0,
    pending: 0,
    suspended: 0,
  });
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await fetchDashboardStats();
        if (data.metrics) {
          setMetrics(data.metrics);
        }
        if (data.chart_data) {
          setChartData(data.chart_data);
        }
        if (data.user_distribution) {
          setDistribution(data.user_distribution);
        }
        if (data.recent_activities) {
          setActivities(data.recent_activities);
        }
      } catch (err) {
        console.error('Failed to load dashboard stats from backend:', err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  const total = distribution.total || 1;
  const tenantPercent = Math.round((distribution.tenants / total) * 100);
  const landlordPercent = Math.round((distribution.landlords / total) * 100);

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="لوحة تحكم سكون"
        subtitle="متابعة الأداء العام وحالة المنصة والمستخدمين"
        lastUpdated="محدث الآن"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-8">
        {/* Admin Quick Toolbar */}
        <QuickActionsToolbar />

        {/* Top 4 Metrics Row */}
        {loading && metrics.length === 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-32 bg-slate-900/60 rounded-2xl animate-pulse border border-slate-800"
              />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {metrics.map((metric, idx) => (
              <MetricCard key={idx} metric={metric} delay={idx * 80} />
            ))}
          </div>
        )}

        {/* Middle Section: New Users Chart & User Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* 30-Day New Users Chart */}
          <div className="lg:col-span-7">
            <BarChartComponent
              title="المستخدمون الجدد (30 يوم)"
              data={chartData}
              color="teal"
              periodLabel="30 يوم"
            />
          </div>

          {/* User Distribution Card */}
          <div
            className="lg:col-span-5 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] flex flex-col justify-between animate-fadeInUp"
            style={{ animationDelay: '100ms' }}
          >
            <div>
              <h3 className="font-extrabold text-[var(--foreground)] text-base mb-6">
                توزيع المستخدمين
              </h3>

              {/* Tenants Row */}
              <div className="mb-6 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-[var(--text-muted)] font-bold">مستأجرون</span>
                  <span className="text-[var(--foreground)] font-black text-sm">
                    {distribution.tenants.toLocaleString('en-US')}
                  </span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/50 rounded-full h-3 overflow-hidden p-0.5">
                  <div
                    className="bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-500 h-2 rounded-full transition-all duration-1000 shadow-sm shadow-blue-500/20"
                    style={{ width: `${tenantPercent}%` }}
                  ></div>
                </div>
              </div>

              {/* Landlords Row */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-[var(--text-muted)] font-bold">ملاك</span>
                  <span className="text-[var(--foreground)] font-black text-sm">
                    {distribution.landlords.toLocaleString('en-US')}
                  </span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/50 rounded-full h-3 overflow-hidden p-0.5">
                  <div
                    className="bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 h-2 rounded-full transition-all duration-1000 shadow-sm shadow-amber-500/20"
                    style={{ width: `${landlordPercent}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Bottom Status Tags */}
            <div className="pt-6 mt-6 border-t border-[var(--divider)] grid grid-cols-3 gap-2 text-center text-xs">
              <div className="bg-emerald-50/90 dark:bg-slate-900/50 p-3 rounded-2xl border border-emerald-200/90 dark:border-slate-800 transition-transform hover:scale-105">
                <div className="text-[11px] text-emerald-800 dark:text-emerald-300 font-extrabold mb-0.5">موثقون</div>
                <div className="text-base font-black text-emerald-700 dark:text-emerald-400">
                  {distribution.verified.toLocaleString('en-US')}
                </div>
              </div>
              <div className="bg-amber-50/90 dark:bg-slate-900/50 p-3 rounded-2xl border border-amber-200/90 dark:border-slate-800 transition-transform hover:scale-105">
                <div className="text-[11px] text-amber-800 dark:text-amber-300 font-extrabold mb-0.5">قيد التوثيق</div>
                <div className="text-base font-black text-amber-700 dark:text-amber-400">
                  {distribution.pending.toLocaleString('en-US')}
                </div>
              </div>
              <div className="bg-rose-50/90 dark:bg-slate-900/50 p-3 rounded-2xl border border-rose-200/90 dark:border-slate-800 transition-transform hover:scale-105">
                <div className="text-[11px] text-rose-800 dark:text-rose-300 font-extrabold mb-0.5">موقوفون</div>
                <div className="text-base font-black text-rose-700 dark:text-rose-400">
                  {distribution.suspended.toLocaleString('en-US')}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section: Recent Activities Feed */}
        <ActivityFeed activities={activities} />
      </div>
    </div>
  );
}
