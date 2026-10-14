import Link from '@/components/ui/AdminLink';
import { ClipboardCheck, ShieldCheck, Headphones, ArrowUpLeft } from 'lucide-react';

export function QuickActionsToolbar() {
  return <nav className="admin-quick-actions" aria-label="اختصارات العمل"><span>وصول سريع</span>{[
    { title: 'مراجعة العقارات', href: '/properties/review', icon: ClipboardCheck },
    { title: 'توثيق الهوية', href: '/kyc', icon: ShieldCheck },
    { title: 'دعم العملاء', href: '/support', icon: Headphones },
  ].map((item) => { const Icon = item.icon; return <Link key={item.href} href={item.href}><Icon size={16} aria-hidden />{item.title}<ArrowUpLeft size={14} aria-hidden /></Link>; })}</nav>;
}
