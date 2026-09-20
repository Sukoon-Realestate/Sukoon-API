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
        return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case 'alert':
        return <AlertTriangle className="w-5 h-5 text-rose-500" />;
      case 'building':
        return <Building2 className="w-5 h-5 text-amber-500" />;
      case 'user':
        return <User className="w-5 h-5 text-blue-500" />;
      case 'shield':
        return <ShieldCheck className="w-5 h-5 text-teal-500" />;
      default:
        return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
    }
  };

  const getIconBg = (type: ActivityItem['iconType']) => {
    switch (type) {
      case 'check':
        return 'bg-emerald-50 border-emerald-100';
      case 'alert':
        return 'bg-rose-50 border-rose-100';
      case 'building':
        return 'bg-amber-50 border-amber-100';
      case 'user':
        return 'bg-blue-50 border-blue-100';
      case 'shield':
        return 'bg-teal-50 border-teal-100';
      default:
        return 'bg-emerald-50 border-emerald-100';
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div className="p-6 pb-4 flex items-center justify-between border-b border-slate-100">
        <h3 className="font-bold text-slate-800 text-base">آخر الأنشطة</h3>
        {showViewAll && (
          <Link
            href="/activities"
            className="text-xs font-bold text-teal-700 hover:text-teal-800 hover:underline"
          >
            عرض الكل
          </Link>
        )}
      </div>

      <div className="divide-y divide-slate-100">
        {activities.map((item) => (
          <div
            key={item.id}
            className="px-6 py-4 flex items-center justify-between hover:bg-slate-50/70 transition-colors"
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
                <p className="text-sm font-semibold text-slate-800">{item.title}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              {item.role && <StatusBadge type="role" value={item.role} />}
              <span className="text-xs text-slate-400 font-medium">{item.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
