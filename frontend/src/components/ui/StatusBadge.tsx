'use client';

import React from 'react';
import { ShieldCheck, Clock, XCircle } from 'lucide-react';

interface StatusBadgeProps {
  type: 'userType' | 'userStatus' | 'kycStatus' | 'automation' | 'role';
  value: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value }) => {
  if (type === 'userType') {
    if (value === 'مستأجر') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200/60 dark:bg-blue-500/10 dark:text-blue-300 dark:border-blue-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 dark:bg-blue-400"></span>
          {value}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200/60 dark:bg-amber-500/10 dark:text-amber-300 dark:border-amber-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 dark:bg-amber-400"></span>
        {value}
      </span>
    );
  }

  if (type === 'userStatus') {
    if (value === 'نشط') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400">
          {value}
        </span>
      );
    }
    if (value === 'قيد المراجعة') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400">
          {value}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400">
        {value}
      </span>
    );
  }

  if (type === 'kycStatus') {
    if (value === 'موثق' || value === 'موثّق') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200/60 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          {value}
        </span>
      );
    }
    if (value === 'قيد المراجعة') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-600 border border-amber-200/60 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20">
          <Clock className="w-3.5 h-3.5" />
          {value}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-600 border border-rose-200/60 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20">
        <XCircle className="w-3.5 h-3.5" />
        {value}
      </span>
    );
  }

  if (type === 'automation') {
    if (value === 'عالي') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-600 border border-rose-200 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20">
          {value}
        </span>
      );
    }
    if (value === 'تلقائي') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-600 border border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20">
          {value}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
        {value}
      </span>
    );
  }

  if (type === 'role') {
    if (value === 'مستأجر') {
      return (
        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 dark:bg-slate-500/15 dark:text-slate-300">
          {value}
        </span>
      );
    }
    if (value === 'عقار') {
      return (
        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300">
          {value}
        </span>
      );
    }
    if (value === 'مالك') {
      return (
        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-500/15 dark:text-blue-300">
          {value}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-teal-100 text-teal-800 dark:bg-teal-500/15 dark:text-teal-300">
        {value}
      </span>
    );
  }

  return <span className="px-2 py-0.5 text-xs font-medium bg-[var(--badge-bg-muted)] text-[var(--text-muted)] rounded">{value}</span>;
};
