import React from 'react';
import Link from '@/components/ui/AdminLink';
import { Users, Building2, Clock, TrendingUp, Calendar, AlertTriangle, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { DashboardMetric } from '@/lib/api/types';

interface MetricCardProps {
  metric: DashboardMetric;
  delay?: number;
  href?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ metric, delay = 0, href }) => {
  const getIcon = () => {
    switch (metric.icon) {
      case 'users':
        return <Users className="w-5 h-5 text-[var(--primary-text)]" />;
      case 'building':
        return <Building2 className="w-5 h-5 text-[var(--primary-text)]" />;
      case 'clock':
        return <Clock className="w-5 h-5 text-[var(--primary-text)]" />;
      case 'revenue':
        return <TrendingUp className="w-5 h-5 text-[var(--primary-text)]" />;
      case 'calendar':
        return <Calendar className="w-5 h-5 text-[var(--primary-text)]" />;
      case 'alert':
        return <AlertTriangle className="w-5 h-5 text-[var(--primary-text)]" />;
      default:
        return <Users className="w-5 h-5 text-[var(--primary-text)]" />;
    }
  };

  const getIconBg = () => 'bg-[var(--primary-subtle)] border-[var(--card-border)]';

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
      className="group relative block bg-[var(--card-bg)] rounded-3xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] hover-lift btn-press animate-scaleIn transition-all hover:border-teal-500/70 hover:shadow-[var(--shadow-card-hover)] cursor-pointer overflow-hidden"
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Top accent glowing bar */}
      <div className="absolute top-0 right-0 left-0 h-1.5 bg-gradient-to-r from-teal-700 to-teal-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div className="flex items-center justify-between mb-3.5">
        <div className={`w-11 h-11 rounded-2xl border flex items-center justify-center transition-transform group-hover:scale-110 ${getIconBg()}`}>
          {getIcon()}
        </div>

        <span
          className={`inline-flex items-center gap-1 text-xs font-black px-2.5 py-1 rounded-full dir-ltr ${
            metric.isPositive === null
              ? 'text-[var(--text-muted)] border border-[var(--card-border)]'
              : metric.isPositive
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300/80 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30'
              : 'bg-rose-100 text-rose-800 border border-rose-300/80 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30'
          }`}
        >
          {metric.isPositive === null ? null : metric.isPositive ? (
            <ArrowUpRight className="w-3.5 h-3.5 shrink-0 stroke-[2.5]" />
          ) : (
            <ArrowDownRight className="w-3.5 h-3.5 shrink-0 stroke-[2.5]" />
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

