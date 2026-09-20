'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import {
  Building2,
  AlertTriangle,
  Check,
  X,
  RotateCcw,
} from 'lucide-react';
import {
  mockProperties,
  propertyMetrics,
  propertyVerificationChecklist,
  propertyRiskFlags,
} from '@/data/mockData';

export default function PropertyReviewQueuePage() {
  const [selectedPropertyId, setSelectedPropertyId] = useState('prop-1');
  const [filterTag, setFilterTag] = useState<'all' | 'images' | 'highRisk'>('all');

  const selectedProperty =
    mockProperties.find((p) => p.id === selectedPropertyId) || mockProperties[0];

  const filteredList = mockProperties.filter((p) => {
    if (filterTag === 'highRisk') return p.riskLevel === 'عالي الخطر';
    if (filterTag === 'images') return (p.imagesCount || 0) < 5;
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="طابور مراجعة العقارات"
        subtitle="فحص طلبات إدراج العقارات، قائمة التحقق الآلية وتقييم المخاطر"
        lastUpdated="9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-blue-600 mb-1">
              {propertyMetrics.openReports}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              بلاغات نشطة
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {propertyMetrics.rejectedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              مرفوض اليوم
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1">
              {propertyMetrics.acceptedToday}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              مقبول اليوم
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {propertyMetrics.pending}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              بانتظار المراجعة
            </div>
          </div>
        </div>

        {/* Main 2 Column Split Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Pending Property List (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <h3 className="font-extrabold text-slate-800 text-base">
                قائمة العقارات المعلقة
              </h3>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setFilterTag('all')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors ${
                    filterTag === 'all'
                      ? 'bg-teal-700 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  كل العقارات
                </button>
                <button
                  onClick={() => setFilterTag('images')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors ${
                    filterTag === 'images'
                      ? 'bg-teal-700 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  تحتاج صور
                </button>
                <button
                  onClick={() => setFilterTag('highRisk')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors ${
                    filterTag === 'highRisk'
                      ? 'bg-teal-700 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  عالي الخطر
                </button>
              </div>
            </div>

            {/* List items */}
            <div className="space-y-3">
              {filteredList.map((item) => {
                const isSelected = item.id === selectedPropertyId;
                return (
                  <div
                    key={item.id}
                    onClick={() => setSelectedPropertyId(item.id)}
                    className={`p-4 rounded-xl border flex items-center justify-between transition-all cursor-pointer ${
                      isSelected
                        ? 'border-teal-500 bg-teal-50/40 shadow-xs'
                        : 'border-slate-200/80 bg-white hover:bg-slate-50/60'
                    }`}
                  >
                    <div className="flex items-center gap-3.5">
                      <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center shrink-0">
                        <Building2 className="w-5 h-5" />
                      </div>

                      <div>
                        <h4 className="font-bold text-slate-900 text-sm">
                          {item.title}
                        </h4>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {item.owner} • {item.imagesCount} صور • {item.time}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {item.riskLevel === 'عالي الخطر' && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-600 border border-rose-200">
                          عالي الخطر
                        </span>
                      )}
                      {item.riskLevel === 'متوسط الخطر' && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-600 border border-amber-200">
                          متوسط الخطر
                        </span>
                      )}
                      {item.riskLevel === 'منخفض الخطر' && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
                          منخفض الخطر
                        </span>
                      )}

                      <button className="bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors">
                        مراجعة
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Verification Checklist Panel (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
            <div className="border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-slate-800 text-base leading-tight">
                قائمة التحقق – {selectedProperty.title}
              </h3>
            </div>

            {/* Checklist items */}
            <div className="space-y-2 text-xs">
              {propertyVerificationChecklist.map((check) => (
                <div
                  key={check.id}
                  className="flex items-center justify-between py-2 border-b border-slate-50"
                >
                  <span
                    className={`font-semibold ${
                      check.passed ? 'text-slate-700' : 'text-rose-500'
                    }`}
                  >
                    {check.title}
                  </span>
                  {check.passed ? (
                    <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold text-[10px]">
                      ✓
                    </span>
                  ) : (
                    <span className="w-5 h-5 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center font-bold text-[10px]">
                      ✗
                    </span>
                  )}
                </div>
              ))}
            </div>

            {/* Risk Flags Box */}
            <div className="space-y-2 bg-rose-50/50 border border-rose-100 rounded-xl p-3.5 text-xs text-rose-800">
              <div className="font-bold text-slate-700 mb-1">Risk Flags:</div>
              {propertyRiskFlags.map((flag, idx) => (
                <div key={idx} className="flex items-center gap-2 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                  <span>{flag}</span>
                </div>
              ))}
            </div>

            {/* Decision Action Buttons */}
            <div className="space-y-2.5 pt-2">
              <button className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-extrabold text-sm rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2">
                <Check className="w-4 h-4" />
                <span>قبول العقار ✓</span>
              </button>

              <button className="w-full py-3 bg-rose-500 hover:bg-rose-600 text-white font-extrabold text-sm rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2">
                <X className="w-4 h-4" />
                <span>رفض ✗</span>
              </button>

              <button className="w-full py-3 bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 font-extrabold text-sm rounded-xl border border-amber-200/60 transition-colors flex items-center justify-center gap-2">
                <RotateCcw className="w-4 h-4 text-amber-600" />
                <span>طلب تعديل</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
