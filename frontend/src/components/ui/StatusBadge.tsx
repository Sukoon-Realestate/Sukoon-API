import React from 'react';
import { ShieldCheck, Clock, XCircle, CheckCircle2, AlertTriangle, User, Building2, ShieldAlert } from 'lucide-react';

interface StatusBadgeProps {
  type?: 'userType' | 'userStatus' | 'kycStatus' | 'automation' | 'role';
  value?: string;
  status?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value, status }) => {
  const val = value || status || '';
  let resolvedType = type;

  if (!resolvedType) {
    if (val === 'مستأجر' || val === 'مالك') resolvedType = 'userType';
    else if (val === 'نشط' || val === 'موقوف' || val === 'محظور') resolvedType = 'userStatus';
    else if (val === 'موثق' || val === 'موثّق' || val === 'انتظار المراجعة' || val === 'approved' || val === 'rejected' || val === 'pending') resolvedType = 'kycStatus';
    else resolvedType = 'userStatus';
  }

  if (resolvedType === 'userType') {
    if (val === 'مستأجر') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200/80 dark:bg-blue-500/15 dark:text-blue-300 dark:border-blue-500/30">
          <User className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
          {val}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200/80 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30">
        <Building2 className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
        {val}
      </span>
    );
  }

  if (resolvedType === 'userStatus') {
    if (val === 'نشط') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          {val}
        </span>
      );
    }
    if (val === 'قيد المراجعة') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200/80 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30">
          <Clock className="w-3.5 h-3.5" />
          {val}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200/80 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30">
        <XCircle className="w-3.5 h-3.5" />
        {val}
      </span>
    );
  }

  if (resolvedType === 'kycStatus') {
    if (val === 'موثق' || val === 'موثّق' || val === 'approved') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          {val === 'approved' ? 'مقبول' : val}
        </span>
      );
    }
    if (val === 'قيد المراجعة' || val === 'انتظار المراجعة' || val === 'pending') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200/80 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30">
          <Clock className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
          {val === 'pending' ? 'انتظار المراجعة' : val}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200/80 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30">
        <ShieldAlert className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
        {val === 'rejected' ? 'مرفوض' : val}
      </span>
    );
  }

  if (resolvedType === 'automation') {
    if (val === 'عالي') {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200/80 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30">
          <AlertTriangle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
          {val}
        </span>
      );
    }
    if (val === 'تلقائي') {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200/80 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30">
          <Clock className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
          {val}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
        {val}
      </span>
    );
  }

  if (resolvedType === 'role') {
    return <span className="inline-flex px-2 py-1 rounded-md text-xs font-medium bg-[var(--badge-bg-muted)] text-[var(--text-muted)] border border-[var(--card-border)]">{val}</span>;
  }

  return <span className="px-2.5 py-1 text-xs font-bold bg-[var(--badge-bg-muted)] text-[var(--text-muted)] border border-[var(--card-border)] rounded-lg">{val}</span>;
};
