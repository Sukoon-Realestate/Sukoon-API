'use client';

import React from 'react';
import { Users, Building2, Clock, TrendingUp, Calendar, AlertTriangle } from 'lucide-react';
import { DashboardMetric } from '@/data/mockData';

interface MetricCardProps {
  metric: DashboardMetric;
}

export const MetricCard: React.FC<MetricCardProps> = ({ metric }) => {
  const getIcon = () => {
    switch (metric.icon) {
      case 'users':
        return <Users className="w-5 h-5 text-blue-600" />;
      case 'building':
        return <Building2 className="w-5 h-5 text-teal-600" />;
      case 'clock':
        return <Clock className="w-5 h-5 text-amber-600" />;
      case 'revenue':
        return <TrendingUp className="w-5 h-5 text-teal-600" />;
      case 'calendar':
        return <Calendar className="w-5 h-5 text-cyan-600" />;
      case 'alert':
        return <AlertTriangle className="w-5 h-5 text-rose-600" />;
      default:
        return <Users className="w-5 h-5 text-teal-600" />;
    }
  };

  const getIconBg = () => {
    switch (metric.icon) {
      case 'users':
        return 'bg-blue-50 border-blue-100';
      case 'building':
        return 'bg-teal-50 border-teal-100';
      case 'clock':
        return 'bg-amber-50 border-amber-100';
      case 'revenue':
        return 'bg-teal-50 border-teal-100';
      case 'calendar':
        return 'bg-cyan-50 border-cyan-100';
      case 'alert':
        return 'bg-rose-50 border-rose-100';
      default:
        return 'bg-slate-50 border-slate-100';
    }
  };

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${getIconBg()}`}>
          {getIcon()}
        </div>

        <span
          className={`text-xs font-bold px-2.5 py-1 rounded-full dir-ltr ${
            metric.isPositive
              ? 'bg-emerald-50 text-emerald-600 border border-emerald-200/60'
              : 'bg-rose-50 text-rose-600 border border-rose-200/60'
          }`}
        >
          {metric.change}
        </span>
      </div>

      <div>
        <div className="text-2xl font-black text-slate-900 leading-tight mb-1">
          {metric.value}
        </div>
        <div className="text-xs font-medium text-slate-500">{metric.title}</div>
      </div>
    </div>
  );
};
