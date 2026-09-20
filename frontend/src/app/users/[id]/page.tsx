'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/components/ui/Toast';
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
  const { showToast } = useToast();

  // Find user by ID or default to Sara
  const initialUser = mockUsers.find((u) => u.id === userId) || mockUsers[0];
  const [user, setUser] = useState(initialUser);
  const [showWarnModal, setShowWarnModal] = useState(false);
  const [showSuspendModal, setShowSuspendModal] = useState(false);

  const handleSendWarning = () => {
    showToast(`تم إرسال تحذير إداري إلى ${user.name} بنجاح`, 'info');
  };

  const handleToggleSuspend = () => {
    const isSuspended = user.status === 'موقوف';
    setUser((prev) => ({ ...prev, status: isSuspended ? 'نشط' : 'موقوف' }));
    showToast(
      isSuspended ? `تم تنشيط حساب ${user.name}` : `تم إيقاف حساب ${user.name} مؤقتاً`,
      isSuspended ? 'success' : 'error'
    );
  };

  const handleExportData = () => {
    showToast(`جاري تجهيز وتنزيل ملف بيانات ${user.name}...`, 'success');
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title={`ملف المستخدم – ${user.name}`}
        subtitle="تفاصيل الحساب الكاملة، سجل النشاطات والإجراءات المتاحة"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: User Profile Details Card (4 cols) */}
          <div className="lg:col-span-4 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] flex flex-col items-center text-center animate-fadeInUp">
            {/* Avatar Circle */}
            <div className="w-24 h-24 rounded-full bg-teal-50 dark:bg-teal-500/10 border-2 border-teal-200 dark:border-teal-500/30 flex items-center justify-center text-teal-700 dark:text-teal-400 text-3xl font-bold mb-4 shadow-inner">
              <User className="w-12 h-12" />
            </div>

            <h3 className="text-xl font-extrabold text-[var(--foreground)] mb-1">
              {user.name}
            </h3>

            <div className="flex items-center gap-2 mb-6">
              <StatusBadge type="kycStatus" value={user.kycStatus} />
              <span className="text-xs text-[var(--text-muted)] font-semibold">
                {user.type}
              </span>
            </div>

            {/* Field Rows */}
            <div className="w-full space-y-4 border-t border-[var(--divider)] pt-5 text-right text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-subtle)] font-medium">رقم الهاتف (admin)</span>
                <span className="font-bold text-[var(--foreground)] dir-ltr font-mono">
                  {user.phone || '01012345432'}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">البريد الإلكتروني</span>
                <span className="font-bold text-[var(--foreground)] font-mono text-[11px] dir-ltr">
                  {user.email}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">تاريخ الانضمام</span>
                <span className="font-bold text-[var(--foreground)]">{user.regDate}</span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">آخر نشاط</span>
                <span className="font-bold text-[var(--foreground)]">{user.lastActive}</span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-[var(--text-subtle)] font-medium">توثيق الهوية</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  {user.kycStatus} <ShieldCheck className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Metrics, Activity Log & Action Buttons (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Top 3 Stat Cards */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-scaleIn">
                <div className="text-2xl font-black text-[var(--foreground)] mb-1">
                  {user.visitRequests || 12}
                </div>
                <div className="text-xs font-semibold text-[var(--text-subtle)]">
                  طلبات زيارة
                </div>
              </div>

              <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-scaleIn" style={{ animationDelay: '80ms' }}>
                <div className="text-2xl font-black text-amber-500 dark:text-amber-400 mb-1 flex items-center justify-center gap-1">
                  <span>{user.rating || 4.7}</span>
                  <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                </div>
                <div className="text-xs font-semibold text-[var(--text-subtle)]">
                  تقييمات
                </div>
              </div>

              <div className="bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-scaleIn" style={{ animationDelay: '160ms' }}>
                <div className="text-2xl font-black text-[var(--foreground)] mb-1">
                  {user.reportsAgainst || 0}
                </div>
                <div className="text-xs font-semibold text-[var(--text-subtle)]">
                  بلاغات ضده
                </div>
              </div>
            </div>

            {/* Activity Log Timeline Widget */}
            <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] animate-fadeInUp" style={{ animationDelay: '100ms' }}>
              <h4 className="font-bold text-[var(--foreground)] text-base mb-6">
                سجل النشاط
              </h4>

              <div className="space-y-4 divide-y divide-[var(--divider)]">
                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                      <Calendar className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      حجز زيارة – شقة مدينة نصر
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    اليوم 9:30 ص
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      تم توثيق الهوية
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    أمس 3:00 م
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                      <MessageSquare className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      إرسال رسالة للمالك أحمد
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    أمس 2:45 م
                  </span>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-500/10 text-rose-500 dark:text-rose-400 flex items-center justify-center">
                      <Heart className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-semibold text-[var(--foreground)]">
                      حفظ عقار ستوديو التجمع
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-subtle)] font-medium">
                    الأحد 10:00 ص
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons Bar */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <button
                onClick={() => setShowWarnModal(true)}
                className="py-4 bg-amber-500 hover:bg-amber-600 active:scale-[0.98] text-white font-extrabold text-sm rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <AlertOctagon className="w-4 h-4" />
                <span>إرسال تحذير</span>
              </button>

              <button
                onClick={() => setShowSuspendModal(true)}
                className={`py-4 active:scale-[0.98] text-white font-extrabold text-sm rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer ${
                  user.status === 'موقوف' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-rose-500 hover:bg-rose-600'
                }`}
              >
                <UserX className="w-4 h-4" />
                <span>{user.status === 'موقوف' ? 'إلغاء الإيقاف' : 'إيقاف مؤقت'}</span>
              </button>

              <button
                onClick={handleExportData}
                className="py-4 bg-[var(--badge-bg-muted)] hover:bg-[var(--card-hover)] active:scale-[0.98] text-[var(--foreground)] font-extrabold text-sm rounded-2xl border border-[var(--card-border)] transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <Download className="w-4 h-4 text-[var(--text-muted)]" />
                <span>تصدير البيانات</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Warning Modal */}
      <ConfirmModal
        isOpen={showWarnModal}
        onClose={() => setShowWarnModal(false)}
        onConfirm={handleSendWarning}
        title={`إرسال تحذير إداري إلى ${user.name}`}
        message="سيتم إرسال إشعار تحذيري رسمي إلى حساب المستخدم والبريد الإلكتروني المسجل."
        variant="warning"
        confirmText="إرسال التحذير"
      />

      {/* Suspend Modal */}
      <ConfirmModal
        isOpen={showSuspendModal}
        onClose={() => setShowSuspendModal(false)}
        onConfirm={handleToggleSuspend}
        title={user.status === 'موقوف' ? `تنشيط حساب ${user.name}` : `إيقاف حساب ${user.name}`}
        message={user.status === 'موقوف' ? 'هل تريد إعادة تفعيل حساب المستخدم؟' : 'هل أنت تأكد من رغبتك في إيقاف حساب هذا المستخدم مؤقتاً؟'}
        variant={user.status === 'موقوف' ? 'success' : 'danger'}
        confirmText={user.status === 'موقوف' ? 'تنشيط' : 'إيقاف مؤقت'}
      />
    </div>
  );
}

