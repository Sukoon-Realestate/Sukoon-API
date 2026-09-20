'use client';

import React from 'react';
import Link from 'next/link';
import { CheckCircle2, AlertTriangle, Building2, User, ShieldCheck } from 'lucide-react';
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
        return <CheckCircle2 className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />;
      case 'alert':
        return <AlertTriangle className="w-5 h-5 text-rose-500 dark:text-rose-400" />;
      case 'building':
        return <Building2 className="w-5 h-5 text-amber-500 dark:text-amber-400" />;
      case 'user':
        return <User className="w-5 h-5 text-blue-500 dark:text-blue-400" />;
      case 'shield':
        return <ShieldCheck className="w-5 h-5 text-teal-500 dark:text-teal-400" />;
      default:
        return <CheckCircle2 className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />;
    }
  };

  const getIconBg = (type: ActivityItem['iconType']) => {
    switch (type) {
      case 'check':
        return 'bg-emerald-50 border-emerald-100 dark:bg-emerald-500/10 dark:border-emerald-500/20';
      case 'alert':
        return 'bg-rose-50 border-rose-100 dark:bg-rose-500/10 dark:border-rose-500/20';
      case 'building':
        return 'bg-amber-50 border-amber-100 dark:bg-amber-500/10 dark:border-amber-500/20';
      case 'user':
        return 'bg-blue-50 border-blue-100 dark:bg-blue-500/10 dark:border-blue-500/20';
      case 'shield':
        return 'bg-teal-50 border-teal-100 dark:bg-teal-500/10 dark:border-teal-500/20';
      default:
        return 'bg-emerald-50 border-emerald-100 dark:bg-emerald-500/10 dark:border-emerald-500/20';
    }
  };

  return (
    <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden animate-fadeInUp">
      <div className="p-6 pb-4 flex items-center justify-between border-b border-[var(--divider)]">
        <h3 className="font-bold text-[var(--foreground)] text-base">آخر الأنشطة</h3>
        {showViewAll && (
          <Link
            href="/activities"
            className="text-xs font-bold text-[var(--primary-text)] hover:underline"
          >
            عرض الكل
          </Link>
        )}
      </div>

      <div className="divide-y divide-[var(--divider)]">
        {activities.map((item, idx) => (
          <div
            key={item.id}
            className="px-6 py-4 flex items-center justify-between hover:bg-[var(--card-hover)] transition-colors animate-fadeInUp"
            style={{ animationDelay: `${idx * 80}ms` }}
          >
            <div className="flex items-center gap-3.5">
              <div
                className={`w-9 h-9 rounded-full border flex items-center justify-center shrink-0 ${getIconBg(
                  item.iconType
                )}`}
              >
                {getIcon(item.iconType)}
              </div>

              <div>
                <p className="text-sm font-semibold text-[var(--foreground)]">{item.title}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              {item.role && <StatusBadge type="role" value={item.role} />}
              <span className="text-xs text-[var(--text-subtle)] font-medium">{item.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
