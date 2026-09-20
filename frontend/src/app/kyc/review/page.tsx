'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
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

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="مراجعة توثيق – سارة أحمد خالد"
        subtitle="فحص الهوية الوطنية والمستندات الرسمية لاتخاذ قرار الاعتماد"
        lastUpdated="9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: User Info Card (3.5 cols) */}
          <div className="lg:col-span-4 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col items-center">
            <div className="w-20 h-20 rounded-full bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 text-2xl font-bold mb-3 shadow-inner">
              <User className="w-10 h-10" />
            </div>

            <h3 className="text-lg font-extrabold text-slate-900 mb-0.5">
              سارة أحمد خالد
            </h3>

            <p className="text-xs text-slate-400 font-semibold mb-3">
              مستأجر • عضو منذ 2024
            </p>

            <div className="mb-6">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-600 border border-amber-200">
                قيد المراجعة ⏱
              </span>
            </div>

            {/* Info details */}
            <div className="w-full space-y-4 border-t border-slate-100 pt-5 text-right text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">رقم الهاتف</span>
                <span className="font-bold text-slate-800 font-mono dir-ltr">
                  01******432
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="text-slate-400 font-medium">البريد</span>
                <span className="font-bold text-slate-800 font-mono text-[11px] dir-ltr">
                  sara@gmail.com
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="text-slate-400 font-medium">تاريخ التسجيل</span>
                <span className="font-bold text-slate-800">1 يناير 2024</span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="text-slate-400 font-medium">عدد الطلبات</span>
                <span className="font-bold text-slate-800">3 طلبات زيارة</span>
              </div>
            </div>
          </div>

          {/* Middle Column: Uploaded Documents (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-5">
            <h3 className="font-extrabold text-slate-800 text-base mb-2">
              المستندات المرفوعة
            </h3>

            {/* Doc 1 */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-500">
                وجه البطاقة القومية
              </label>
              <div className="w-full h-36 rounded-2xl bg-slate-100 border border-slate-200 flex flex-col items-center justify-center text-slate-400">
                <FileText className="w-10 h-10 text-slate-300 mb-1" />
                <span className="text-xs font-semibold">صورة البطاقة الأمامية</span>
              </div>
            </div>

            {/* Doc 2 */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-500">
                ظهر البطاقة القومية
              </label>
              <div className="w-full h-36 rounded-2xl bg-slate-100 border border-slate-200 flex flex-col items-center justify-center text-slate-400">
                <FileText className="w-10 h-10 text-slate-300 mb-1" />
                <span className="text-xs font-semibold">صورة البطاقة الخلفية</span>
              </div>
            </div>

            {/* Doc 3 */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-500">
                صورة السيلفي
              </label>
              <div className="w-full h-36 rounded-2xl bg-slate-100 border border-slate-200 flex flex-col items-center justify-center text-slate-400">
                <User className="w-10 h-10 text-slate-300 mb-1" />
                <span className="text-xs font-semibold">صورة سيلفي مباشرة</span>
              </div>
            </div>

            {/* Confidential Warning */}
            <div className="bg-rose-50 border border-rose-200/60 rounded-xl p-3.5 flex items-center justify-center gap-2 text-rose-700 text-xs font-bold text-center">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>هذه البيانات سرية – للمراجع فقط</span>
            </div>
          </div>

          {/* Right Column: Decision & History Log (3.5 cols) */}
          <div className="lg:col-span-3 space-y-6">
            {/* Decision Card */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
              <h3 className="font-extrabold text-slate-800 text-base mb-2">
                قرار التوثيق
              </h3>

              <button className="w-full py-3.5 bg-emerald-500 hover:bg-emerald-600 text-white font-extrabold text-sm rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2">
                <Check className="w-4 h-4" />
                <span>قبول التوثيق ✓</span>
              </button>

              <button className="w-full py-3.5 bg-rose-500 hover:bg-rose-600 text-white font-extrabold text-sm rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2">
                <X className="w-4 h-4" />
                <span>رفض ✗</span>
              </button>

              <button className="w-full py-3.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 font-extrabold text-sm rounded-xl border border-amber-200/60 transition-colors flex items-center justify-center gap-2">
                <RotateCcw className="w-4 h-4 text-amber-600" />
                <span>طلب إعادة رفع</span>
              </button>

              <div className="pt-2">
                <label className="text-xs font-bold text-slate-400 block mb-1">
                  ملاحظات داخلية (اختياري)
                </label>
                <textarea
                  rows={3}
                  value={internalNote}
                  onChange={(e) => setInternalNote(e.target.value)}
                  placeholder="اكتب ملاحظاتك..."
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 placeholder:text-slate-400 resize-none"
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
                  <span>قيد المراجعة البشرية</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
