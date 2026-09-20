import React from 'react';
import { BarChart3, TrendingUp } from 'lucide-react';

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
  const totalValue = data.reduce((acc, curr) => acc + curr.value, 0);
  const avgValue = Math.round(totalValue / (data.length || 1));

  return (
    <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] animate-fadeInUp flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center border border-teal-500/20">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-extrabold text-[var(--foreground)] text-sm sm:text-base leading-tight">
                {title}
              </h3>
              <p className="text-[11px] text-[var(--text-muted)] font-medium">
                متوسط: <span className="font-bold text-[var(--foreground)]">{avgValue}</span>/يوم
              </p>
            </div>
          </div>

          {periodLabel && (
            <span
              className={`text-xs font-bold px-3 py-1 rounded-full ${
                color === 'red'
                  ? 'bg-rose-50 text-rose-600 border border-rose-200/60 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20'
                  : 'bg-teal-50 text-teal-700 border border-teal-200/60 dark:bg-teal-500/10 dark:text-teal-400 dark:border-teal-500/20'
              }`}
            >
              {periodLabel}
            </span>
          )}
        </div>

        {/* Bars visualization */}
        <div className="h-40 flex items-end justify-between gap-1.5 pt-6 pb-2 px-1">
          {data.map((item, idx) => {
            const heightPercent = (item.value / maxValue) * 100;

            let barBg = 'bg-teal-500/20 hover:bg-teal-500/40 dark:bg-teal-500/25 dark:hover:bg-teal-500/45';
            if (color === 'red') {
              barBg = item.isCurrent
                ? 'bg-gradient-to-t from-rose-600 to-rose-400 text-white shadow-xs glow-rose-sm'
                : 'bg-rose-500/20 hover:bg-rose-500/40 dark:bg-rose-500/25 dark:hover:bg-rose-500/45';
            } else {
              barBg = item.isCurrent
                ? 'bg-gradient-to-t from-teal-700 to-teal-500 text-white shadow-xs glow-teal-sm'
                : 'bg-teal-500/20 hover:bg-teal-500/40 dark:bg-teal-500/25 dark:hover:bg-teal-500/45';
            }

            return (
              <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end">
                {/* Tooltip */}
                <div className="opacity-0 group-hover:opacity-100 transition-all duration-200 absolute -top-9 bg-slate-900 text-white text-[10px] font-bold px-2 py-1 rounded-lg shadow-lg pointer-events-none z-20 whitespace-nowrap transform -translate-y-1 group-hover:translate-y-0">
                  {item.value}
                </div>

                <div
                  className={`w-full rounded-t-md transition-all duration-300 animate-barGrow ${barBg}`}
                  style={{
                    height: `${Math.max(heightPercent, 8)}%`,
                    animationDelay: `${idx * 25}ms`,
                  }}
                ></div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] font-semibold text-[var(--text-subtle)] border-t border-[var(--divider)] pt-2.5 px-1">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-teal-500"></span>
          اليوم
        </span>
        <span className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3 text-teal-600" />
          الإجمالي: {totalValue.toLocaleString()}
        </span>
        <span>منذ 30 يوم</span>
      </div>
    </div>
  );
};
