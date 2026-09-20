'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/components/ui/Toast';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { EmptyState } from '@/components/ui/EmptyState';
import { Pagination } from '@/components/ui/Pagination';
import { Search, Filter, Building2, Eye, XCircle, CheckCircle2 } from 'lucide-react';
import { mockProperties, propertyMetrics, PropertyItem } from '@/data/mockData';

export default function PropertiesManagementPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [propertiesList, setPropertiesList] = useState<PropertyItem[]>(mockProperties);
  const [showFilterDrawer, setShowFilterDrawer] = useState(false);
  const [typeFilter, setTypeFilter] = useState<'all' | 'شقة' | 'ستوديو' | 'غرفة' | 'فيلا'>('all');
  const [selectedPropertyToReject, setSelectedPropertyToReject] = useState<PropertyItem | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const { showToast } = useToast();

  const filteredProperties = propertiesList.filter((prop) => {
    const matchesSearch =
      prop.title.includes(searchQuery) ||
      prop.owner.includes(searchQuery) ||
      prop.type.includes(searchQuery);

    if (!matchesSearch) return false;
    if (typeFilter !== 'all' && prop.type !== typeFilter) return false;
    return true;
  });

  const paginatedProperties = filteredProperties.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleConfirmReject = () => {
    if (!selectedPropertyToReject) return;
    setPropertiesList((prev) =>
      prev.map((p) => (p.id === selectedPropertyToReject.id ? { ...p, status: 'مرفوض' } : p))
    );
    showToast(`تم رفض إدراج العقار "${selectedPropertyToReject.title}"`, 'error');
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setTypeFilter('all');
    setCurrentPage(1);
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="إدارة العقارات"
        subtitle="متابعة كل العقارات المعروضة، المراجعة وإجراءات الموافقة والرفض"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <Breadcrumbs />
        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="w-full sm:w-auto text-lg font-extrabold text-[var(--foreground)]">
            إدارة العقارات
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-80">
              <input
                type="text"
                placeholder="بحث في العقارات..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-4 pr-10 py-2.5 bg-[var(--card-bg)] rounded-xl border border-[var(--card-border)] text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all placeholder:text-[var(--text-subtle)] text-[var(--foreground)]"
              />
              <Search className="w-4 h-4 text-[var(--text-subtle)] absolute right-3.5 top-3.5" />
            </div>

            <div className="relative">
              <button
                onClick={() => setShowFilterDrawer(!showFilterDrawer)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-semibold transition-colors shadow-[var(--shadow-card)] cursor-pointer ${
                  showFilterDrawer || typeFilter !== 'all'
                    ? 'bg-teal-700 text-white border-teal-800'
                    : 'bg-[var(--card-bg)] text-teal-700 hover:bg-[var(--card-hover)] border-[var(--card-border)]'
                }`}
              >
                <Filter className="w-4 h-4" />
                <span>تصفية ({typeFilter === 'all' ? 'الكل' : typeFilter})</span>
              </button>

              {/* Filter Dropdown */}
              {showFilterDrawer && (
                <div className="absolute top-12 left-0 w-48 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-xl p-3 z-30 animate-fadeInUp">
                  <p className="text-xs font-bold text-[var(--text-muted)] mb-2 px-1">نوع العقار:</p>
                  <div className="space-y-1">
                    {(['all', 'شقة', 'ستوديو', 'غرفة', 'فيلا'] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => { setTypeFilter(t); setShowFilterDrawer(false); }}
                        className={`w-full text-right px-3 py-1.5 rounded-xl text-xs font-bold transition-colors ${typeFilter === t ? 'bg-teal-500/15 text-teal-600' : 'text-[var(--foreground)] hover:bg-[var(--card-hover)]'}`}
                      >
                        {t === 'all' ? 'جميع الأنواع' : t}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 4 Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-[var(--foreground)] mb-1">
              {propertyMetrics.total.toLocaleString()}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              إجمالي العقارات
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1">
              {propertyMetrics.active}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">نشط</div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {propertyMetrics.pending}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              قيد المراجعة
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {propertyMetrics.rejected}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">مرفوض</div>
          </div>
        </div>

        {/* Properties Data Table */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-[var(--table-header-bg)] border-b border-[var(--card-border)] text-[var(--text-muted)] text-xs font-bold">
                  <th className="py-4 px-6">العقار</th>
                  <th className="py-4 px-6">المالك</th>
                  <th className="py-4 px-6">النوع</th>
                  <th className="py-4 px-6">الحالة</th>
                  <th className="py-4 px-6">السعر</th>
                  <th className="py-4 px-6">المشاهدات</th>
                  <th className="py-4 px-6 text-center">إجراء</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--divider)] text-sm">
                {paginatedProperties.length > 0 ? (
                  paginatedProperties.map((prop) => (
                    <tr
                      key={prop.id}
                      className="hover:bg-[var(--table-row-hover)] transition-colors"
                    >
                      <td className="py-4 px-6 font-bold text-[var(--foreground)] flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-[var(--badge-bg-muted)] text-[var(--text-muted)] flex items-center justify-center shrink-0">
                          <Building2 className="w-4 h-4" />
                        </div>
                        <span>{prop.title}</span>
                      </td>
                      <td className="py-4 px-6 text-[var(--text-muted)] font-medium text-xs">
                        {prop.owner}
                      </td>
                      <td className="py-4 px-6">
                        <span className="bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400 border border-teal-200/60 text-xs font-bold px-2.5 py-0.5 rounded-full">
                          {prop.type}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        {prop.status === 'مقبول' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
                            مقبول ✓
                          </span>
                        )}
                        {prop.status === 'قيد المراجعة' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-600 border border-amber-200">
                            قيد المراجعة ⏱
                          </span>
                        )}
                        {prop.status === 'مرفوض' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-600 border border-rose-200">
                            مرفوض ✗
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-6 font-bold text-teal-700 dark:text-teal-400 text-xs dir-ltr text-right">
                        {prop.price}
                      </td>
                      <td className="py-4 px-6 text-[var(--text-muted)] text-xs font-medium">
                        {prop.views}
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center justify-center gap-2">
                          <Link
                            href={`/properties/review`}
                            className="inline-flex items-center gap-1 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer btn-press"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>مراجعة</span>
                          </Link>
                          {prop.status !== 'مرفوض' && (
                            <button
                              onClick={() => setSelectedPropertyToReject(prop)}
                              className="inline-flex items-center gap-1 bg-rose-50 hover:bg-rose-100 text-rose-600 dark:bg-rose-500/15 dark:text-rose-400 text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer btn-press"
                            >
                              <XCircle className="w-3.5 h-3.5" />
                              <span>رفض</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="p-0 border-0">
                      <EmptyState
                        title="لم نجد أي عقار يطابق خيارات البحث"
                        description="جرب البحث باسم العقار، اسم المالك، أو تغيير الفئة لتسريع العثور على الإدراج المطلوب."
                        onReset={handleResetFilters}
                      />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <Pagination
            currentPage={currentPage}
            totalPages={Math.ceil(filteredProperties.length / itemsPerPage)}
            totalItems={filteredProperties.length}
            itemsPerPage={itemsPerPage}
            onPageChange={setCurrentPage}
            onItemsPerPageChange={(size) => {
              setItemsPerPage(size);
              setCurrentPage(1);
            }}
          />
        </div>
      </div>

      {/* Reject Modal */}
      <ConfirmModal
        isOpen={!!selectedPropertyToReject}
        onClose={() => setSelectedPropertyToReject(null)}
        onConfirm={handleConfirmReject}
        title={`رفض إدراج العقار: ${selectedPropertyToReject?.title}`}
        message="هل أنت تأكد من رفض إدراج هذا العقار؟ سيتم إخطار المالك بالأسباب."
        variant="danger"
        confirmText="تأكيد الرفض"
      />
    </div>
  );
}

