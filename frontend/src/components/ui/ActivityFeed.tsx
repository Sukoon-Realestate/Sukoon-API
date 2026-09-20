import React from 'react';
import Link from 'next/link';
import { CheckCircle2, AlertTriangle, Building2, User, ShieldCheck, Clock, ArrowRight } from 'lucide-react';
import { ActivityItem } from '@/data/mockData';
import { StatusBadge } from './StatusBadge';

interface ActivityFeedProps {
  activities: ActivityItem[];
  showViewAll?: boolean;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  activities,
  showViewAll = true,
}) => {
  const getIcon = (type: ActivityItem['iconType']) => {
    switch (type) {
      case 'check':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />;
      case 'alert':
        return <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400" />;
      case 'building':
        return <Building2 className="w-4 h-4 text-amber-600 dark:text-amber-400" />;
      case 'user':
        return <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />;
      case 'shield':
        return <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400" />;
      default:
        return <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />;
    }
  };

  const getIconBg = (type: ActivityItem['iconType']) => {
    switch (type) {
      case 'check':
        return 'bg-emerald-500/10 border-emerald-200/80 dark:border-emerald-500/30 glow-teal-sm';
      case 'alert':
        return 'bg-rose-500/10 border-rose-200/80 dark:border-rose-500/30 glow-rose-sm';
      case 'building':
        return 'bg-amber-500/10 border-amber-200/80 dark:border-amber-500/30 glow-amber-sm';
      case 'user':
        return 'bg-blue-500/10 border-blue-200/80 dark:border-blue-500/30 glow-blue-sm';
      case 'shield':
        return 'bg-teal-500/10 border-teal-200/80 dark:border-teal-500/30 glow-teal-sm';
      default:
        return 'bg-emerald-500/10 border-emerald-200/80 dark:border-emerald-500/30';
    }
  };

  return (
    <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden animate-fadeInUp">
      <div className="p-5 pb-4 flex items-center justify-between border-b border-[var(--divider)]">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse"></div>
          <h3 className="font-extrabold text-[var(--foreground)] text-base">سجل الأنشطة والأحداث الحية</h3>
        </div>
        {showViewAll && (
          <Link
            href="/system/logs"
            className="inline-flex items-center gap-1 text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline"
          >
            <span>عرض جميع السجلات</span>
            <ArrowRight className="w-3.5 h-3.5 rotate-180" />
          </Link>
        )}
      </div>

      <div className="p-4 relative space-y-3">
        {/* Timeline connector line */}
        <div className="absolute right-8 top-8 bottom-8 w-0.5 bg-[var(--divider)] hidden sm:block"></div>

        {activities.map((item, idx) => (
          <div
            key={item.id}
            className="group relative p-3.5 rounded-xl border border-transparent hover:border-[var(--card-border)] hover:bg-[var(--card-hover)] transition-all flex items-center justify-between gap-3 animate-fadeInUp cursor-pointer"
            style={{ animationDelay: `${idx * 60}ms` }}
          >
            <div className="flex items-center gap-3.5 min-w-0">
              <div
                className={`w-9 h-9 rounded-xl border flex items-center justify-center shrink-0 z-10 transition-transform group-hover:scale-110 ${getIconBg(
                  item.iconType
                )}`}
              >
                {getIcon(item.iconType)}
              </div>

              <div className="min-w-0">
                <p className="text-xs sm:text-sm font-bold text-[var(--foreground)] leading-snug truncate">
                  {item.title}
                </p>
                <div className="flex items-center gap-2 mt-0.5 sm:hidden">
                  <span className="text-[11px] text-[var(--text-muted)] font-medium flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {item.time}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2.5 shrink-0">
              {item.role && <StatusBadge type="role" value={item.role} />}
              <span className="hidden sm:inline-flex items-center gap-1 text-xs text-[var(--text-muted)] font-semibold bg-[var(--badge-bg-muted)] px-2.5 py-1 rounded-full border border-[var(--card-border)]">
                <Clock className="w-3.5 h-3.5 text-teal-600" />
                {item.time}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
