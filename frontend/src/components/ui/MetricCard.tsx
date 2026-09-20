import React from 'react';
import Link from 'next/link';
import { Users, Building2, Clock, TrendingUp, TrendingDown, Calendar, AlertTriangle, ArrowUpRight, ArrowDownRight } from 'lucide-react';
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
        return <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />;
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
        return 'bg-blue-500/10 border-blue-200/60 dark:border-blue-500/30 text-blue-600 glow-blue-sm';
      case 'building':
        return 'bg-teal-500/10 border-teal-200/60 dark:border-teal-500/30 text-teal-600 glow-teal-sm';
      case 'clock':
        return 'bg-amber-500/10 border-amber-200/60 dark:border-amber-500/30 text-amber-600 glow-amber-sm';
      case 'revenue':
        return 'bg-emerald-500/10 border-emerald-200/60 dark:border-emerald-500/30 text-emerald-600 glow-teal-sm';
      case 'calendar':
        return 'bg-cyan-500/10 border-cyan-200/60 dark:border-cyan-500/30 text-cyan-600 glow-blue-sm';
      case 'alert':
        return 'bg-rose-500/10 border-rose-200/60 dark:border-rose-500/30 text-rose-600 glow-rose-sm';
      default:
        return 'bg-teal-500/10 border-teal-200/60 dark:border-teal-500/30 text-teal-600';
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
      className="group relative block bg-[var(--card-bg)] rounded-2xl p-5 border border-[var(--card-border)] shadow-[var(--shadow-card)] hover-lift btn-press animate-scaleIn transition-all hover:border-teal-500/60 cursor-pointer overflow-hidden"
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Top accent glowing bar */}
      <div className="absolute top-0 right-0 left-0 h-1 bg-gradient-to-r from-teal-500 via-cyan-500 to-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div className="flex items-center justify-between mb-3.5">
        <div className={`w-11 h-11 rounded-2xl border flex items-center justify-center transition-transform group-hover:scale-110 ${getIconBg()}`}>
          {getIcon()}
        </div>

        <span
          className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full dir-ltr ${
            metric.isPositive
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30'
              : 'bg-rose-50 text-rose-700 border border-rose-200/80 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30'
          }`}
        >
          {metric.isPositive ? (
            <ArrowUpRight className="w-3.5 h-3.5 shrink-0" />
          ) : (
            <ArrowDownRight className="w-3.5 h-3.5 shrink-0" />
          )}
          <span>{metric.change}</span>
        </span>
      </div>

      <div>
        <div className="text-2xl sm:text-3xl font-black text-[var(--foreground)] tracking-tight leading-tight mb-1">
          {metric.value}
        </div>
        <div className="text-xs font-semibold text-[var(--text-muted)] group-hover:text-[var(--foreground)] transition-colors">
          {metric.title}
        </div>
      </div>
    </Link>
  );
};

