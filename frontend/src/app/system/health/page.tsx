'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import {
  TrendingUp,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Download,
  Check,
} from 'lucide-react';
import {
  mockSystemHealthMetrics,
  mockApiPerformanceData,
  mockInternalAdminNotes,
  mockAuditLogs,
} from '@/data/mockData';

export default function SystemHealthPage() {
  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="صحة النظام وسجل التدقيق"
        subtitle="مراقبة أداء الخوادم، سرعة الاستجابة وسجل عمليات المشرفين"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Uptime */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-2xl font-black text-slate-900 tracking-tight block">
                {mockSystemHealthMetrics.uptime}
              </span>
              <p className="text-xs font-bold text-slate-700">
                {mockSystemHealthMetrics.uptimeSub}
              </p>
              <span className="text-[10px] text-slate-400 font-medium block">
                آخر 30 يوم
              </span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>

          {/* Card 2: Response Time */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-2xl font-black text-slate-900 tracking-tight block">
                {mockSystemHealthMetrics.responseTime}
              </span>
              <p className="text-xs font-bold text-slate-700">
                {mockSystemHealthMetrics.responseSub}
              </p>
              <span className="text-[10px] text-slate-400 font-medium block">
                متوسط API
              </span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center border border-teal-100">
              <RefreshCw className="w-5 h-5" />
            </div>
          </div>

          {/* Card 3: Today's Errors */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-2xl font-black text-slate-900 tracking-tight block">
                {mockSystemHealthMetrics.errorsToday}
              </span>
              <p className="text-xs font-bold text-slate-700">
                {mockSystemHealthMetrics.errorsSub}
              </p>
              <span className="text-[10px] text-slate-400 font-medium block">
                أخطاء 5xx
              </span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>

          {/* Card 4: Database Status */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-2xl font-black text-emerald-600 tracking-tight block">
                {mockSystemHealthMetrics.dbStatus}
              </span>
              <p className="text-xs font-bold text-slate-700">
                {mockSystemHealthMetrics.dbSub}
              </p>
              <span className="text-[10px] text-slate-400 font-medium block">
                اتصال مستقر
              </span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Middle Section: Audit Log & API Performance */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Audit Log Table (6 cols) */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-slate-800 text-base">
                سجل التدقيق – Admin Actions
              </h3>
              <button className="text-xs text-teal-600 font-bold hover:underline flex items-center gap-1">
                <span>تصدير السجل</span>
                <Download className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="divide-y divide-slate-100 space-y-3">
              {mockAuditLogs.slice(0, 6).map((log) => (
                <div
                  key={log.id}
                  className="pt-3 first:pt-0 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-slate-400 font-semibold dir-ltr">
                      {log.time}
                    </span>
                    {log.typeBadge === 'KYC' && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        KYC
                      </span>
                    )}
                    {log.typeBadge === 'عقار' && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">
                        عقار
                      </span>
                    )}
                    {log.typeBadge === 'مستخدم' && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                        مستخدم
                      </span>
                    )}
                    {log.typeBadge === 'دور' && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                        دور
                      </span>
                    )}
                    {log.typeBadge === 'دعم' && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        تذكرة
                      </span>
                    )}
                    {log.typeBadge === 'بلاغ' && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                        بلاغ
                      </span>
                    )}

                    <span className="font-bold text-slate-800">
                      {log.action}
                    </span>
                  </div>

                  <span className="text-slate-400 font-medium">{log.operator}</span>
                </div>
              ))}
            </div>
          </div>

          {/* API Performance Bar Chart (6 cols) */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <div>
              <h3 className="font-extrabold text-slate-800 text-base">
                أداء API – الساعة الأخيرة
              </h3>
              <p className="text-xs text-slate-400 font-medium mt-0.5">
                متوسط وقت استجابة API خلال الساعة الماضية
              </p>
            </div>

            {/* Bar Chart Visualization */}
            <div className="h-44 pt-6 flex items-end justify-between gap-1.5 border-b border-slate-100 pb-2">
              {mockApiPerformanceData.map((item, idx) => (
                <div
                  key={idx}
                  className="flex-1 flex flex-col items-center gap-1 group h-full justify-end"
                >
                  <div
                    style={{ height: item.height }}
                    className="w-full bg-[#10B981] hover:bg-[#059669] rounded-t-md transition-all relative"
                  >
                    <div className="opacity-0 group-hover:opacity-100 absolute -top-7 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[10px] font-bold px-1.5 py-0.5 rounded pointer-events-none transition-opacity whitespace-nowrap z-10">
                      {item.ms}ms
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Card: Internal Admin Notes */}
        <div className="bg-[#19232D] text-white rounded-2xl p-6 shadow-md space-y-4">
          <h3 className="font-black text-sm tracking-wide text-slate-100 uppercase">
            Internal Admin Notes
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-semibold text-slate-300">
            {mockInternalAdminNotes.map((note, idx) => (
              <div key={idx} className="flex items-center gap-2.5">
                <div className="w-4 h-4 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center shrink-0">
                  <Check className="w-3 h-3 stroke-[3]" />
                </div>
                <span>{note}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
