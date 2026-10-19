'use client';

import { IdentityImage } from '@/components/ui/IdentityImage';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
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
import { fetchKycDetail, approveKyc, rejectKyc } from '@/lib/api/kyc';
import { KycDetail } from '@/lib/api/types';
import { LogoLoader } from '@/components/ui/LogoLoader';

function IndividualKycReviewContent() {
  const searchParams = useSearchParams();
  const submissionId = searchParams.get('id') || '';

  const [kycData, setKycData] = useState<KycDetail | null>(null);
  const [internalNote, setInternalNote] = useState('');
  const [status, setStatus] = useState<'غير متاح' | 'قيد المراجعة' | 'مقبول' | 'مرفوض'>('غير متاح');
  const [modalType, setModalType] = useState<'approve' | 'reject' | 'reupload' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDeciding, setIsDeciding] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    let current = true;
    setKycData(null);
    setStatus('غير متاح');
    setModalType(null);
    setInternalNote('');
    setIsLoading(Boolean(submissionId));
    async function loadDetail() {
      if (!submissionId) return;
      setIsLoading(true);
      try {
        const data = await fetchKycDetail(submissionId);
        if (!current) return;
        setKycData(data);
        if (data) setStatus(data.status === 'approved' ? 'مقبول' : data.status === 'rejected' ? 'مرفوض' : 'قيد المراجعة');
      } catch {
        if (current) showToast('Identity evidence could not be loaded.', 'error');
      } finally {
        if (current) setIsLoading(false);
      }
    }
    void loadDetail();
    return () => { current = false; };
  }, [submissionId]);

  const userName = kycData?.userName || 'مستخدم';
  const userType = kycData?.userType || 'مستأجر';
  const nationalId = kycData?.nationalId || 'غير مسجل';
  const birthDate = kycData?.birthDate || 'غير محدد';
  const gender = kycData?.gender || 'غير محدد';

  const handleConfirmDecision = async () => {
    if (isDeciding || !modalType || kycData?.id !== submissionId || !kycData?.canReview) { showToast('Load the current pending submission before deciding.', 'error'); return; }
    if (modalType !== 'approve' && !internalNote.trim()) { showToast('Enter the reason that will be visible to the applicant.', 'error'); return; }
    setIsDeciding(true);
    try {
      if (modalType === 'approve') {
        if (kycData?.id) await approveKyc(kycData.id);
        setStatus('مقبول');
        showToast(`تمت الموافقة على توثيق هوية ${userName} بنجاح`, 'success');
      } else if (modalType === 'reject') {
        if (kycData?.id) await rejectKyc(kycData.id, internalNote.trim());
        setStatus('مرفوض');
        showToast('تم رفض طلب التوثيق وتثبيت الحالة في النظام', 'error');
      } else if (modalType === 'reupload') {
        await rejectKyc(kycData.id, internalNote.trim());
        setStatus('مرفوض');
        showToast('Resubmission requested through the recorded rejection reason.', 'success');
      }
    } catch { showToast('The result was not confirmed. Reload the original record before retrying.', 'error'); } finally {
      // Reconcile the authoritative original record before permitting another decision.
      setKycData(null);
      setStatus('غير متاح');
      try {
        const current = await fetchKycDetail(submissionId);
        setKycData(current);
        if (current) setStatus(current.status === 'approved' ? 'مقبول' : current.status === 'rejected' ? 'مرفوض' : 'قيد المراجعة');
      } catch { showToast('Reload the page to read the current review result.', 'error'); }
      setIsDeciding(false);
      setModalType(null);
    }
  };

  const canDecide = !isLoading && !isDeciding && kycData?.id === submissionId && kycData?.canReview === true;

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title={`مراجعة توثيق – ${userName}`}
        subtitle="فحص الهوية الوطنية والمستندات الرسمية لاتخاذ قرار الاعتماد"
        lastUpdated="محدث الآن"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: User Info Card (3.5 cols) */}
          <div className="lg:col-span-4 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] flex flex-col items-center">
            <div className="w-20 h-20 rounded-full bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 text-2xl font-bold mb-3 shadow-inner">
              <User className="w-10 h-10" />
            </div>

            <h3 className="text-lg font-extrabold text-[var(--foreground)] mb-0.5">
              {userName}
            </h3>

            <p className="text-xs text-[var(--text-subtle)] font-semibold mb-3">
              {userType} • عضو مسجل
            </p>

            <div className="mb-6">
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold border ${
                  status === 'مقبول'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : status === 'مرفوض'
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : 'bg-amber-50 text-amber-700 border-amber-200'
                }`}
              >
                {status}
              </span>
            </div>

            {/* User Meta Data Rows */}
            <div className="w-full space-y-3.5 border-t border-[var(--divider)] pt-4 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-subtle)] font-medium">الرقم القومي المدخل</span>
                <span className="font-bold text-[var(--foreground)] font-mono dir-ltr">{nationalId}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[var(--text-subtle)] font-medium">تاريخ الميلاد</span>
                <span className="font-bold text-[var(--foreground)]">{birthDate}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[var(--text-subtle)] font-medium">النوع</span>
                <span className="font-bold text-[var(--foreground)]">{gender}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[var(--text-subtle)] font-medium">تاريخ رفع الطلب</span>
                <span className="font-bold text-[var(--foreground)]">{kycData?.submittedAt || 'غير متاح'}</span>
              </div>
            </div>

            {/* No biometric provider result is present in this request contract. */}
            <div className="w-full mt-6 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl p-3 flex items-start gap-2.5 text-right">
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div>
                <h5 className="font-bold text-xs text-amber-800 dark:text-amber-300">
                  لا تتوفر نتيجة تحقق آلي معتمدة
                </h5>
                <p className="text-[11px] text-amber-700/80 dark:text-amber-400 mt-0.5">
                  عرض الصور لا يثبت حيوية الوجه أو تطابقه مع الهوية. راجع المستندات قبل تسجيل القرار.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: ID Photos & Decision Controls (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Documents Preview Grid */}
            <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
              <h4 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
                المستندات والصور المرفوعة
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* ID Card Front */}
                <div className="border border-[var(--card-border)] rounded-xl p-4 bg-[var(--badge-bg-muted)] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-[var(--foreground)]">
                      وجه بطاقة الهوية (Front)
                    </span>
                  </div>
                  <div className="w-full h-44 bg-slate-200 dark:bg-slate-700/50 rounded-lg flex items-center justify-center border border-dashed border-slate-300 dark:border-slate-600 overflow-hidden">
                    {kycData?.idFaceUrl ? (
                      <IdentityImage src={kycData.idFaceUrl} alt="ID Front" className="w-full h-full object-cover" />
                    ) : (
                      <div className="text-center p-4">
                        <FileText className="w-8 h-8 text-slate-400 mx-auto mb-1" />
                        <span className="text-xs text-[var(--text-muted)] font-medium">
                          معاينة صورة بطاقة الرقم القومي (الوجه)
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* ID Card Back */}
                <div className="border border-[var(--card-border)] rounded-xl p-4 bg-[var(--badge-bg-muted)] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-[var(--foreground)]">
                      ظهر بطاقة الهوية (Back)
                    </span>
                  </div>
                  <div className="w-full h-44 bg-slate-200 dark:bg-slate-700/50 rounded-lg flex items-center justify-center border border-dashed border-slate-300 dark:border-slate-600 overflow-hidden">
                    {kycData?.idBackUrl ? (
                      <IdentityImage src={kycData.idBackUrl} alt="ID Back" className="w-full h-full object-cover" />
                    ) : (
                      <div className="text-center p-4">
                        <FileText className="w-8 h-8 text-slate-400 mx-auto mb-1" />
                        <span className="text-xs text-[var(--text-muted)] font-medium">
                          معاينة صورة بطاقة الرقم القومي (الظهر)
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Live Selfie Check */}
              <div className="border border-[var(--card-border)] rounded-xl p-4 bg-[var(--badge-bg-muted)] space-y-2 mt-4">
                <span className="font-bold text-xs text-[var(--foreground)] block">
                  صورة السيلفي المرفوعة
                </span>
                <div className="w-full h-48 bg-slate-200 dark:bg-slate-700/50 rounded-lg flex items-center justify-center border border-dashed border-slate-300 dark:border-slate-600 overflow-hidden">
                  {kycData?.selfieUrl ? (
                    <IdentityImage src={kycData.selfieUrl} alt="Selfie" className="w-full h-full object-cover" />
                  ) : (
                    <div className="text-center p-4">
                      <User className="w-8 h-8 text-slate-400 mx-auto mb-1" />
                      <span className="text-xs text-[var(--text-muted)] font-medium">
                        لم تُرفق صورة سيلفي
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Decision Controls Container */}
            <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
              <h4 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
                قرار المراجعة الإداري
              </h4>

              <div>
                <label className="text-xs font-bold text-[var(--foreground)] block mb-1.5">
                  سبب الرفض أو طلب إعادة الرفع (يظهر للمستخدم):
                </label>
                <textarea
                  value={internalNote}
                  onChange={(e) => setInternalNote(e.target.value)}
                  placeholder="اكتب السبب الذي سيظهر للمستخدم عند الرفض أو طلب إعادة الرفع..."
                  rows={3}
                  className="w-full p-3 bg-[var(--input-bg)] rounded-xl border border-[var(--card-border)] text-xs text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all placeholder:text-[var(--text-subtle)]"
                ></textarea>
              </div>

              <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
                <button
                  disabled={!canDecide}
                  onClick={() => setModalType('approve')}
                  className="w-full sm:flex-1 py-3 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-md shadow-emerald-600/20"
                >
                  <Check className="w-4 h-4" />
                  <span>قبول وتوثيق الحساب</span>
                </button>

                <button
                  disabled={!canDecide}
                  onClick={() => setModalType('reupload')}
                  className="w-full sm:flex-1 py-3 px-4 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-md shadow-amber-500/20"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>طلب إعادة الرفع</span>
                </button>

                <button
                  disabled={!canDecide}
                  onClick={() => setModalType('reject')}
                  className="w-full sm:flex-1 py-3 px-4 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-md shadow-rose-600/20"
                >
                  <X className="w-4 h-4" />
                  <span>رفض التوثيق</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dynamic Action Modal */}
      <ConfirmModal
        isOpen={!!modalType}
        onClose={() => setModalType(null)}
        onConfirm={handleConfirmDecision}
        title={
          modalType === 'approve'
            ? `قبول وتوثيق حساب ${userName}`
            : modalType === 'reject'
            ? `رفض طلب توثيق ${userName}`
            : `طلب إعادة رفع المستندات من ${userName}`
        }
        message={
          modalType === 'approve'
            ? 'سيُسجَّل اعتماد الهوية. تظل المعاملات الأخرى خاضعة لصلاحياتها وشروطها المستقلة.'
            : modalType === 'reject'
            ? 'سيُسجَّل رفض المستندات والسبب ليتمكن المستخدم من مراجعته وإعادة التقديم.'
            : 'سيُسجَّل رفض الطلب مع السبب الذي أدخلته ليتمكن المستخدم من إعادة التقديم.'
        }
        variant={
          modalType === 'approve' ? 'success' : modalType === 'reject' ? 'danger' : 'warning'
        }
        confirmText={
          modalType === 'approve' ? 'تأكيد القبول' : modalType === 'reject' ? 'تأكيد الرفض' : 'إرسال الطلب'
        }
      />
    </div>
  );
}

export default function IndividualKycReviewPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 p-12 text-center text-slate-400">
          <LogoLoader showLabel label="جاري تحميل صفحة المراجعة..." />
        </div>
      }
    >
      <IndividualKycReviewContent />
    </Suspense>
  );
}

