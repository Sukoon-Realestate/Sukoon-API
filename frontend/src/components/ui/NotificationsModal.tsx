'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Bell,
  X,
  CheckCheck,
  Building2,
  UserCheck,
  AlertTriangle,
  ShieldAlert,
  Info,
  ExternalLink,
  Trash2,
} from 'lucide-react';
import { useToast } from './Toast';

export interface NotificationItem {
  id: string;
  title: string;
  body: string;
  time: string;
  category: 'kyc' | 'property' | 'alert' | 'system';
  isRead: boolean;
  link?: string;
}

interface NotificationsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationsModal: React.FC<NotificationsModalProps> = ({ isOpen, onClose }) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'all' | 'unread' | 'kyc' | 'property'>('all');

  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: 'notif-1',
      title: 'طلب توثيق جديد من سارة أحمد',
      body: 'قام المستخدم بتمحيص بطاقته القومية وصورة السيلفي وهو بانتظار الاعتماد.',
      time: 'منذ 5 دقائق',
      category: 'kyc',
      isRead: false,
      link: '/kyc/review',
    },
    {
      id: 'notif-2',
      title: 'بلاغ خطر عالي على عقار شقة مدينة نصر',
      body: 'تم اكتشاف رقم هاتف ظاهري في الصور المرفوعة 010****432.',
      time: 'منذ 15 دقيقة',
      category: 'alert',
      isRead: false,
      link: '/properties/review',
    },
    {
      id: 'notif-3',
      title: 'عقار جديد بانتظار المراجعة (ستوديو التجمع)',
      body: 'قام نادر طارق بإدراج عقار جديد بسعر 8,500 ج.',
      time: 'منذ 35 دقيقة',
      category: 'property',
      isRead: false,
      link: '/properties/review',
    },
    {
      id: 'notif-4',
      title: 'تم تسجيل مستخدم جديد كمستأجر',
      body: 'انضم محمد علي إلى منصة سكون وتم تحويل حسابه لطابور التوثيق.',
      time: 'منذ ساعة',
      category: 'kyc',
      isRead: true,
      link: '/users/sara-ahmed',
    },
    {
      id: 'notif-5',
      title: 'تحديث أمان وحظر حاسم',
      body: 'تم إيقاف حساب طارق محمد بسبب تكرار لغة غير مسيئة.',
      time: 'منذ ساعتين',
      category: 'system',
      isRead: true,
      link: '/users/suspended',
    },
  ]);

  if (!isOpen) return null;

  const filteredNotifications = notifications.filter((n) => {
    if (activeTab === 'unread') return !n.isRead;
    if (activeTab === 'kyc') return n.category === 'kyc';
    if (activeTab === 'property') return n.category === 'property';
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  const handleMarkAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
    showToast('تم تحديد جميع التنبيهات كمقروءة', 'success');
  };

  const handleClearAll = () => {
    setNotifications([]);
    showToast('تم مسح جميع التنبيهات', 'info');
  };

  const handleToggleRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: !n.isRead } : n))
    );
  };

  const getCategoryIcon = (category: NotificationItem['category']) => {
    switch (category) {
      case 'kyc':
        return <UserCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />;
      case 'property':
        return <Building2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />;
      case 'alert':
        return <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400" />;
      default:
        return <ShieldAlert className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />;
    }
  };

  const getCategoryBg = (category: NotificationItem['category']) => {
    switch (category) {
      case 'kyc':
        return 'bg-emerald-50 dark:bg-emerald-500/15 border-emerald-200/60 dark:border-emerald-500/30';
      case 'property':
        return 'bg-teal-50 dark:bg-teal-500/15 border-teal-200/60 dark:border-teal-500/30';
      case 'alert':
        return 'bg-rose-50 dark:bg-rose-500/15 border-rose-200/60 dark:border-rose-500/30';
      default:
        return 'bg-cyan-50 dark:bg-cyan-500/15 border-cyan-200/60 dark:border-cyan-500/30';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end p-2 sm:p-4 bg-black/50 backdrop-blur-xs animate-fadeIn">
      <div
        className="w-full max-w-md bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-2xl flex flex-col max-h-[85vh] animate-scaleIn text-right overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-4 border-b border-[var(--divider)] flex items-center justify-between bg-[var(--header-bg)]">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-teal-50 dark:bg-teal-500/15 text-teal-600 dark:text-teal-400 border border-teal-200/60 dark:border-teal-500/30 flex items-center justify-center">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-black text-base text-[var(--foreground)] leading-tight">
                مركز التنبيهات الإدارية
              </h3>
              <p className="text-[11px] text-[var(--text-muted)] font-medium">
                {unreadCount > 0 ? `لديك ${unreadCount} تنبيهات جديدة لم تقرأ` : 'جميع التنبيهات مقروءة'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-[var(--text-muted)] hover:bg-[var(--card-hover)] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action Controls & Filter Tabs */}
        <div className="px-4 pt-3 pb-2 border-b border-[var(--divider)] bg-[var(--card-hover)]/40 flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            {/* Filter Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-bold">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-3 py-1 rounded-full transition-colors cursor-pointer ${
                  activeTab === 'all'
                    ? 'bg-teal-700 text-white shadow-xs'
                    : 'text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                الكل ({notifications.length})
              </button>
              <button
                onClick={() => setActiveTab('unread')}
                className={`px-3 py-1 rounded-full transition-colors cursor-pointer ${
                  activeTab === 'unread'
                    ? 'bg-teal-700 text-white shadow-xs'
                    : 'text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                غير مقروءة ({unreadCount})
              </button>
              <button
                onClick={() => setActiveTab('kyc')}
                className={`px-3 py-1 rounded-full transition-colors cursor-pointer ${
                  activeTab === 'kyc'
                    ? 'bg-teal-700 text-white shadow-xs'
                    : 'text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                KYC
              </button>
              <button
                onClick={() => setActiveTab('property')}
                className={`px-3 py-1 rounded-full transition-colors cursor-pointer ${
                  activeTab === 'property'
                    ? 'bg-teal-700 text-white shadow-xs'
                    : 'text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                عقارات
              </button>
            </div>
          </div>

          {/* Quick Actions Bar */}
          <div className="flex items-center justify-between text-[11px] font-bold text-[var(--text-muted)] pt-1 border-t border-[var(--divider)]">
            <button
              onClick={handleMarkAllAsRead}
              className="flex items-center gap-1 text-teal-600 dark:text-teal-400 hover:underline cursor-pointer"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              <span>تحديد الكل كمقروء</span>
            </button>

            {notifications.length > 0 && (
              <button
                onClick={handleClearAll}
                className="flex items-center gap-1 text-rose-500 hover:underline cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>مسح الكل</span>
              </button>
            )}
          </div>
        </div>

        {/* Notifications List Body */}
        <div className="flex-1 overflow-y-auto divide-y divide-[var(--divider)] p-2">
          {filteredNotifications.length > 0 ? (
            filteredNotifications.map((item) => (
              <div
                key={item.id}
                onClick={() => handleToggleRead(item.id)}
                className={`p-3.5 rounded-xl transition-all flex items-start gap-3 cursor-pointer group ${
                  !item.isRead
                    ? 'bg-teal-50/50 dark:bg-teal-500/10 border border-teal-200/50 dark:border-teal-500/20'
                    : 'hover:bg-[var(--card-hover)]'
                }`}
              >
                <div
                  className={`w-9 h-9 rounded-xl border flex items-center justify-center shrink-0 mt-0.5 ${getCategoryBg(
                    item.category
                  )}`}
                >
                  {getCategoryIcon(item.category)}
                </div>

                <div className="flex-1 space-y-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="font-bold text-xs text-[var(--foreground)] leading-tight truncate">
                      {item.title}
                    </h4>
                    <span className="text-[10px] text-[var(--text-muted)] font-semibold shrink-0">
                      {item.time}
                    </span>
                  </div>

                  <p className="text-xs text-[var(--text-muted)] leading-relaxed line-clamp-2">
                    {item.body}
                  </p>

                  {item.link && (
                    <div className="pt-1.5 flex items-center justify-between">
                      <Link
                        href={item.link}
                        onClick={onClose}
                        className="inline-flex items-center gap-1 text-[11px] font-bold text-teal-600 dark:text-teal-400 hover:underline"
                      >
                        <span>متابعة الإجراء</span>
                        <ExternalLink className="w-3 h-3" />
                      </Link>

                      {!item.isRead && (
                        <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-xs text-[var(--text-muted)] font-medium">
              لا توجد تنبيهات حالية في هذه الفئة.
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-3 bg-[var(--card-hover)] border-t border-[var(--divider)] text-center text-xs">
          <Link
            href="/notifications"
            onClick={onClose}
            className="font-bold text-teal-600 dark:text-teal-400 hover:underline flex items-center justify-center gap-1.5"
          >
            <span>فتح صفحة جميع حملات الإشعارات</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
};
