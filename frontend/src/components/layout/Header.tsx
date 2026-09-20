'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Bell, User, Menu, LogOut, Settings, Shield, CheckCircle2, AlertTriangle, ExternalLink } from 'lucide-react';
import { useSidebar } from './AppLayout';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { NotificationsModal } from '@/components/ui/NotificationsModal';

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

  return (
    <header className="h-16 bg-[var(--header-bg)] border-b border-[var(--header-border)] px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30 shadow-[var(--shadow-card)] backdrop-blur-sm animate-fadeIn">
      {/* User profile & Mobile Menu button (Left in RTL layout) */}
      <div className="relative flex items-center gap-2">
        <button
          type="button"
          onClick={toggleMobileMenu}
          className="lg:hidden p-1.5 rounded-lg text-[var(--text-muted)] hover:bg-[var(--card-hover)] transition-colors cursor-pointer"
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
                className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-bold text-rose-600 hover:bg-rose-500/10 rounded-xl transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
                <span>تسجيل الخروج</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main title (Centered) */}
      <div className="text-center flex-1 mx-2 sm:mx-4 min-w-0 flex flex-col items-center">
        <h2 className="text-sm sm:text-base font-black text-[var(--foreground)] tracking-tight truncate flex items-center justify-center gap-2">
          <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
          <span>{title}</span>
        </h2>
        {subtitle && (
          <p className="hidden md:block text-[11px] text-[var(--text-muted)] font-bold truncate">
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
              setShowNotifications(true);
              setShowProfileMenu(false);
            }}
            className="relative p-2 rounded-xl hover:bg-[var(--card-hover)] text-[var(--text-muted)] transition-colors cursor-pointer border border-[var(--card-border)] bg-[var(--card-bg)] shadow-xs"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5 text-[var(--foreground)]" />
            <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-rose-500 ring-2 ring-[var(--header-bg)] animate-pulseDot"></span>
          </button>

          {/* Interactive Rich Notifications Modal */}
          <NotificationsModal
            isOpen={showNotifications}
            onClose={() => setShowNotifications(false)}
          />
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

