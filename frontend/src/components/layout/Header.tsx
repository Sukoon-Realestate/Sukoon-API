'use client';

import React from 'react';
import { Bell, User, RefreshCw } from 'lucide-react';

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
  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-8 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      {/* User profile info (Left in RTL layout) */}
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-teal-50 flex items-center justify-center text-teal-600 border border-teal-100">
          <User className="w-4 h-4" />
        </div>
        <span className="px-3 py-1 bg-[#0D7C66] text-white text-xs font-bold rounded-full shadow-xs">
          Admin
        </span>
      </div>

      {/* Main title (Centered) */}
      <div className="text-center flex-1 mx-4">
        <h2 className="text-lg font-black text-slate-800 tracking-tight">
          {title}
        </h2>
        {subtitle && <p className="text-[11px] text-slate-400 font-medium">{subtitle}</p>}
      </div>

      {/* Timestamp & Notification bell (Right in RTL layout) */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-400 font-semibold">
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

