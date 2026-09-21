'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  PlusCircle,
  Download,
  UserPlus,
  ShieldAlert,
  Sparkles,
  Command,
} from 'lucide-react';
import { useToast } from './Toast';
import { ConfirmModal } from './ConfirmModal';

export const QuickActionsToolbar: React.FC = () => {
  const { showToast } = useToast();
  const [showExportModal, setShowExportModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);

  const handleExport = () => {
    showToast('جاري تجهيز تقرير النظام بصيغة PDF...', 'info');
    setTimeout(() => {
      showToast('تم تصدير التقرير الشامل بنجاح!', 'success');
    }, 1500);
  };

  const handleInvite = () => {
    showToast('تم إرسال دعوة المشرف الجديد عبر البريد الإلكتروني', 'success');
  };

  return (
    <>
      <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl p-4 shadow-[var(--shadow-card)] mb-6 animate-fadeIn flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center border border-teal-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-extrabold text-sm text-[var(--foreground)] leading-tight">
              أدوات التشغيل السريع
            </h4>
            <p className="text-[11px] text-[var(--text-muted)] font-medium">
              اختصارات المشرف الرئيسي للتنفيذ المباشر
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          <Link
            href="/properties/review"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-gradient-to-r from-teal-600 via-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white font-extrabold text-xs rounded-xl shadow-xs shadow-teal-600/25 transition-all cursor-pointer btn-press shrink-0"
          >
            <PlusCircle className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>مراجعة العقارات</span>
          </Link>

          <button
            onClick={() => setShowExportModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 dark:bg-[var(--card-hover)] dark:hover:bg-[var(--card-border)] dark:text-[var(--foreground)] border border-slate-200 dark:border-[var(--card-border)] font-bold text-xs rounded-xl transition-all cursor-pointer btn-press shrink-0"
          >
            <Download className="w-3.5 h-3.5 text-teal-700 dark:text-teal-400 stroke-[2.5]" />
            <span>تصدير PDF</span>
            <span className="hidden md:inline-block text-[10px] bg-slate-200 dark:bg-[var(--badge-bg-muted)] text-slate-700 dark:text-[var(--text-muted)] px-1.5 py-0.5 rounded font-mono font-bold">
              Ctrl+E
            </span>
          </button>

          <button
            onClick={() => setShowInviteModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-50/90 hover:bg-blue-100/90 text-blue-800 dark:bg-[var(--card-hover)] dark:hover:bg-[var(--card-border)] dark:text-[var(--foreground)] border border-blue-200/90 dark:border-[var(--card-border)] font-bold text-xs rounded-xl transition-all cursor-pointer btn-press shrink-0"
          >
            <UserPlus className="w-3.5 h-3.5 text-blue-700 dark:text-blue-400 stroke-[2.5]" />
            <span>دعوة مشرف</span>
          </button>

          <Link
            href="/users/suspended"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-rose-50/90 hover:bg-rose-100/90 text-rose-800 dark:bg-rose-500/15 dark:hover:bg-rose-500/25 dark:text-rose-300 border border-rose-200/90 dark:border-rose-500/30 font-bold text-xs rounded-xl transition-all cursor-pointer shrink-0"
          >
            <ShieldAlert className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>طابور الحظر (43)</span>
          </Link>
        </div>
      </div>

      {/* Confirmation Modals */}
      <ConfirmModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        onConfirm={handleExport}
        title="تصدير تقرير المنصة"
        message="هل ترغب في توليد وتنزيل التقرير الشامل لجميع الأنشطة والإيرادات بصيغة PDF؟"
        confirmText="تأكيد التصدير"
        variant="info"
      />

      <ConfirmModal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        onConfirm={handleInvite}
        title="دعوة مشرف جديد"
        message="سيتم إرسال رابط تفعيل حساب المشرف ذو الصلاحيات المحددة عبر البريد الإلكتروني."
        confirmText="إرسال الدعوة"
        variant="success"
      />
    </>
  );
};
