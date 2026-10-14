import Link from '@/components/ui/AdminLink';
import { ArrowUpRight, ArrowDownRight, ArrowUpLeft } from 'lucide-react';
import type { DashboardMetric } from '@/lib/api/types';

const destinations: Record<DashboardMetric['icon'], string> = {
  users: '/users', building: '/properties', clock: '/kyc', revenue: '/financials', calendar: '/analytics', alert: '/users/reports',
};
interface MetricCardProps { metric: DashboardMetric; delay?: number; href?: string }
export function MetricCard({ metric, href }: MetricCardProps) {
  const Trend = metric.isPositive ? ArrowUpRight : ArrowDownRight;
  return <Link href={href || destinations[metric.icon]} className="admin-metric">
    <div className="admin-metric-label"><span>{metric.title}</span><ArrowUpLeft size={16} aria-hidden /></div>
    <strong className="admin-metric-value" dir="auto">{metric.value}</strong>
    {metric.change && <span className={`admin-metric-change ${metric.isPositive ? 'is-positive' : 'is-negative'}`}><Trend size={15} aria-hidden /><span dir="auto">{metric.change}</span></span>}
  </Link>;
}
