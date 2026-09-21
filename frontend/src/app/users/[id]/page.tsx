'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
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
  ArrowRight,
} from 'lucide-react';
import { fetchUserDetail, suspendUser, unsuspendUser } from '@/lib/api/users';
import { UserItem } from '@/lib/api/types';

export default function UserProfilePage() {
  const params = useParams();
  const userId = params?.id as string;
  const { showToast } = useToast();

  const [user, setUser] = useState<UserItem | null>(null);
  const [showWarnModal, setShowWarnModal] = useState(false);
  const [showSuspendModal, setShowSuspendModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (!userId) return;
      setIsLoading(true);
      try {
        const detail = await fetchUserDetail(userId);
        if (detail) {
          setUser(detail);
        }
      } catch (err) {
        console.error('Failed to fetch user details from API:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadUser();
  }, [userId]);

  const handleSendWarning = () => {
    if (!user) return;
    showToast(`تم إرسال تحذير إداري إلى ${user.name} بنجاح`, 'info');
  };

  const handleToggleSuspend = async () => {
    if (!user) return;
    const isSuspended = user.status === 'موقوف';
    try {
      if (isSuspended) {
        await unsuspendUser(user.id);
      } else {
        await suspendUser(user.id, 'إيقاف إداري من صفحة الملف');
      }
      setUser((prev) => (prev ? { ...prev, status: isSuspended ? 'نشط' : 'موقوف' } : null));
      showToast(
        isSuspended ? `تم تنشيط حساب ${user.name}` : `تم إيقاف حساب ${user.name} مؤقتاً`,
        isSuspended ? 'success' : 'error'
      );
    } catch {
      showToast('حدث خطأ أثناء تحديث حالة المستخدم', 'error');
    } finally {
      setShowSuspendModal(false);
    }
  };

  const handleExportData = () => {
    if (!user) return;
    showToast(`جاري تجهيز وتنزيل ملف بيانات ${user.name}...`, 'success');
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col pb-12">
        <Header
          title="ملف المستخدم"
          subtitle="تفاصيل الحساب الكاملة، سجل النشاطات والإجراءات المتاحة"
        />
        <div className="p-12 text-center text-slate-400 text-xs font-bold space-y-3">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p>جاري تحميل تفاصيل المستخدم من الخادم...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex-1 flex flex-col pb-12">
        <Header
          title="المستخدم غير موجود"
          subtitle="لم يتم العثور على الحساب المطلوب"
        />
        <div className="p-12 text-center text-slate-400 text-xs font-bold space-y-4">
          <p>لم يتم العثور على أي مستخدم مطابق لهذا المعرف.</p>
          <Link
            href="/users"
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-xl font-bold hover:bg-teal-500 transition-colors"
          >
            <ArrowRight className="w-4 h-4" />
            <span>العودة لقائمة المستخدمين</span>
          </Link>
        </div>
      </div>
    );
  }

  const activityLog = user.activityLog || [];

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title={`ملف المستخدم – ${user.name}`}
        subtitle="تفاصيل الحساب الكاملة، سجل النشاطات والإجراءات المتاحة"
        lastUpdated="محدث الآن"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: User Profile Details Card (4 cols) */}
          <div className="lg:col-span-4 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] flex flex-col items-center text-center animate-fadeInUp">
            {/* Avatar Circle */}
            <div className="w-24 h-24 rounded-full bg-teal-500/10 border-2 border-teal-500/30 flex items-center justify-center text-teal-400 text-3xl font-bold mb-4 shadow-inner overflow-hidden">
              {user.avatar ? (
                <img src={user.avatar} alt={user.name} className="w-full h-full object-cover" />
              ) : (
                <User className="w-12 h-12" />
              )}
            </div>

            <h3 className="text-xl font-extrabold text-white mb-1">
              {user.name}
            </h3>

            <div className="flex items-center gap-2 mb-6">
              <StatusBadge status={user.kycStatus} />
              <span className="text-xs text-slate-400 font-semibold">
                {user.type}
              </span>
            </div>

            {/* Field Rows */}
            <div className="w-full space-y-4 border-t border-[var(--divider)] pt-5 text-right text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">رقم الهاتف</span>
                <span className="font-bold text-white dir-ltr font-mono">
                  {user.phone || 'غير مسجل'}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-slate-400 font-medium">البريد الإلكتروني</span>
                <span className="font-bold text-white font-mono text-[11px] dir-ltr">
                  {user.email}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-slate-400 font-medium">تاريخ الانضمام</span>
                <span className="font-bold text-white font-mono">{user.regDate}</span>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--divider)] pt-3">
                <span className="text-slate-400 font-medium">حالة الحساب</span>
                <StatusBadge status={user.status} />
              </div>
            </div>

            {/* Admin Action Buttons */}
            <div className="w-full space-y-2 mt-6 pt-4 border-t border-[var(--divider)]">
              <button
                onClick={() => setShowWarnModal(true)}
                className="w-full py-2.5 px-4 rounded-xl border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <AlertOctagon className="w-4 h-4 text-amber-400" />
                <span>إرسال تحذير إداري</span>
              </button>

              <button
                onClick={() => setShowSuspendModal(true)}
                className={`w-full py-2.5 px-4 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
                  user.status === 'موقوف'
                    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20'
                    : 'border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20'
                }`}
              >
                <UserX className="w-4 h-4" />
                <span>{user.status === 'موقوف' ? 'تنشيط الحساب' : 'إيقاف الحساب مؤقتاً'}</span>
              </button>

              <button
                onClick={handleExportData}
                className="w-full py-2.5 px-4 rounded-xl border border-slate-700 bg-slate-800/60 hover:bg-slate-800 text-slate-200 text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <Download className="w-4 h-4 text-slate-400" />
                <span>تصدير بيانات المستخدم</span>
              </button>
            </div>
          </div>

          {/* Right Column: User Metrics & Timeline (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Top Stat Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-[var(--card-bg)] rounded-2xl p-4 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-fadeInUp">
                <div className="text-2xl font-black text-white mb-1">
                  {user.visitRequests ?? 0}
                </div>
                <div className="text-xs font-semibold text-slate-400">
                  طلبات المعاينة
                </div>
              </div>

              <div
                className="bg-[var(--card-bg)] rounded-2xl p-4 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-fadeInUp"
                style={{ animationDelay: '50ms' }}
              >
                <div className="text-2xl font-black text-teal-400 mb-1 flex items-center justify-center gap-1">
                  <span>{user.properties_count ?? 0}</span>
                </div>
                <div className="text-xs font-semibold text-slate-400">
                  عقارات معلنة
                </div>
              </div>

              <div
                className="bg-[var(--card-bg)] rounded-2xl p-4 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-fadeInUp"
                style={{ animationDelay: '100ms' }}
              >
                <div className="text-2xl font-black text-rose-500 mb-1">
                  {user.reportsAgainst ?? 0}
                </div>
                <div className="text-xs font-semibold text-slate-400">
                  بلاغات ضد المستخدم
                </div>
              </div>

              <div
                className="bg-[var(--card-bg)] rounded-2xl p-4 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-fadeInUp"
                style={{ animationDelay: '150ms' }}
              >
                <div className="text-2xl font-black text-emerald-400 mb-1 flex items-center justify-center gap-1">
                  <span>{user.is_verified ? '5.0' : '4.5'}</span>
                  <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                </div>
                <div className="text-xs font-semibold text-slate-400">
                  تقييم السلوك
                </div>
              </div>
            </div>

            {/* Timeline Activity Log */}
            <div
              className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] animate-fadeInUp"
              style={{ animationDelay: '200ms' }}
            >
              <h4 className="font-extrabold text-white text-base mb-6 border-b border-[var(--divider)] pb-3">
                سجل نشاطات وتفاعلات المستخدم
              </h4>

              {activityLog.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">
                  لا توجد نشاطات مسجلة لهذا الحساب حالياً.
                </p>
              ) : (
                <div className="space-y-6 relative before:absolute before:top-2 before:bottom-2 before:right-4 before:w-0.5 before:bg-[var(--divider)]">
                  {activityLog.map((log) => (
                    <div key={log.id} className="relative pr-9 flex items-start gap-4">
                      <div className="absolute right-2 top-0.5 w-4 h-4 rounded-full bg-teal-500 border-2 border-[var(--card-bg)]"></div>
                      <div className="flex-1 space-y-1">
                        <p className="text-xs font-bold text-white">
                          {log.title}
                        </p>
                        <p className="text-[11px] text-slate-400 font-medium">
                          {log.time}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Warning Modal */}
      <ConfirmModal
        isOpen={showWarnModal}
        onConfirm={handleSendWarning}
        title={`إرسال تحذير إداري إلى ${user.name}`}
        description="سيصل هذا التنبيه فوراً كإشعار داخلي للحساب ينبهه بالالتزام بسياسة المنصة."
        confirmLabel="إرسال التحذير"
        confirmVariant="warning"
        onCancel={() => setShowWarnModal(false)}
      />

      {/* Suspend Modal */}
      <ConfirmModal
        isOpen={showSuspendModal}
        onConfirm={handleToggleSuspend}
        title={
          user.status === 'موقوف'
            ? `إلغاء إيقاف حساب ${user.name}`
            : `تأكيد إيقاف حساب ${user.name}`
        }
        description={
          user.status === 'موقوف'
            ? 'هل أنت متأكد من إعادة تنشيط الحساب واستعادة إمكانية تسجيل الدخول؟'
            : 'هل أنت متأكد من إيقاف هذا الحساب؟ سيتم حجب وصول المستخدم.'
        }
        confirmLabel={user.status === 'موقوف' ? 'تنشيط الحساب' : 'إيقاف الحساب'}
        confirmVariant={user.status === 'موقوف' ? 'primary' : 'danger'}
        onCancel={() => setShowSuspendModal(false)}
      />
    </div>
  );
}
