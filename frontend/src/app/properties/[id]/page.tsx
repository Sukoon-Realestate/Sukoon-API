'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import {
  Building2,
  ShieldCheck,
  EyeOff,
  Trash2,
  Download,
} from 'lucide-react';
import { mockProperties } from '@/data/mockData';

export default function PropertyDetailPage() {
  const params = useParams();
  const propId = params?.id as string;

  const property =
    mockProperties.find((p) => p.id === propId) || mockProperties[0];

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="تفاصيل العقار – Admin View"
        subtitle="سجل المراجعة، الإحصائيات الكاملة وإجراءات الإشراف"
        lastUpdated="9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Property Preview Card (4 cols) */}
          <div className="lg:col-span-4 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] flex flex-col items-center">
            {/* Property Image Placeholder */}
            <div className="w-full h-44 rounded-2xl bg-[var(--badge-bg-muted)] border border-[var(--card-border)] flex items-center justify-center text-[var(--text-subtle)] mb-5">
              <Building2 className="w-16 h-16 text-slate-300" />
            </div>

            <h3 className="text-lg font-extrabold text-[var(--foreground)] mb-2 text-center">
              {property.title}
            </h3>

            <div className="mb-6">
              <span className="inline-flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                <ShieldCheck className="w-3.5 h-3.5" />
                موثّق
              </span>
            </div>

            {/* Property Specs List */}
            <div className="w-full space-y-4 border-t border-[var(--divider)] pt-5 text-right text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-subtle)] font-medium">المالك</span>
                <span className="font-bold text-[var(--foreground)]">{property.owner}</span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">السعر</span>
                <span className="font-extrabold text-teal-700 dir-ltr text-sm font-mono">
                  {property.price}/شهر
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">المساحة</span>
                <span className="font-bold text-[var(--foreground)] dir-ltr">
                  {property.area || '90 م²'}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">الغرف</span>
                <span className="font-bold text-[var(--foreground)]">
                  {property.rooms || 3} غرف
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">تاريخ الإضافة</span>
                <span className="font-bold text-[var(--foreground)]">
                  {property.createdDate || '1 مايو 2025'}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">آخر تحديث</span>
                <span className="font-bold text-[var(--foreground)]">
                  {property.lastUpdated || 'اليوم'}
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Stats, Review Log & Actions (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Top 3 Stat Cards */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
                <div className="text-2xl font-black text-blue-600 mb-1">
                  1,247
                </div>
                <div className="text-xs font-semibold text-[var(--text-subtle)]">
                  مشاهدات
                </div>
              </div>

              <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
                <div className="text-2xl font-black text-emerald-600 mb-1">
                  23
                </div>
                <div className="text-xs font-semibold text-[var(--text-subtle)]">
                  طلبات زيارة
                </div>
              </div>

              <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
                <div className="text-2xl font-black text-[var(--foreground)] mb-1">
                  0
                </div>
                <div className="text-xs font-semibold text-[var(--text-subtle)]">
                  بلاغات
                </div>
              </div>
            </div>

            {/* Audit Log Card */}
            <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)]">
              <h4 className="font-bold text-[var(--foreground)] text-base mb-6">
                سجل المراجعة
              </h4>

              <div className="space-y-4 divide-y divide-[var(--divider)]">
                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      تم قبول العقار
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    1 مايو 9:30 ص • أحمد العدل
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      مراجعة أولية آلية – لم تُكتشف مشاكل
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    1 مايو 9:20 ص • النظام
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      إرسال العقار من المالك
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    1 مايو 9:00 ص • أحمد محمد
                  </span>
                </div>
              </div>
            </div>

            {/* Bottom Action Controls */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <button className="py-4 bg-amber-50 hover:bg-amber-100 text-amber-800 font-extrabold text-sm rounded-2xl border border-amber-200 transition-all flex items-center justify-center gap-2">
                <EyeOff className="w-4 h-4 text-amber-700" />
                <span>إخفاء العقار</span>
              </button>

              <button className="py-4 bg-rose-500 hover:bg-rose-600 text-white font-extrabold text-sm rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2">
                <Trash2 className="w-4 h-4" />
                <span>حذف</span>
              </button>

              <button className="py-4 bg-[var(--badge-bg-muted)] hover:bg-[var(--card-hover)] text-[var(--foreground)] font-extrabold text-sm rounded-2xl border border-[var(--card-border)] transition-all flex items-center justify-center gap-2">
                <Download className="w-4 h-4 text-[var(--text-muted)]" />
                <span>تصدير</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
