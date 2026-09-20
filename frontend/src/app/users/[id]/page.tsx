'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import {
  User,
  ShieldCheck,
  Calendar,
  MessageSquare,
  Heart,
  AlertOctagon,
  UserX,
  Download,
  Star,
} from 'lucide-react';
import { mockUsers } from '@/data/mockData';

export default function UserProfilePage() {
  const params = useParams();
  const userId = params?.id as string;

  // Find user by ID or default to Sara
  const user = mockUsers.find((u) => u.id === userId) || mockUsers[0];

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title={`ملف المستخدم – ${user.name}`}
        subtitle="تفاصيل الحساب الكاملة، سجل النشاطات والإجراءات المتاحة"
        lastUpdated="9:41 ص"
      />

      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: User Profile Details Card (4 cols) */}
          <div className="lg:col-span-4 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col items-center text-center">
            {/* Avatar Circle */}
            <div className="w-24 h-24 rounded-full bg-teal-50 border-2 border-teal-200 flex items-center justify-center text-teal-700 text-3xl font-bold mb-4 shadow-inner">
              <User className="w-12 h-12" />
            </div>

            <h3 className="text-xl font-extrabold text-slate-900 mb-1">
              {user.name}
            </h3>

            <div className="flex items-center gap-2 mb-6">
              <StatusBadge type="kycStatus" value={user.kycStatus} />
              <span className="text-xs text-slate-500 font-semibold">
                {user.type}
              </span>
            </div>

            {/* Field Rows */}
            <div className="w-full space-y-4 border-t border-slate-100 pt-5 text-right text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">رقم الهاتف (admin)</span>
                <span className="font-bold text-slate-800 dir-ltr font-mono">
                  {user.phone || '01012345432'}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="text-slate-400 font-medium">البريد الإلكتروني</span>
                <span className="font-bold text-slate-800 font-mono text-[11px] dir-ltr">
                  {user.email}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="text-slate-400 font-medium">تاريخ الانضمام</span>
                <span className="font-bold text-slate-800">{user.regDate}</span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="text-slate-400 font-medium">آخر نشاط</span>
                <span className="font-bold text-slate-800">{user.lastActive}</span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="text-slate-400 font-medium">توثيق الهوية</span>
                <span className="font-bold text-emerald-600 flex items-center gap-1">
                  موثّق <ShieldCheck className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Metrics, Activity Log & Action Buttons (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Top 3 Stat Cards */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
                <div className="text-2xl font-black text-slate-900 mb-1">
                  {user.visitRequests || 12}
                </div>
                <div className="text-xs font-semibold text-slate-400">
                  طلبات زيارة
                </div>
              </div>

              <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
                <div className="text-2xl font-black text-amber-500 mb-1 flex items-center justify-center gap-1">
                  <span>{user.rating || 4.7}</span>
                  <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                </div>
                <div className="text-xs font-semibold text-slate-400">
                  تقييمات
                </div>
              </div>

              <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs text-center">
                <div className="text-2xl font-black text-slate-900 mb-1">
                  {user.reportsAgainst || 0}
                </div>
                <div className="text-xs font-semibold text-slate-400">
                  بلاغات ضده
                </div>
              </div>
            </div>

            {/* Activity Log Timeline Widget */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
              <h4 className="font-bold text-slate-800 text-base mb-6">
                سجل النشاط
              </h4>

              <div className="space-y-4 divide-y divide-slate-100">
                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
                      <Calendar className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-semibold text-slate-700">
                      حجز زيارة – شقة مدينة نصر
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 font-medium">
                    اليوم 9:30 ص
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-semibold text-slate-700">
                      تم توثيق الهوية
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 font-medium">
                    أمس 3:00 م
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                      <MessageSquare className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-semibold text-slate-700">
                      إرسال رسالة للمالك أحمد
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 font-medium">
                    أمس 2:45 م
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-500 flex items-center justify-center">
                      <Heart className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-semibold text-slate-700">
                      حفظ عقار ستوديو التجمع
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 font-medium">
                    الأحد 10:00 ص
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons Bar */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <button className="py-4 bg-amber-500 hover:bg-amber-600 text-white font-extrabold text-sm rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2">
                <AlertOctagon className="w-4 h-4" />
                <span>تحذير</span>
              </button>

              <button className="py-4 bg-rose-500 hover:bg-rose-600 text-white font-extrabold text-sm rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2">
                <UserX className="w-4 h-4" />
                <span>إيقاف مؤقت</span>
              </button>

              <button className="py-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-extrabold text-sm rounded-2xl border border-slate-200/80 transition-all flex items-center justify-center gap-2">
                <Download className="w-4 h-4 text-slate-500" />
                <span>تصدير البيانات</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
