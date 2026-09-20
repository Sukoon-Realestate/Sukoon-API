'use client';

import React from 'react';
import { Bell, User, Menu } from 'lucide-react';
import { useSidebar } from './AppLayout';

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

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      {/* User profile & Mobile Menu button (Left in RTL layout) */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleMobileMenu}
          className="lg:hidden p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Toggle Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="w-8 h-8 rounded-full bg-teal-50 flex items-center justify-center text-teal-600 border border-teal-100">
          <User className="w-4 h-4" />
        </div>
        <span className="hidden sm:inline-block px-3 py-1 bg-[#0D7C66] text-white text-xs font-bold rounded-full shadow-xs">
          Admin
        </span>
      </div>

      {/* Main title (Centered) */}
      <div className="text-center flex-1 mx-2 sm:mx-4 min-w-0">
        <h2 className="text-sm sm:text-lg font-black text-slate-800 tracking-tight truncate">
          {title}
        </h2>
        {subtitle && (
          <p className="hidden md:block text-[11px] text-slate-400 font-medium truncate">
            {subtitle}
          </p>
        )}
      </div>

      {/* Timestamp & Notification bell (Right in RTL layout) */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <span className="hidden sm:inline text-xs text-slate-400 font-semibold">
          آخر تحديث: {lastUpdated}
        </span>
        <button className="relative p-1.5 rounded-full hover:bg-slate-100 text-slate-600 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white"></span>
        </button>
      </div>
    </header>
  );
};

