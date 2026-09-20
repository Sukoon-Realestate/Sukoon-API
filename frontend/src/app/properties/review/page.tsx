'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/components/ui/Toast';
import {
  Building2,
  AlertTriangle,
  Check,
  X,
  RotateCcw,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import {
  mockProperties,
  propertyMetrics,
  propertyVerificationChecklist as initialChecklist,
  propertyRiskFlags,
} from '@/data/mockData';

export default function PropertyReviewQueuePage() {
  const [selectedPropertyId, setSelectedPropertyId] = useState('prop-1');
  const [filterTag, setFilterTag] = useState<'all' | 'images' | 'highRisk'>('all');
  const [checklist, setChecklist] = useState(initialChecklist);
  const [decisionModal, setDecisionModal] = useState<'approve' | 'reject' | 'edit' | null>(null);
  const [status, setStatus] = useState<'قيد المراجعة' | 'مقبول' | 'مرفوض' | 'تعديل'>('قيد المراجعة');
  const { showToast } = useToast();

  const selectedProperty =
    mockProperties.find((p) => p.id === selectedPropertyId) || mockProperties[0];

  const filteredList = mockProperties.filter((p) => {
    if (filterTag === 'highRisk') return p.riskLevel === 'عالي الخطر';
    if (filterTag === 'images') return (p.imagesCount || 0) < 5;
    return true;
  });

  const toggleChecklistItem = (id: string) => {
    setChecklist((prev) =>
      prev.map((item) => (item.id === id ? { ...item, passed: !item.passed } : item))
    );
  };

  const handleConfirmDecision = () => {
    if (decisionModal === 'approve') {
      setStatus('مقبول');
      showToast(`تم قبول إدراج العقار "${selectedProperty.title}" بنجاح`, 'success');
    } else if (decisionModal === 'reject') {
      setStatus('مرفوض');
      showToast(`تم رفض العقار "${selectedProperty.title}" وإبلاغ المالك`, 'error');
    } else if (decisionModal === 'edit') {
      setStatus('تعديل');
      showToast(`تم إرسال طلب تعديل البيانات والصور للمالك`, 'info');
    }
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="طابور مراجعة العقارات"
        subtitle="فحص طلبات إدراج العقارات، قائمة التحقق الآلية وتقييم المخاطر"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 4 Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-blue-600 mb-1">
              {propertyMetrics.openReports}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              بلاغات نشطة
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-rose-500 mb-1">
              {propertyMetrics.rejectedToday}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              مرفوض اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-emerald-600 mb-1">
              {propertyMetrics.acceptedToday}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              مقبول اليوم
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center">
            <div className="text-2xl font-black text-amber-500 mb-1">
              {propertyMetrics.pending}
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
                قائمة العقارات المعلقة
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
                  تحتاج صور
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
              {filteredList.map((item) => {
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

                      <button className="bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer">
                        مراجعة
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Verification Checklist Panel (5 cols) */}
          <div className="lg:col-span-5 bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] p-6 space-y-6">
            <div className="border-b border-[var(--divider)] pb-3 flex items-center justify-between">
              <h3 className="font-extrabold text-[var(--foreground)] text-base leading-tight">
                قائمة التحقق – {selectedProperty.title}
              </h3>
              <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                status === 'مقبول' ? 'bg-emerald-50 text-emerald-600 border-emerald-200' :
                status === 'مرفوض' ? 'bg-rose-50 text-rose-600 border-rose-200' :
                status === 'تعديل' ? 'bg-amber-50 text-amber-600 border-amber-200' :
                'bg-blue-50 text-blue-600 border-blue-200'
              }`}>
                {status}
              </span>
            </div>

            {/* Checklist items (Click to toggle) */}
            <div className="space-y-2 text-xs">
              <p className="text-[11px] font-bold text-[var(--text-subtle)] mb-1">انقر للتأكد يدويًا من عناصر القائمة:</p>
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

            {/* Risk Flags Box */}
            <div className="space-y-2 bg-rose-50/50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 rounded-xl p-3.5 text-xs text-rose-800 dark:text-rose-300">
              <div className="font-bold mb-1">ملاحظات المخاطر (Risk Flags):</div>
              {propertyRiskFlags.map((flag, idx) => (
                <div key={idx} className="flex items-center gap-2 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                  <span>{flag}</span>
                </div>
              ))}
            </div>

            {/* Decision Action Buttons */}
            <div className="space-y-2.5 pt-2">
              <button
                onClick={() => setDecisionModal('approve')}
                className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-extrabold text-sm rounded-xl shadow-[var(--shadow-card)] transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <Check className="w-4 h-4" />
                <span>قبول العقار ✓</span>
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
                <span>طلب تعديل بيانات</span>
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
            ? `قبول وتفعيل إدراج "${selectedProperty.title}"`
            : decisionModal === 'reject'
            ? `رفض إدراج "${selectedProperty.title}"`
            : `طلب تعديل بيانات "${selectedProperty.title}"`
        }
        message={
          decisionModal === 'approve'
            ? 'هل تحققت من صحة البيانات والصور وتود إظهار هذا العقار للمستأجرين في البحث؟'
            : decisionModal === 'reject'
            ? 'هل أنت تأكد من رفض إدراج هذا العقار نهائياً؟'
            : 'سيتم إرسال إشعار للمالك لإعادة رفع صور بدقة أعلى أو توضيح التفاصيل.'
        }
        variant={decisionModal === 'approve' ? 'success' : decisionModal === 'reject' ? 'danger' : 'warning'}
        confirmText={decisionModal === 'approve' ? 'قبول واعتماد' : decisionModal === 'reject' ? 'تأكيد الرفض' : 'إرسال طلب التعديل'}
      />
    </div>
  );
}

