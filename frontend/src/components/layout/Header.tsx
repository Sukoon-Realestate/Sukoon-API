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
  lastUpdated = 'اليوم 9:41 ص',
}) => {
  return (
    <header className="h-20 bg-white border-b border-slate-200/80 px-8 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      <div>
        <h2 className="text-xl font-extrabold text-slate-800 leading-snug flex items-center gap-2">
          {title}
        </h2>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Last Updated badge */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200/60">
          <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
          <span>آخر تحديث: {lastUpdated}</span>
        </div>

        {/* Notification Bell */}
        <button className="relative w-10 h-10 rounded-full bg-slate-100 hover:bg-slate-200/80 flex items-center justify-center text-slate-600 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white"></span>
        </button>

        {/* Admin User Chip */}
        <div className="flex items-center gap-2 bg-slate-100/90 pl-3 pr-1 py-1 rounded-full border border-slate-200/80">
          <div className="w-8 h-8 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-xs shadow-xs">
            <User className="w-4 h-4" />
          </div>
          <span className="text-sm font-semibold text-slate-700 ml-1">Admin</span>
        </div>
      </div>
    </header>
  );
};
