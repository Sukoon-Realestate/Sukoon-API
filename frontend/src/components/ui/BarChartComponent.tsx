'use client';

import React from 'react';

interface ChartBarData {
  day: number;
  value: number;
  isCurrent?: boolean;
}

interface BarChartProps {
  title: string;
  data: ChartBarData[];
  color?: 'teal' | 'red';
  periodLabel?: string;
}

export const BarChartComponent: React.FC<BarChartProps> = ({
  title,
  data,
  color = 'teal',
  periodLabel = '30 يوم',
}) => {
  const maxValue = Math.max(...data.map((d) => d.value), 100);

  return (
    <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] animate-fadeInUp">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-bold text-[var(--foreground)] text-base flex items-center gap-2">
          {title}
        </h3>
        {periodLabel && (
          <span className={`text-xs font-semibold px-3 py-1 rounded-full ${
            color === 'red'
              ? 'bg-rose-50 text-rose-600 border border-rose-200/60 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20'
              : 'bg-teal-50 text-teal-700 border border-teal-200/60 dark:bg-teal-500/10 dark:text-teal-400 dark:border-teal-500/20'
          }`}>
            {periodLabel}
          </span>
        )}
      </div>

      {/* Bars visualization */}
      <div className="h-36 flex items-end justify-between gap-1.5 pt-4 pb-2 px-1">
        {data.map((item, idx) => {
          const heightPercent = (item.value / maxValue) * 100;
          
          let barBg = 'bg-teal-200/60 hover:bg-teal-300/70 dark:bg-teal-500/20 dark:hover:bg-teal-500/35';
          if (color === 'red') {
            barBg = item.isCurrent
              ? 'bg-rose-600 hover:bg-rose-700 dark:bg-rose-500 dark:hover:bg-rose-400'
              : 'bg-rose-200/60 hover:bg-rose-300/70 dark:bg-rose-500/20 dark:hover:bg-rose-500/35';
          } else {
            barBg = item.isCurrent
              ? 'bg-teal-700 hover:bg-teal-800 dark:bg-teal-500 dark:hover:bg-teal-400'
              : 'bg-teal-200/60 hover:bg-teal-300/70 dark:bg-teal-500/20 dark:hover:bg-teal-500/35';
          }

          return (
            <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
              {/* Tooltip */}
              <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 absolute -top-8 bg-[var(--foreground)] text-[var(--background)] text-[10px] font-bold px-2 py-0.5 rounded shadow pointer-events-none z-10 whitespace-nowrap">
                {item.value}
              </div>
              <div
                className={`w-full rounded-t-sm transition-all duration-300 animate-barGrow ${barBg}`}
                style={{
                  height: `${Math.max(heightPercent, 10)}%`,
                  animationDelay: `${idx * 30}ms`,
                }}
              ></div>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between text-[11px] text-[var(--text-subtle)] border-t border-[var(--divider)] pt-2 px-1">
        <span>اليوم</span>
        <span>1 يناير</span>
      </div>
    </div>
  );
};
