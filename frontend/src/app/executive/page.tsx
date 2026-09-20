'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import { MetricCard } from '@/components/ui/MetricCard';
import { BarChartComponent } from '@/components/ui/BarChartComponent';
import { ActivityFeed } from '@/components/ui/ActivityFeed';
import { UserCheck } from 'lucide-react';
import {
  executiveMetrics,
  monthlyUserChartData,
  reportTrendData,
  userDistributionData,
  executiveRecentActivities,
} from '@/data/mockData';

export default function ExecutiveDashboardPage() {
  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="لوحة التحكم التنفيذية"
        subtitle="نظرة عامة على مؤشرات الأداء والأنشطة الإدارية الحية"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-8">
        {/* Top 5 Metrics Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {executiveMetrics.map((metric, idx) => (
            <MetricCard key={idx} metric={metric} />
          ))}
        </div>

        {/* Dual Trend Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <BarChartComponent
            title="نشاط المنصة – Traffic Trend"
            data={monthlyUserChartData}
            color="teal"
            periodLabel="30 يوم"
          />
          <BarChartComponent
            title="البلاغات – Reports Trend"
            data={reportTrendData}
            color="red"
            periodLabel="30 يوم"
          />
        </div>

        {/* Bottom Section: User Summary & Recent Activities */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* User Summary Widget (Left Column) */}
          <div className="lg:col-span-4 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col justify-between">
            <div>
              <h3 className="font-bold text-slate-800 text-base mb-6">
                ملخص المستخدمين
              </h3>

              <div className="flex items-center gap-3 mb-6 p-3 bg-slate-50 rounded-xl border border-slate-100">
                <div className="w-12 h-12 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center font-bold text-lg">
                  <UserCheck className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="font-bold text-slate-800 text-base">Admin User</h4>
                  <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-semibold mt-0.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span>نشط الآن</span>
                  </div>
                </div>
              </div>

              {/* User Breakdown Stats */}
              <div className="space-y-4 divide-y divide-slate-100">
                <div className="flex items-center justify-between pt-2">
                  <span className="text-xs font-semibold text-slate-500">
                    إجمالي المستخدمين
                  </span>
                  <span className="font-black text-slate-900 text-base">
                    {userDistributionData.total.toLocaleString()}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <span className="text-xs font-semibold text-slate-500">
                    مستأجرون
                  </span>
                  <span className="font-bold text-slate-800 text-sm">
                    {userDistributionData.tenants.toLocaleString()}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <span className="text-xs font-semibold text-slate-500">ملاك</span>
                  <span className="font-bold text-slate-800 text-sm">
                    {userDistributionData.landlords.toLocaleString()}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <span className="text-xs font-semibold text-slate-500">
                    موثّقون
                  </span>
                  <span className="font-bold text-emerald-600 text-sm">
                    {userDistributionData.verified.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Activity Feed (Right Column) */}
          <div className="lg:col-span-8">
            <ActivityFeed activities={executiveRecentActivities} showViewAll={true} />
          </div>
        </div>
      </div>
    </div>
  );
}
