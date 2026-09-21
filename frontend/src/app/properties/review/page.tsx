'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/components/ui/Toast';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import {
  Building2,
  AlertTriangle,
  Check,
  X,
  RotateCcw,
} from 'lucide-react';
import {
  fetchAdminProperties,
  fetchAdminPropertyMetrics,
  fetchAdminPropertyDetail,
  approveProperty,
  rejectProperty,
  requestPropertyRevision,
} from '@/lib/api/properties';
import { PropertyItem, PropertyMetrics, PropertyDetail } from '@/lib/api/types';

function PropertyReviewQueueContent() {
  const searchParams = useSearchParams();
  const queryId = searchParams.get('id');

  const [properties, setProperties] = useState<PropertyItem[]>([]);
  const [metrics, setMetrics] = useState<PropertyMetrics>({
    total: 0,
    active: 0,
    pending: 0,
    rejected: 0,
    acceptedToday: 0,
    rejectedToday: 0,
    openReports: 0,
  });
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('');
  const [selectedPropertyDetail, setSelectedPropertyDetail] = useState<PropertyDetail | null>(null);
  const [filterTag, setFilterTag] = useState<'all' | 'images' | 'highRisk'>('all');
  const [decisionModal, setDecisionModal] = useState<'approve' | 'reject' | 'edit' | null>(null);
  const [status, setStatus] = useState<string>('قيد المراجعة');
  const [isLoading, setIsLoading] = useState(true);
  const [checklist, setChecklist] = useState<Array<{ id: string; title: string; passed: boolean }>>([
    { id: 'c1', title: 'الصور واضحة ولا تحتوي على علامات مائية خارجية', passed: true },
    { id: 'c2', title: 'السعر متوافق مع متوسط المنطقة والمساحة', passed: true },
    { id: 'c3', title: 'العنوان والحي والمدينة محددة بدقة', passed: true },
    { id: 'c4', title: 'بيانات المالك متوافقة مع حساب المنصة', passed: true },
    { id: 'c5', title: 'المواصفات (عدد الغرف والمساحة) منطقية', passed: true },
  ]);
  const { showToast } = useToast();

  useEffect(() => {
    async function loadQueue() {
      setIsLoading(true);
      try {
        const [propsRes, metricsRes] = await Promise.allSettled([
          fetchAdminProperties({ page_size: 20 }),
          fetchAdminPropertyMetrics(),
        ]);

        if (propsRes.status === 'fulfilled' && propsRes.value?.results) {
          const list = propsRes.value.results;
          setProperties(list);
          const initialId = queryId || (list.length > 0 ? list[0].id : '');
          setSelectedPropertyId(initialId);
        }

        if (metricsRes.status === 'fulfilled' && metricsRes.value) {
          setMetrics(metricsRes.value);
        }
      } catch (err) {
        console.error('Failed to load review queue:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadQueue();
  }, [queryId]);

  useEffect(() => {
    async function loadDetail() {
      if (!selectedPropertyId) return;
      try {
        const detail = await fetchAdminPropertyDetail(selectedPropertyId);
        if (detail) {
          setSelectedPropertyDetail(detail);
          setStatus(detail.status);
          // Set checklist verification flags based on real data
          setChecklist([
            { id: 'c1', title: 'الصور كافية وواضحة (3+ صور)', passed: (detail.imagesCount || 0) >= 3 },
            { id: 'c2', title: 'السعر محدد بالعملة المحلية بشكل صحيح', passed: detail.price_raw > 0 },
            { id: 'c3', title: 'المدينة والحي مسجلين بدقة', passed: Boolean(detail.city && detail.district) },
            { id: 'c4', title: 'بيانات المالك مفعلة وموثقة', passed: Boolean(detail.owner) },
            { id: 'c5', title: 'عدد الغرف والمساحة مدخلة', passed: Boolean(detail.rooms && detail.area) },
          ]);
        }
      } catch (err) {
        console.error('Failed to load property detail for review:', err);
      }
    }
    loadDetail();
  }, [selectedPropertyId]);

  const filteredList = properties.filter((p) => {
    if (filterTag === 'highRisk') return p.riskLevel === 'عالي الخطر';
    if (filterTag === 'images') return (p.imagesCount || 0) < 3;
    return true;
  });

  const toggleChecklistItem = (id: string) => {
    setChecklist((prev) =>
      prev.map((item) => (item.id === id ? { ...item, passed: !item.passed } : item))
    );
  };

  const handleConfirmDecision = async () => {
    if (!selectedPropertyId || !selectedPropertyDetail) return;
    try {
      if (decisionModal === 'approve') {
        await approveProperty(selectedPropertyId);
        setStatus('مقبول');
        setProperties((prev) =>
          prev.map((p) => (p.id === selectedPropertyId ? { ...p, status: 'مقبول', is_verified: true } : p))
        );
        showToast(`تم قبول وتفعيل إدراج العقار "${selectedPropertyDetail.title}" بنجاح`, 'success');
      } else if (decisionModal === 'reject') {
        await rejectProperty(selectedPropertyId, 'مرفوض من طابور المراجعة الإدارية');
        setStatus('مرفوض');
        setProperties((prev) =>
          prev.map((p) => (p.id === selectedPropertyId ? { ...p, status: 'مرفوض' } : p))
        );
        showToast(`تم رفض العقار "${selectedPropertyDetail.title}" وإخفاؤه`, 'error');
      } else if (decisionModal === 'edit') {
        await requestPropertyRevision(selectedPropertyId, 'طلب تعديل الصور والبيانات');
        setStatus('تعديل');
        setProperties((prev) =>
          prev.map((p) => (p.id === selectedPropertyId ? { ...p, status: 'تعديل' } : p))
        );
        showToast(`تم إرسال طلب تعديل البيانات والصور لمالك العقار`, 'info');
      }
    } catch {
      showToast('حدث خطأ أثناء تنفيذ الإجراء الإداري', 'error');
    } finally {
      setDecisionModal(null);
    }
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="طابور مراجعة العقارات"
        subtitle="فحص طلبات إدراج العقارات، قائمة التحقق الآلية وتقييم المخاطر"
        lastUpdated="محدث الآن"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <Breadcrumbs
          items={[
            { label: 'الرئيسية', href: '/' },
            { label: 'إدارة العقارات', href: '/properties' },
            { label: 'طابور المراجعة' },
          ]}
        />

        {/* Top 4 Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-blue-600 mb-1">
              {metrics.openReports}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              بلاغات نشطة
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {metrics.rejectedToday}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              مرفوض اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1">
              {metrics.acceptedToday}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              مقبول اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {metrics.pending}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              بانتظار المراجعة
            </div>
          </div>
        </div>

        {/* Main 2 Column Split Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Pending Property List (7 cols) */}
          <div className="lg:col-span-7 bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] p-6 space-y-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <h3 className="font-extrabold text-[var(--foreground)] text-base">
                قائمة العقارات للمراجعة
              </h3>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setFilterTag('all')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                    filterTag === 'all'
                      ? 'bg-teal-700 text-white'
                      : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                  }`}
                >
                  كل العقارات
                </button>
                <button
                  onClick={() => setFilterTag('images')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                    filterTag === 'images'
                      ? 'bg-teal-700 text-white'
                      : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                  }`}
                >
                  صور قليلة (&lt;3)
                </button>
                <button
                  onClick={() => setFilterTag('highRisk')}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                    filterTag === 'highRisk'
                      ? 'bg-teal-700 text-white'
                      : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                  }`}
                >
                  عالي الخطر
                </button>
              </div>
            </div>

            {/* List items */}
            <div className="space-y-3">
              {isLoading ? (
                <div className="py-12 text-center text-slate-400">
                  <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                  <p className="text-xs">جاري تحميل قائمة العقارات...</p>
                </div>
              ) : filteredList.length > 0 ? (
                filteredList.map((item) => {
                  const isSelected = item.id === selectedPropertyId;
                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedPropertyId(item.id)}
                      className={`p-4 rounded-xl border flex items-center justify-between transition-all cursor-pointer ${
                        isSelected
                          ? 'border-teal-500 bg-teal-500/10 dark:bg-teal-500/20 shadow-[var(--shadow-card)] ring-1 ring-teal-500/30'
                          : 'border-[var(--card-border)] bg-[var(--card-bg)] hover:bg-[var(--table-row-hover)]'
                      }`}
                    >
                      <div className="flex items-center gap-3.5">
                        <div className="w-10 h-10 rounded-xl bg-[var(--badge-bg-muted)] text-[var(--text-muted)] flex items-center justify-center shrink-0">
                          <Building2 className="w-5 h-5" />
                        </div>

                        <div>
                          <h4 className="font-bold text-[var(--foreground)] text-sm">
                            {item.title}
                          </h4>
                          <p className="text-xs text-[var(--text-subtle)] mt-0.5">
                            {item.owner} • {item.imagesCount || 0} صور • {item.price}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {item.riskLevel === 'عالي الخطر' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200/80 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30">
                            عالي الخطر
                          </span>
                        )}
                        {item.riskLevel === 'متوسط الخطر' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200/80 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30">
                            متوسط الخطر
                          </span>
                        )}
                        {item.riskLevel === 'منخفض الخطر' && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30">
                            منخفض الخطر
                          </span>
                        )}

                        <span className="bg-teal-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg">
                          مراجعة
                        </span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-8 text-center text-slate-400 text-xs font-bold">
                  لا توجد عقارات تطابق هذا الفلتر حالياً.
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Verification Checklist Panel (5 cols) */}
          <div className="lg:col-span-5 bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] p-6 space-y-6">
            <div className="border-b border-[var(--divider)] pb-3 flex items-center justify-between">
              <h3 className="font-extrabold text-[var(--foreground)] text-base leading-tight">
                {selectedPropertyDetail ? selectedPropertyDetail.title : 'قائمة التحقق'}
              </h3>
              <span
                className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                  status === 'مقبول'
                    ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                    : status === 'مرفوض'
                    ? 'bg-rose-50 text-rose-600 border-rose-200'
                    : status === 'تعديل'
                    ? 'bg-amber-50 text-amber-600 border-amber-200'
                    : 'bg-blue-50 text-blue-600 border-blue-200'
                }`}
              >
                {status}
              </span>
            </div>

            {/* Checklist items (Click to toggle) */}
            <div className="space-y-2 text-xs">
              <p className="text-[11px] font-bold text-[var(--text-subtle)] mb-1">
                انقر لتأكيد عناصر القائمة يدويًا:
              </p>
              {checklist.map((check) => (
                <div
                  key={check.id}
                  onClick={() => toggleChecklistItem(check.id)}
                  className="flex items-center justify-between py-2 border-b border-[var(--divider)] cursor-pointer hover:bg-[var(--card-hover)] px-2 rounded-lg transition-colors"
                >
                  <span
                    className={`font-semibold ${
                      check.passed ? 'text-[var(--foreground)]' : 'text-rose-500'
                    }`}
                  >
                    {check.title}
                  </span>
                  {check.passed ? (
                    <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">
                      ✓
                    </span>
                  ) : (
                    <span className="w-5 h-5 rounded-full bg-rose-100 dark:bg-rose-500/20 text-rose-600 dark:text-rose-400 flex items-center justify-center font-bold text-[10px]">
                      ✗
                    </span>
                  )}
                </div>
              ))}
            </div>

            {/* Risk Assessment Box */}
            <div className="space-y-2 bg-rose-100/70 dark:bg-rose-950/40 border-2 border-rose-300 dark:border-rose-800/80 rounded-2xl p-4 text-xs shadow-xs">
              <div className="font-black text-[#9f1239] dark:text-[#fecdd3] text-xs sm:text-sm mb-2 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-[#e11d48] dark:text-[#fb7185] shrink-0" />
                <span>تقييم المخاطر (Risk Assessment):</span>
              </div>
              <div className="flex items-center gap-2 font-black text-[#881337] dark:text-[#ffe4e6] text-xs pr-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#e11d48] dark:bg-[#fb7185] shrink-0"></span>
                <span>
                  مستوى الخطر: {selectedPropertyDetail?.riskLevel || 'منخفض'} • عدد الصور المرفقة: {selectedPropertyDetail?.imagesCount || 0}
                </span>
              </div>
              <div className="flex items-center gap-2 font-black text-[#881337] dark:text-[#ffe4e6] text-xs pr-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#e11d48] dark:bg-[#fb7185] shrink-0"></span>
                <span>
                  المالك: {selectedPropertyDetail?.owner} (سجل بلاغات: {selectedPropertyDetail?.reports || 0})
                </span>
              </div>
            </div>

            {/* Decision Action Buttons */}
            <div className="space-y-2.5 pt-2">
              <button
                onClick={() => setDecisionModal('approve')}
                className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-extrabold text-sm rounded-xl shadow-[var(--shadow-card)] transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <Check className="w-4 h-4" />
                <span>قبول واعتماد العقار ✓</span>
              </button>

              <button
                onClick={() => setDecisionModal('reject')}
                className="w-full py-3 bg-rose-500 hover:bg-rose-600 text-white font-extrabold text-sm rounded-xl shadow-[var(--shadow-card)] transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <X className="w-4 h-4" />
                <span>رفض العقار ✗</span>
              </button>

              <button
                onClick={() => setDecisionModal('edit')}
                className="w-full py-3 bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-400 font-extrabold text-sm rounded-xl border border-amber-200/60 dark:border-amber-500/30 transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <RotateCcw className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                <span>طلب تعديل بيانات من المالك</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Decision Confirm Modal */}
      <ConfirmModal
        isOpen={!!decisionModal}
        onClose={() => setDecisionModal(null)}
        onConfirm={handleConfirmDecision}
        title={
          decisionModal === 'approve'
            ? `قبول وتفعيل إدراج "${selectedPropertyDetail?.title}"`
            : decisionModal === 'reject'
            ? `رفض إدراج "${selectedPropertyDetail?.title}"`
            : `طلب تعديل بيانات "${selectedPropertyDetail?.title}"`
        }
        message={
          decisionModal === 'approve'
            ? 'هل تحققت من صحة البيانات والصور وتود إظهار هذا العقار للمستأجرين في نتائج البحث؟'
            : decisionModal === 'reject'
            ? 'هل أنت تأكد من رفض هذا الإدراج؟ سيتم إخفاء العقار وإشعار المالك.'
            : 'سيتم إرسال إشعار للمالك لإعادة مراجعة المواصفات ورفع صور إضافية.'
        }
        variant={decisionModal === 'approve' ? 'success' : decisionModal === 'reject' ? 'danger' : 'warning'}
        confirmText={decisionModal === 'approve' ? 'قبول واعتماد' : decisionModal === 'reject' ? 'تأكيد الرفض' : 'إرسال طلب التعديل'}
      />
    </div>
  );
}

export default function PropertyReviewQueuePage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 p-12 text-center text-slate-400">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-xs font-bold">جاري تحميل طابور مراجعة العقارات...</p>
        </div>
      }
    >
      <PropertyReviewQueueContent />
    </Suspense>
  );
}

