'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { ShieldBan, Image as ImageIcon, FileText, Trash2, Eye } from 'lucide-react';
import { mockModerationItems, moderationMetrics } from '@/data/mockData';

export default function ContentModerationPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'texts' | 'images'>('all');

  const filteredItems = mockModerationItems.filter((item) => {
    if (activeTab === 'texts') return item.type === 'نصوص';
    if (activeTab === 'images') return item.type === 'صور';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="مراجعة المحتوى – Content Moderation"
        subtitle="كشف الصور والمحتوى والمستندات غير الملائمة والمراجعة الفورية"
        lastUpdated="9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {moderationMetrics.suspiciousImages}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              صور مشبوهة
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {moderationMetrics.misleadingDesc}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              أوصاف مضللة
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {moderationMetrics.phoneNumInPhotos}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              أرقام هواتف في صور
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {moderationMetrics.inappropriateContent}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              محتوى غير لائق
            </div>
          </div>
        </div>

        {/* Content Moderation List Container */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <h3 className="font-extrabold text-slate-800 text-base">
              محتوى مشبوه بانتظار المراجعة
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
                الكل
              </button>
              <button
                onClick={() => setActiveTab('texts')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'texts'
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                نصوص
              </button>
              <button
                onClick={() => setActiveTab('images')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'images'
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                صور
              </button>
            </div>
          </div>

          {/* List Items */}
          <div className="divide-y divide-slate-100 space-y-2">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                className="py-4 px-3 flex flex-col sm:flex-row items-center justify-between gap-4 hover:bg-slate-50/70 rounded-xl transition-colors"
              >
                <div className="flex items-center gap-4 w-full sm:w-auto">
                  <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center shrink-0">
                    {item.type === 'صور' ? (
                      <ImageIcon className="w-5 h-5" />
                    ) : (
                      <FileText className="w-5 h-5" />
                    )}
                  </div>

                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">
                      {item.title}
                    </h4>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {item.reason}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                  {item.riskLevel === 'عالي' && (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-600 border border-rose-200">
                      عالي
                    </span>
                  )}
                  {item.riskLevel === 'متوسط' && (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-600 border border-amber-200">
                      متوسط
                    </span>
                  )}
                  {item.riskLevel === 'منخفض' && (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
                      منخفض
                    </span>
                  )}

                  <Link
                    href="/properties/review"
                    className="inline-flex items-center gap-1 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>مراجعة</span>
                  </Link>

                  <button className="inline-flex items-center gap-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors">
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>حذف</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
