'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/components/ui/Toast';
import {
  User,
  FileText,
  AlertTriangle,
  Check,
  X,
  RotateCcw,
} from 'lucide-react';

export default function IndividualKycReviewPage() {
  const [internalNote, setInternalNote] = useState('');
  const [status, setStatus] = useState<'قيد المراجعة' | 'مقبول' | 'مرفوض' | 'إعادة رفع'>('قيد المراجعة');
  const [modalType, setModalType] = useState<'approve' | 'reject' | 'reupload' | null>(null);
  const { showToast } = useToast();

  const handleConfirmDecision = () => {
    if (modalType === 'approve') {
      setStatus('مقبول');
      showToast('تمت الموافقة على توثيق هوية سارة أحمد بنجاح', 'success');
    } else if (modalType === 'reject') {
      setStatus('مرفوض');
      showToast('تم رفض طلب التوثيق وتثبيت الحالة في النظام', 'error');
    } else if (modalType === 'reupload') {
      setStatus('إعادة رفع');
      showToast('تم إرسال طلب إعادة رفع المستندات إلى سارة أحمد', 'info');
    }
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="مراجعة توثيق – سارة أحمد خالد"
        subtitle="فحص الهوية الوطنية والمستندات الرسمية لاتخاذ قرار الاعتماد"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: User Info Card (3.5 cols) */}
          <div className="lg:col-span-4 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] flex flex-col items-center">
            <div className="w-20 h-20 rounded-full bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 text-2xl font-bold mb-3 shadow-inner">
              <User className="w-10 h-10" />
            </div>

            <h3 className="text-lg font-extrabold text-[var(--foreground)] mb-0.5">
              سارة أحمد خالد
            </h3>

            <p className="text-xs text-[var(--text-subtle)] font-semibold mb-3">
              مستأجر • عضو منذ 2024
            </p>

            <div className="mb-6">
              <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                status === 'مقبول' ? 'bg-emerald-50 text-emerald-600 border-emerald-200' :
                status === 'مرفوض' ? 'bg-rose-50 text-rose-600 border-rose-200' :
                status === 'إعادة رفع' ? 'bg-blue-50 text-blue-600 border-blue-200' :
                'bg-amber-50 text-amber-600 border-amber-200'
              }`}>
                {status === 'مقبول' ? 'موثّق ومقبول ✓' :
                 status === 'مرفوض' ? 'طلب مرفوض ✗' :
                 status === 'إعادة رفع' ? 'طلب إعادة رفع ⏱' :
                 'قيد المراجعة ⏱'}
              </span>
            </div>

            {/* Info details */}
            <div className="w-full space-y-4 border-t border-[var(--divider)] pt-5 text-right text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-subtle)] font-medium">رقم الهاتف</span>
                <span className="font-bold text-[var(--foreground)] font-mono dir-ltr">
                  01012345432
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">البريد</span>
                <span className="font-bold text-[var(--foreground)] font-mono text-[11px] dir-ltr">
                  sara@gmail.com
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">تاريخ التسجيل</span>
                <span className="font-bold text-[var(--foreground)]">1 يناير 2024</span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">عدد الطلبات</span>
                <span className="font-bold text-[var(--foreground)]">3 طلبات زيارة</span>
              </div>
            </div>
          </div>

          {/* Middle Column: Uploaded Documents (5 cols) */}
          <div className="lg:col-span-5 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-5">
            <h3 className="font-extrabold text-[var(--foreground)] text-base mb-2">
              المستندات المرفوعة
            </h3>

            {/* Doc 1 */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-muted)]">
                وجه البطاقة القومية
              </label>
              <div className="w-full h-36 rounded-2xl bg-[var(--badge-bg-muted)] border border-[var(--card-border)] flex flex-col items-center justify-center text-[var(--text-subtle)] hover:border-teal-500/50 transition-colors cursor-pointer">
                <FileText className="w-10 h-10 text-teal-600 dark:text-teal-400 mb-1" />
                <span className="text-xs font-semibold">صورة البطاقة الأمامية (معاينة)</span>
              </div>
            </div>

            {/* Doc 2 */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-muted)]">
                ظهر البطاقة القومية
              </label>
              <div className="w-full h-36 rounded-2xl bg-[var(--badge-bg-muted)] border border-[var(--card-border)] flex flex-col items-center justify-center text-[var(--text-subtle)] hover:border-teal-500/50 transition-colors cursor-pointer">
                <FileText className="w-10 h-10 text-teal-600 dark:text-teal-400 mb-1" />
                <span className="text-xs font-semibold">صورة البطاقة الخلفية (معاينة)</span>
              </div>
            </div>

            {/* Doc 3 */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-muted)]">
                صورة السيلفي
              </label>
              <div className="w-full h-36 rounded-2xl bg-[var(--badge-bg-muted)] border border-[var(--card-border)] flex flex-col items-center justify-center text-[var(--text-subtle)] hover:border-teal-500/50 transition-colors cursor-pointer">
                <User className="w-10 h-10 text-teal-600 dark:text-teal-400 mb-1" />
                <span className="text-xs font-semibold">صورة سيلفي مباشرة (معاينة)</span>
              </div>
            </div>

            {/* Confidential Warning */}
            <div className="bg-rose-100/70 dark:bg-rose-950/40 border-2 border-rose-300 dark:border-rose-800/80 rounded-2xl p-4 flex items-center justify-center gap-2 text-[#881337] dark:text-[#fecdd3] text-xs font-black text-center shadow-xs">
              <AlertTriangle className="w-4 h-4 shrink-0 text-[#e11d48] dark:text-[#fb7185]" />
              <span>هذه البيانات سرية وخاصة بالنظام – للمراجع المعيّن فقط</span>
            </div>
          </div>

          {/* Right Column: Decision & History Log (3.5 cols) */}
          <div className="lg:col-span-3 space-y-6">
            {/* Decision Card */}
            <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
              <h3 className="font-extrabold text-[var(--foreground)] text-base mb-2">
                قرار التوثيق
              </h3>

              <button
                onClick={() => setModalType('approve')}
                className="w-full py-3.5 bg-emerald-500 hover:bg-emerald-600 text-white font-extrabold text-sm rounded-xl shadow-[var(--shadow-card)] transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <Check className="w-4 h-4" />
                <span>قبول التوثيق ✓</span>
              </button>

              <button
                onClick={() => setModalType('reject')}
                className="w-full py-3.5 bg-rose-500 hover:bg-rose-600 text-white font-extrabold text-sm rounded-xl shadow-[var(--shadow-card)] transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <X className="w-4 h-4" />
                <span>رفض ✗</span>
              </button>

              <button
                onClick={() => setModalType('reupload')}
                className="w-full py-3.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 font-extrabold text-sm rounded-xl border border-amber-200/60 transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <RotateCcw className="w-4 h-4 text-amber-600" />
                <span>طلب إعادة رفع</span>
              </button>

              <div className="pt-2">
                <label className="text-xs font-bold text-[var(--text-subtle)] block mb-1">
                  ملاحظات داخلية (اختياري)
                </label>
                <textarea
                  rows={3}
                  value={internalNote}
                  onChange={(e) => setInternalNote(e.target.value)}
                  placeholder="اكتب ملاحظاتك..."
                  className="w-full p-3 bg-[var(--card-hover)] border border-[var(--card-border)] rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 placeholder:text-[var(--text-subtle)] resize-none"
                ></textarea>
              </div>
            </div>

            {/* Dark Navy Verification History Log */}
            <div className="bg-[#161F28] text-slate-300 rounded-2xl p-6 border border-slate-800 shadow-md">
              <h4 className="font-bold text-white text-sm mb-4">
                سجل التوثيق
              </h4>

              <div className="space-y-3.5 text-xs">
                <div className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0"></span>
                  <span>إرسال الطلب: 9:30 ص</span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-teal-400 shrink-0"></span>
                  <span>مراجعة أولية: 9:41 ص</span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shrink-0"></span>
                  <span>الحالة الحالية: {status}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Decision Confirm Modal */}
      <ConfirmModal
        isOpen={!!modalType}
        onClose={() => setModalType(null)}
        onConfirm={handleConfirmDecision}
        title={
          modalType === 'approve'
            ? 'تأكيد قبول توثيق الهوية'
            : modalType === 'reject'
            ? 'تأكيد رفض طلب التوثيق'
            : 'طلب إعادة رفع المستندات'
        }
        message={
          modalType === 'approve'
            ? 'هل تحققت من مطابقة جميع المستندات وتود منح شارة "حساب موثق" لسارة أحمد؟'
            : modalType === 'reject'
            ? 'هل أنت تأكد من رفض هذا الطلب بسبب عدم تطابق البيانات أو تلف الصورة؟'
            : 'سيتم إرسال تنبيه للمستخدم لإعادة التقاط صور أوضح للهوية الوطنية.'
        }
        variant={modalType === 'approve' ? 'success' : modalType === 'reject' ? 'danger' : 'warning'}
        confirmText={
          modalType === 'approve' ? 'قبول واعتماد' : modalType === 'reject' ? 'تأكيد الرفض' : 'إرسال طلب'
        }
      />
    </div>
  );
}

