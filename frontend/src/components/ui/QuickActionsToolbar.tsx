'use client';
import Link from '@/components/ui/AdminLink';
import { useAuth } from '@/context/AuthContext';
import { canOpenAdminPath } from '../../lib/admin-access';

export function QuickActionsToolbar() {
  const { user } = useAuth();
  const links = [
    { title: 'مراجعة العقارات', href: '/properties/review' },
    { title: 'توثيق الهوية', href: '/kyc' },
    { title: 'دعم العملاء', href: '/support' },
    { title: 'الفريق والصلاحيات', href: '/roles' },
  ].filter(item => canOpenAdminPath(user?.allowedPaths, item.href));
  if (!links.length) return null;
  return <nav aria-label="اختصارات العمل" className="flex flex-wrap gap-3">{links.map(item =>
    <Link key={item.href} href={item.href} className="min-h-12 rounded-lg border border-[var(--card-border)] px-4 py-3">{item.title}</Link>)}</nav>;
}
