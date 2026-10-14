import Link from '@/components/ui/AdminLink';
import { Check, Flag, Building2, UserRound, ShieldCheck, History, ArrowUpLeft } from 'lucide-react';
import type { ActivityItem } from '@/lib/api/types';
import { StatusBadge } from './StatusBadge';

const icons = { check: Check, alert: Flag, building: Building2, user: UserRound, shield: ShieldCheck };
export function ActivityFeed({ activities, showViewAll = true }: { activities: ActivityItem[]; showViewAll?: boolean }) {
  return <section className="admin-panel admin-activity">
    <div className="admin-panel-heading"><div><h2>آخر الأنشطة</h2><p>آخر الإجراءات المسجلة على المنصة</p></div>{showViewAll && <Link href="/system/logs" className="admin-text-link">عرض السجل<ArrowUpLeft size={15} aria-hidden /></Link>}</div>
    {activities.length ? <ol className="admin-activity-list">{activities.map((item) => { const Icon = icons[item.iconType] || History; return <li key={item.id}><span className={`admin-activity-icon ${item.iconType === 'alert' ? 'is-alert' : ''}`}><Icon size={17} aria-hidden /></span><div><p>{item.title}</p><time>{item.time}</time></div>{item.role && <StatusBadge type="role" value={item.role} />}</li>; })}</ol> : <div className="admin-inline-empty"><History size={24} aria-hidden /><p>ستظهر الإجراءات الجديدة هنا عند تسجيلها.</p></div>}
  </section>;
}
