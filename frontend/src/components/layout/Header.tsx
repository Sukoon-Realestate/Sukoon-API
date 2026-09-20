'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Bell, User, Menu, LogOut, Settings, Shield, CheckCircle2, AlertTriangle, ExternalLink } from 'lucide-react';
import { useSidebar } from './AppLayout';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '@/components/ui/ThemeToggle';

interface HeaderProps {
  title: string;
  subtitle?: string;
  lastUpdated?: string;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  lastUpdated = '9:41 ص',
}) => {
  const { toggleMobileMenu } = useSidebar();
  const { logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const notifications = [
    { id: 1, title: 'طلب توثيق جديد من سارة أحمد', time: 'منذ 5 دقائق', icon: CheckCircle2, type: 'kyc' },
    { id: 2, title: 'بلاغ جديد على عقار شقة مدينة نصر', time: 'منذ 12 دقيقة', icon: AlertTriangle, type: 'alert' },
    { id: 3, title: 'عقار جديد بانتظار المراجعة (ستوديو التجمع)', time: 'منذ 25 دقيقة', icon: CheckCircle2, type: 'prop' },
  ];

  return (
    <header className="h-16 bg-[var(--header-bg)] border-b border-[var(--header-border)] px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30 shadow-[var(--shadow-card)] backdrop-blur-sm animate-fadeIn">
      {/* User profile & Mobile Menu button (Left in RTL layout) */}
      <div className="relative flex items-center gap-2">
        <button
          type="button"
          onClick={toggleMobileMenu}
          className="lg:hidden p-1.5 rounded-lg text-[var(--text-muted)] hover:bg-[var(--card-hover)] transition-colors"
          aria-label="Toggle Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <button
          onClick={() => {
            setShowProfileMenu(!showProfileMenu);
            setShowNotifications(false);
          }}
          className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer group text-right"
        >
          <div className="w-8 h-8 rounded-full bg-[var(--primary-subtle)] flex items-center justify-center text-[var(--primary)] border border-[var(--primary)]/20 group-hover:scale-105 transition-transform">
            <User className="w-4 h-4" />
          </div>
          <span className="hidden sm:inline-block px-3 py-1 bg-[var(--primary)] text-white text-xs font-bold rounded-full shadow-xs">
            Admin
          </span>
        </button>

        {/* Profile Dropdown Menu */}
        {showProfileMenu && (
          <div className="absolute top-12 right-0 w-56 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-xl p-2 z-50 animate-fadeInUp">
            <div className="p-3 border-b border-[var(--divider)] mb-1">
              <p className="font-extrabold text-sm text-[var(--foreground)]">أحمد العدل</p>
              <p className="text-xs text-[var(--text-subtle)] font-medium">مشرف رئيسي (System Admin)</p>
            </div>
            <Link
              href="/settings"
              onClick={() => setShowProfileMenu(false)}
              className="flex items-center gap-2.5 px-3 py-2 text-xs font-bold text-[var(--foreground)] hover:bg-[var(--card-hover)] rounded-xl transition-colors"
            >
              <Settings className="w-4 h-4 text-teal-600" />
              <span>إعدادات الحساب والنظام</span>
            </Link>
            <Link
              href="/roles"
              onClick={() => setShowProfileMenu(false)}
              className="flex items-center gap-2.5 px-3 py-2 text-xs font-bold text-[var(--foreground)] hover:bg-[var(--card-hover)] rounded-xl transition-colors"
            >
              <Shield className="w-4 h-4 text-teal-600" />
              <span>إدارة الأدوار والصلاحيات</span>
            </Link>
            <div className="border-t border-[var(--divider)] mt-1 pt-1">
              <button
                onClick={logout}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-bold text-rose-600 hover:bg-rose-500/10 rounded-xl transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>تسجيل الخروج</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main title (Centered) */}
      <div className="text-center flex-1 mx-2 sm:mx-4 min-w-0">
        <h2 className="text-sm sm:text-lg font-black text-[var(--foreground)] tracking-tight truncate">
          {title}
        </h2>
        {subtitle && (
          <p className="hidden md:block text-[11px] text-[var(--text-subtle)] font-medium truncate">
            {subtitle}
          </p>
        )}
      </div>

      {/* Timestamp & Notification bell & Theme toggle & Logout (Right in RTL layout) */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0 relative">
        <span className="hidden sm:inline text-xs text-[var(--text-subtle)] font-semibold">
          آخر تحديث: {lastUpdated}
        </span>

        {/* Bell Button */}
        <div className="relative">
          <button
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowProfileMenu(false);
            }}
            className="relative p-1.5 rounded-full hover:bg-[var(--card-hover)] text-[var(--text-muted)] transition-colors cursor-pointer"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-[var(--header-bg)] animate-pulseDot"></span>
          </button>

          {/* Notifications Dropdown Panel */}
          {showNotifications && (
            <div className="absolute top-12 left-0 sm:-left-12 w-80 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-xl p-4 z-50 animate-fadeInUp">
              <div className="flex items-center justify-between border-b border-[var(--divider)] pb-3 mb-3">
                <h4 className="font-extrabold text-sm text-[var(--foreground)]">التنبيهات الإدارية</h4>
                <span className="text-[10px] font-extrabold bg-teal-500/10 text-teal-600 px-2 py-0.5 rounded-full">
                  3 جديدة
                </span>
              </div>

              <div className="space-y-2 mb-3">
                {notifications.map((item) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.id}
                      className="p-2.5 rounded-xl bg-[var(--card-hover)]/60 hover:bg-[var(--card-hover)] transition-colors text-right flex items-start gap-2.5"
                    >
                      <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${item.type === 'alert' ? 'text-rose-500' : 'text-teal-500'}`} />
                      <div>
                        <p className="text-xs font-bold text-[var(--foreground)] leading-snug">{item.title}</p>
                        <p className="text-[10px] text-[var(--text-subtle)] font-medium mt-0.5">{item.time}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              <Link
                href="/notifications"
                onClick={() => setShowNotifications(false)}
                className="w-full py-2 bg-[var(--primary)] hover:opacity-90 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 transition-opacity"
              >
                <span>عرض جميع الإشعارات</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}
        </div>

        <ThemeToggle />

        <button
          type="button"
          onClick={logout}
          title="تسجيل الخروج"
          className="p-1.5 rounded-full text-[var(--text-subtle)] hover:text-rose-500 hover:bg-rose-500/10 transition-colors cursor-pointer"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};

