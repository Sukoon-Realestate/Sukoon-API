'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { useToast } from '@/components/ui/Toast';
import {
  Building2,
  ShieldCheck,
  EyeOff,
  Trash2,
  Download,
  ArrowRight,
} from 'lucide-react';
import { fetchAdminPropertyDetail, rejectProperty } from '@/lib/api/properties';
import { PropertyDetail } from '@/lib/api/types';

export default function PropertyDetailPage() {
  const params = useParams();
  const propId = params?.id as string;
  const { showToast } = useToast();

  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadProperty() {
      if (!propId) return;
      setIsLoading(true);
      try {
        const data = await fetchAdminPropertyDetail(propId);
        if (data) {
          setProperty(data);
        }
      } catch (err) {
        console.error('Failed to load property detail:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadProperty();
  }, [propId]);

  const handleHideProperty = async () => {
    if (!property) return;
    try {
      await rejectProperty(property.id, 'إخفاء العقار من قبل الإدارة');
      setProperty((prev) => (prev ? { ...prev, status: 'مرفوض', is_verified: false } : null));
      showToast('تم إخفاء العقار من نتائج البحث للمستخدمين', 'info');
    } catch {
      showToast('حدث خطأ أثناء تعديل حالة العقار', 'error');
    }
  };

  const handleExportData = () => {
    if (!property) return;
    showToast(`جاري تصدير بيانات العقار "${property.title}"...`, 'success');
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col pb-12">
        <Header
          title="تفاصيل العقار – Admin View"
          subtitle="سجل المراجعة، الإحصائيات الكاملة وإجراءات الإشراف"
        />
        <div className="p-12 text-center text-slate-400 text-xs font-bold space-y-3">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p>جاري تحميل تفاصيل العقار من الخادم...</p>
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="flex-1 flex flex-col pb-12">
        <Header
          title="العقار غير موجود"
          subtitle="تعذر العثور على العقار المطلوب"
        />
        <div className="p-12 text-center space-y-4">
          <p className="text-slate-400 font-bold">العقار المطلوب غير متوفر أو تم حذفه.</p>
          <Link
            href="/properties"
            className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-bold px-4 py-2 rounded-xl text-xs"
          >
            <ArrowRight className="w-4 h-4" />
            العودة إلى إدارة العقارات
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="تفاصيل العقار – Admin View"
        subtitle="سجل المراجعة، الإحصائيات الكاملة وإجراءات الإشراف"
        lastUpdated="محدث الآن"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <Breadcrumbs
          items={[
            { label: 'الرئيسية', href: '/' },
            { label: 'إدارة العقارات', href: '/properties' },
            { label: property.title },
          ]}
        />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Property Preview Card (4 cols) */}
          <div className="lg:col-span-4 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] flex flex-col items-center">
            {/* Property Image */}
            <div className="w-full h-44 rounded-2xl bg-[var(--badge-bg-muted)] border border-[var(--card-border)] flex items-center justify-center text-[var(--text-subtle)] mb-5 overflow-hidden">
              {property.images && property.images.length > 0 ? (
                <img
                  src={property.images[0]}
                  alt={property.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Building2 className="w-16 h-16 text-slate-300" />
              )}
            </div>

            <h3 className="text-lg font-extrabold text-[var(--foreground)] mb-2 text-center">
              {property.title}
            </h3>

            <div className="mb-6 flex items-center gap-2">
              {property.is_verified ? (
                <span className="inline-flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  موثّق ومقبول
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                  {property.status}
                </span>
              )}
            </div>

            {/* Property Specs List */}
            <div className="w-full space-y-4 border-t border-[var(--divider)] pt-5 text-right text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-subtle)] font-medium">المالك</span>
                <span className="font-bold text-[var(--foreground)]">{property.owner}</span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">السعر</span>
                <span className="font-extrabold text-teal-700 dark:text-teal-400 dir-ltr text-sm font-mono">
                  {property.price} / {property.price_period}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">المساحة</span>
                <span className="font-bold text-[var(--foreground)] dir-ltr">
                  {property.area}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">الغرف</span>
                <span className="font-bold text-[var(--foreground)]">
                  {property.rooms} غرف
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">الموقع</span>
                <span className="font-bold text-[var(--foreground)]">
                  {property.location || 'القاهرة'}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">تاريخ الإضافة</span>
                <span className="font-bold text-[var(--foreground)]">
                  {property.createdDate || 'حديثاً'}
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
                  {property.views.toLocaleString()}
                </div>
                <div className="text-xs font-semibold text-[var(--text-subtle)]">
                  مشاهدات
                </div>
              </div>

              <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
                <div className="text-2xl font-black text-emerald-600 mb-1">
                  {property.visits}
                </div>
                <div className="text-xs font-semibold text-[var(--text-subtle)]">
                  طلبات زيارة
                </div>
              </div>

              <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
                <div className="text-2xl font-black text-[var(--foreground)] mb-1">
                  {property.reports}
                </div>
                <div className="text-xs font-semibold text-[var(--text-subtle)]">
                  بلاغات
                </div>
              </div>
            </div>

            {/* Audit Log Card */}
            <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)]">
              <h4 className="font-bold text-[var(--foreground)] text-base mb-6">
                سجل المراجعة والحالة
              </h4>

              <div className="space-y-4 divide-y divide-[var(--divider)]">
                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      حالة العقار الحالية: {property.status}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    {property.lastUpdated}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      مستوى تقييم المخاطر: {property.riskLevel}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    النظام الآلي
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      تم إنشاء الإدراج بواسطة {property.owner}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    {property.createdDate}
                  </span>
                </div>
              </div>
            </div>

            {/* Bottom Action Controls */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <button
                onClick={handleHideProperty}
                className="py-4 bg-amber-50 hover:bg-amber-100 text-amber-800 font-extrabold text-sm rounded-2xl border border-amber-200 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <EyeOff className="w-4 h-4 text-amber-700" />
                <span>إخفاء العقار</span>
              </button>

              <Link
                href={`/properties/review?id=${property.id}`}
                className="py-4 bg-teal-600 hover:bg-teal-700 text-white font-extrabold text-sm rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>مراجعة واعتماد</span>
              </Link>

              <button
                onClick={handleExportData}
                className="py-4 bg-[var(--badge-bg-muted)] hover:bg-[var(--card-hover)] text-[var(--foreground)] font-extrabold text-sm rounded-2xl border border-[var(--card-border)] transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
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
