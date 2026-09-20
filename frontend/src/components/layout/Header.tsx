'use client';

import React from 'react';
import { Bell, User, Menu, LogOut } from 'lucide-react';
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

  return (
    <header className="h-16 bg-[var(--header-bg)] border-b border-[var(--header-border)] px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30 shadow-[var(--shadow-card)] backdrop-blur-sm animate-fadeIn">
      {/* User profile & Mobile Menu button (Left in RTL layout) */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleMobileMenu}
          className="lg:hidden p-1.5 rounded-lg text-[var(--text-muted)] hover:bg-[var(--card-hover)] transition-colors"
          aria-label="Toggle Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="w-8 h-8 rounded-full bg-[var(--primary-subtle)] flex items-center justify-center text-[var(--primary)] border border-[var(--primary)]/20">
          <User className="w-4 h-4" />
        </div>
        <span className="hidden sm:inline-block px-3 py-1 bg-[var(--primary)] text-white text-xs font-bold rounded-full shadow-xs">
          Admin
        </span>
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
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <span className="hidden sm:inline text-xs text-[var(--text-subtle)] font-semibold">
          آخر تحديث: {lastUpdated}
        </span>
        <button className="relative p-1.5 rounded-full hover:bg-[var(--card-hover)] text-[var(--text-muted)] transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-[var(--header-bg)] animate-pulseDot"></span>
        </button>
        <ThemeToggle />
        <button
          type="button"
          onClick={logout}
          title="تسجيل الخروج"
          className="p-1.5 rounded-full text-[var(--text-subtle)] hover:text-rose-500 hover:bg-rose-500/10 transition-colors"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};
