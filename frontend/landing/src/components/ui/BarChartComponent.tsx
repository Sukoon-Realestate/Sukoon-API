import type { CSSProperties } from 'react';
import { ChartColumn } from 'lucide-react';

export interface ChartBarData { day?: number; label?: string; value: number; isCurrent?: boolean }
interface BarChartProps { title: string; data: ChartBarData[]; color?: 'teal' | 'red'; periodLabel?: string }
export function BarChartComponent({ title, data, color = 'teal', periodLabel = '30 يوم' }: BarChartProps) {
  const max = Math.max(...data.map((item) => item.value), 1);
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const step = Math.max(1, Math.ceil(data.length / 6));
  return <section className="admin-panel admin-chart" aria-label={title}>
    <div className="admin-panel-heading"><div><h2>{title}</h2><p>إجمالي الفترة <strong>{total.toLocaleString('en-US')}</strong></p></div><span className="admin-period-label">{periodLabel}</span></div>
    {data.length ? <>
      <div className="admin-chart-area">
        <div className="admin-chart-axis" aria-hidden>{[max, max / 2, 0].map((value, index) => <span key={index}>{Math.round(value).toLocaleString('en-US')}</span>)}</div>
        <div className="admin-chart-bars" role="img" aria-label={`${title}: ${data.map((item) => `${item.label || item.day || ''}: ${item.value}`).join('، ')}`}>
          {data.map((item, index) => <div key={index} className="admin-chart-column"><div className={`admin-chart-bar ${color === 'red' ? 'is-red' : ''} ${item.isCurrent || index === data.length - 1 ? 'is-current' : ''}`} style={{ '--bar-height': `${Math.max(0, item.value / max * 100)}%` } as CSSProperties} title={`${item.label || item.day || index + 1}: ${item.value.toLocaleString('en-US')}`} /><span>{index % step === 0 || index === data.length - 1 ? item.label || item.day || index + 1 : ''}</span></div>)}
        </div>
      </div>
      <div className="admin-chart-caption"><span><i />{title}</span><span>متوسط الفترة: {Math.round(total / data.length).toLocaleString('en-US')}</span></div>
    </> : <div className="admin-chart-empty"><ChartColumn size={30} strokeWidth={1.4} aria-hidden /><p>لا توجد بيانات لهذه الفترة بعد.</p></div>}
  </section>;
}
