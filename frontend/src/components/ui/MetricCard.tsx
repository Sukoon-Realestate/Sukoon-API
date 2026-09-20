'use client';

import React from 'react';
import Link from 'next/link';
import { Users, Building2, Clock, TrendingUp, Calendar, AlertTriangle } from 'lucide-react';
import { DashboardMetric } from '@/data/mockData';

interface MetricCardProps {
  metric: DashboardMetric;
  delay?: number;
  href?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ metric, delay = 0, href }) => {
  const getIcon = () => {
    switch (metric.icon) {
      case 'users':
        return <Users className="w-5 h-5 text-blue-500 dark:text-blue-400" />;
      case 'building':
        return <Building2 className="w-5 h-5 text-teal-600 dark:text-teal-400" />;
      case 'clock':
        return <Clock className="w-5 h-5 text-amber-600 dark:text-amber-400" />;
      case 'revenue':
        return <TrendingUp className="w-5 h-5 text-teal-600 dark:text-teal-400" />;
      case 'calendar':
        return <Calendar className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />;
      case 'alert':
        return <AlertTriangle className="w-5 h-5 text-rose-600 dark:text-rose-400" />;
      default:
        return <Users className="w-5 h-5 text-teal-600 dark:text-teal-400" />;
    }
  };

  const getIconBg = () => {
    switch (metric.icon) {
      case 'users':
        return 'bg-blue-50 border-blue-100 dark:bg-blue-500/10 dark:border-blue-500/20';
      case 'building':
        return 'bg-teal-50 border-teal-100 dark:bg-teal-500/10 dark:border-teal-500/20';
      case 'clock':
        return 'bg-amber-50 border-amber-100 dark:bg-amber-500/10 dark:border-amber-500/20';
      case 'revenue':
        return 'bg-teal-50 border-teal-100 dark:bg-teal-500/10 dark:border-teal-500/20';
      case 'calendar':
        return 'bg-cyan-50 border-cyan-100 dark:bg-cyan-500/10 dark:border-cyan-500/20';
      case 'alert':
        return 'bg-rose-50 border-rose-100 dark:bg-rose-500/10 dark:border-rose-500/20';
      default:
        return 'bg-slate-50 border-slate-100 dark:bg-slate-500/10 dark:border-slate-500/20';
    }
  };

  const getDefaultHref = () => {
    if (href) return href;
    switch (metric.icon) {
      case 'users':
        return '/users';
      case 'building':
        return '/properties';
      case 'clock':
        return '/kyc';
      case 'revenue':
        return '/financials';
      case 'calendar':
        return '/analytics';
      case 'alert':
        return '/users/reports';
      default:
        return '/';
    }
  };

  return (
    <Link
      href={getDefaultHref()}
      className="block bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] hover-lift animate-scaleIn transition-all hover:border-teal-500/50 cursor-pointer"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${getIconBg()}`}>
          {getIcon()}
        </div>

        <span
          className={`text-xs font-bold px-2.5 py-1 rounded-full dir-ltr ${
            metric.isPositive
              ? 'bg-emerald-50 text-emerald-600 border border-emerald-200/60 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20'
              : 'bg-rose-50 text-rose-600 border border-rose-200/60 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20'
          }`}
        >
          {metric.change}
        </span>
      </div>

      <div>
        <div className="text-2xl font-black text-[var(--foreground)] leading-tight mb-1">
          {metric.value}
        </div>
        <div className="text-xs font-medium text-[var(--text-muted)]">{metric.title}</div>
      </div>
    </Link>
  );
};

