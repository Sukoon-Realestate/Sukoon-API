'use client';

import React, { useState, useEffect } from 'react';
import { adminPath } from '@/lib/basePath';
import { useRouter } from 'next/navigation';
import Link from '@/components/ui/AdminLink';
import { TableScroll } from '@/components/ui/TableScroll';
import { Header } from '@/components/layout/Header';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { EmptyState } from '@/components/ui/EmptyState';
import { Pagination } from '@/components/ui/Pagination';
import { Search, Building2, Eye, XCircle } from 'lucide-react';
import {
  fetchAdminProperties,
  fetchAdminPropertyMetrics,
} from '@/lib/api/properties';
import { PropertyItem, PropertyMetrics } from '@/lib/api/types';
import { LogoLoader } from '@/components/ui/LogoLoader';

export default function PropertiesManagementPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [propertiesList, setPropertiesList] = useState<PropertyItem[]>([]);
  const [metrics, setMetrics] = useState<PropertyMetrics | null>(null);
  const [typeFilter, setTypeFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [loadedKey, setLoadedKey] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [loadError, setLoadError] = useState('');
  const queryKey = JSON.stringify([currentPage, itemsPerPage, searchQuery, typeFilter, refresh]);
  const isLoading = loadedKey !== queryKey;

  useEffect(() => {
    const controller = new AbortController();
    const params: import('@/lib/api/properties').FetchPropertiesParams = { page: currentPage, page_size: itemsPerPage };
    if (searchQuery.trim()) params.search = searchQuery.trim();
    if (typeFilter !== 'all') params.property_type_id = typeFilter;
    void Promise.allSettled([fetchAdminProperties(params, controller.signal), fetchAdminPropertyMetrics(controller.signal)]).then(([properties, metrics]) => {
      if (controller.signal.aborted) return;
      setPropertiesList(properties.status === 'fulfilled' ? properties.value.results : []);
      setTotalCount(properties.status === 'fulfilled' ? properties.value.count : 0);
      setMetrics(metrics.status === 'fulfilled' ? metrics.value : null);
      setLoadError(properties.status === 'rejected' || metrics.status === 'rejected' ? 'تعذر تحميل القائمة أو بعض إحصاءاتها. أعد المحاولة.' : '');
      setLoadedKey(queryKey);
    });
    return () => controller.abort();
  }, [queryKey, currentPage, itemsPerPage, searchQuery, typeFilter]);

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

      <div className="admin-page-body min-w-0 w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <Breadcrumbs items={[{ label: 'الرئيسية', href: '/' }, { label: 'إدارة العقارات' }]} />
        {loadError && !isLoading && <p role="alert">{loadError}<button className="min-h-12 underline px-3" onClick={() => setRefresh(value => value + 1)}>إعادة المحاولة</button></p>}

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="w-full sm:w-auto text-lg font-extrabold text-[var(--foreground)]">
            إدارة العقارات
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
            <div className="relative min-w-0 w-full sm:flex-1 sm:w-80">
              <input
                type="text"
                placeholder="بحث في العقارات، المالك، المدينة..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full pl-4 pr-10 py-2.5 bg-[var(--card-bg)] rounded-xl border border-[var(--card-border)] text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all placeholder:text-[var(--text-subtle)] text-[var(--foreground)]"
              />
              <Search className="w-4 h-4 text-[var(--text-subtle)] absolute right-3.5 top-3.5" />
            </div>

            <label className="flex min-w-0 w-full flex-col gap-1 text-sm sm:max-w-60">
              نوع العقار
              <select aria-label="نوع العقار" value={typeFilter} disabled={isLoading || !metrics?.propertyTypes}
                onChange={event => { setTypeFilter(event.target.value); setCurrentPage(1); }}
                className="min-h-12 w-full min-w-0 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] px-3">
                <option value="all">جميع الأنواع</option>
                {metrics?.propertyTypes?.map(kind => <option key={kind.id} value={kind.id}>
                  {kind.name}{kind.is_active ? '' : ' — موقوف للاختيار الجديد'}
                </option>)}
              </select>
              {!isLoading && !metrics?.propertyTypes && <span role="status">تعذر تحميل أنواع العقارات. أعد المحاولة.</span>}
            </label>
          </div>
        </div>

        {/* 4 Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-[var(--foreground)] mb-1">
              {metrics?.total.toLocaleString() ?? 'غير متاح'}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              إجمالي العقارات
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1">
              {metrics?.active ?? 'غير متاح'}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">نشط ومقبول</div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {metrics?.pending ?? 'غير متاح'}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              قيد المراجعة
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {metrics?.rejected ?? 'غير متاح'}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">مرفوض / مخفي</div>
          </div>
        </div>

        {/* Properties Data Table */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden">
          <TableScroll>
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
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-[var(--text-muted)]">
                      <LogoLoader showLabel label="جاري تحميل قائمة العقارات من الخادم..." />
                    </td>
                  </tr>
                ) : propertiesList.length > 0 ? (
                  propertiesList.map((prop) => (
                    <tr
                      key={prop.id}
                      className="hover:bg-[var(--table-row-hover)] transition-colors"
                    >
                      <td className="py-4 px-6 font-bold text-[var(--foreground)] flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-[var(--badge-bg-muted)] text-[var(--text-muted)] flex items-center justify-center shrink-0">
                          <Building2 className="w-4 h-4" />
                        </div>
                        <Link
                          href={`/properties/${prop.id}`}
                          className="hover:text-teal-400 transition-colors"
                        >
                          {prop.title}
                        </Link>
                      </td>
                      <td className="py-4 px-6 text-[var(--text-muted)] font-medium text-xs">
                        {prop.owner || '—'}
                      </td>
                      <td className="py-4 px-6">
                        <span className="bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400 border border-teal-200/60 text-xs font-bold px-2.5 py-0.5 rounded-full">
                          {prop.type}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        {prop.status === 'مقبول' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30">
                            مقبول ✓
                          </span>
                        )}
                        {prop.status === 'قيد المراجعة' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200/80 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30">
                            قيد المراجعة ⏱
                          </span>
                        )}
                        {prop.status === 'مرفوض' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200/80 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30">
                            مرفوض ✗
                          </span>
                        )}
                        {prop.status === 'تعديل' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200/80 dark:bg-blue-500/15 dark:text-blue-300 dark:border-blue-500/30">
                            طلب تعديل ↻
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-6 font-bold text-teal-700 dark:text-teal-400 text-xs dir-ltr text-right">
                        {prop.price}
                      </td>
                      <td className="py-4 px-6 text-[var(--text-muted)] text-xs font-medium">
                        {prop.views || 0}
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center justify-center gap-2">
                          <Link
                            href={`/properties/review?id=${prop.id}`}
                            className="inline-flex items-center gap-1 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer btn-press shadow-xs"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>مراجعة</span>
                          </Link>
                          {prop.status !== 'مرفوض' && (
                            <button
                              onClick={() => { router.push(adminPath(`/properties/review?id=${encodeURIComponent(prop.id)}`)); }}
                              className="inline-flex items-center gap-1 bg-rose-50 text-rose-700 border border-rose-200/80 hover:bg-rose-100 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30 dark:hover:bg-rose-500/25 text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer btn-press"
                            >
                              <XCircle className="w-3.5 h-3.5" />
                              <span>مراجعة</span>
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
          </TableScroll>

          {/* Pagination */}
          <Pagination
            currentPage={currentPage}
            totalPages={Math.max(1, Math.ceil((totalCount || 0) / (itemsPerPage || 10)))}
            totalItems={totalCount || 0}
            itemsPerPage={itemsPerPage}
            onPageChange={setCurrentPage}
            onItemsPerPageChange={(size) => {
              setItemsPerPage(size);
              setCurrentPage(1);
            }}
          />
        </div>
      </div>


    </div>
  );
}
