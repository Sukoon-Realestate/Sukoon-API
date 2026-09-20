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
    <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-bold text-slate-800 text-base flex items-center gap-2">
          {title}
        </h3>
        {periodLabel && (
          <span className={`text-xs font-semibold px-3 py-1 rounded-full ${
            color === 'red' ? 'bg-rose-50 text-rose-600 border border-rose-200/60' : 'bg-teal-50 text-teal-700 border border-teal-200/60'
          }`}>
            {periodLabel}
          </span>
        )}
      </div>

      {/* Bars visualization */}
      <div className="h-36 flex items-end justify-between gap-1.5 pt-4 pb-2 px-1">
        {data.map((item, idx) => {
          const heightPercent = (item.value / maxValue) * 100;
          
          let barBg = 'bg-teal-100 hover:bg-teal-200';
          if (color === 'red') {
            barBg = item.isCurrent ? 'bg-rose-600 hover:bg-rose-700' : 'bg-rose-100 hover:bg-rose-200';
          } else {
            barBg = item.isCurrent ? 'bg-teal-700 hover:bg-teal-800' : 'bg-teal-100 hover:bg-teal-200';
          }

          return (
            <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
              {/* Tooltip */}
              <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-8 bg-slate-800 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow pointer-events-none z-10 whitespace-nowrap">
                {item.value}
              </div>
              <div
                className={`w-full rounded-t-sm transition-all duration-300 ${barBg}`}
                style={{ height: `${Math.max(heightPercent, 10)}%` }}
              ></div>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 pt-2 px-1">
        <span>اليوم</span>
        <span>1 يناير</span>
      </div>
    </div>
  );
};
