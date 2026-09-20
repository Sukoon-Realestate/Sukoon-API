'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import { MetricCard } from '@/components/ui/MetricCard';
import { BarChartComponent } from '@/components/ui/BarChartComponent';
import { ActivityFeed } from '@/components/ui/ActivityFeed';
import {
  overviewMetrics,
  monthlyUserChartData,
  userDistributionData,
  mainRecentActivities,
} from '@/data/mockData';

export default function OverviewDashboardPage() {
  const tenantPercent = Math.round(
    (userDistributionData.tenants / userDistributionData.total) * 100
  );
  const landlordPercent = Math.round(
    (userDistributionData.landlords / userDistributionData.total) * 100
  );

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="لوحة تحكم سكون"
        subtitle="متابعة الأداء العام وحالة المنصة والمستخدمين"
        lastUpdated="اليوم 9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {/* Top 4 Metrics Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {overviewMetrics.map((metric, idx) => (
            <MetricCard key={idx} metric={metric} />
          ))}
        </div>

        {/* Middle Section: New Users Chart & User Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* 30-Day New Users Chart */}
          <div className="lg:col-span-7">
            <BarChartComponent
              title="المستخدمون الجدد (30 يوم)"
              data={monthlyUserChartData}
              color="teal"
              periodLabel="30 يوم"
            />
          </div>

          {/* User Distribution Card */}
          <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col justify-between">
            <div>
              <h3 className="font-bold text-slate-800 text-base mb-6">
                توزيع المستخدمين
              </h3>

              {/* Tenants Row */}
              <div className="mb-6 space-y-2">
                <div className="flex items-center justify-between text-sm font-bold">
                  <span className="text-slate-800">مستأجرون</span>
                  <span className="text-slate-500 font-medium">
                    {userDistributionData.tenants.toLocaleString()}
                  </span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-blue-600 rounded-full transition-all duration-500"
                    style={{ width: `${tenantPercent}%` }}
                  ></div>
                </div>
              </div>

              {/* Landlords Row */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm font-bold">
                  <span className="text-slate-800">ملاك</span>
                  <span className="text-slate-500 font-medium">
                    {userDistributionData.landlords.toLocaleString()}
                  </span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-amber-500 rounded-full transition-all duration-500"
                    style={{ width: `${landlordPercent}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 mt-6">
              <span>إجمالي المستخدمين المسجلين:</span>
              <span className="font-bold text-slate-800">
                {userDistributionData.total.toLocaleString()} مستخدم
              </span>
            </div>
          </div>
        </div>

        {/* Bottom Section: Recent Activities */}
        <div>
          <ActivityFeed activities={mainRecentActivities} showViewAll={true} />
        </div>
      </div>
    </div>
  );
}
