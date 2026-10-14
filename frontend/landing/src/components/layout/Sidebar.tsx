'use client';

import { useEffect, useState, useRef } from 'react';
import Image from 'next/image';
import PublicLink from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronDown, X, ArrowUpLeft, Search } from 'lucide-react';
import Link from '@/components/ui/AdminLink';
import logo from '@/assets/brand/logo.png';
import { adminRelativePath } from '@/lib/basePath';
import { activeAdminHref, adminNavigation } from '@/lib/admin-navigation';
import { fetchDashboardStats } from '@/lib/api/dashboard';
import { fetchAdminPropertyMetrics } from '@/lib/api/properties';
import { fetchSupportMetrics } from '@/lib/api/support';
import { useAuth } from '@/context/AuthContext';

interface SidebarProps { isMobileOpen?: boolean; onCloseMobile?: () => void }

export function Sidebar({ isMobileOpen = false, onCloseMobile }: SidebarProps) {
  const pathname = adminRelativePath(usePathname());
  const activeHref = activeAdminHref(pathname);
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [query, setQuery] = useState('');
  const [counts, setCounts] = useState<Record<string, number>>({});
  const drawer = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([fetchDashboardStats(), fetchAdminPropertyMetrics(), fetchSupportMetrics()]).then(([dashboard, properties, support]) => {
      if (cancelled) return;
      const values: Record<string, number> = {};
      if (dashboard.status === 'fulfilled') values.kyc = dashboard.value.user_distribution.pending;
      if (properties.status === 'fulfilled') values.properties = properties.value.pending;
      if (support.status === 'fulfilled') values.support = support.value.openTickets;
      setCounts(values);
    });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const dialog = drawer.current;
    if (!dialog) return;
    if (isMobileOpen && !dialog.open) dialog.showModal();
    if (!isMobileOpen && dialog.open) dialog.close();
    if (!isMobileOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = previousOverflow; };
  }, [isMobileOpen]);

  const content = (mobile: boolean) => <>
    <div className="admin-sidebar-brand">
      <Link href="/" onClick={onCloseMobile} className="flex items-center gap-3" aria-label="سكون، ملخص المنصة">
        <Image src={logo} alt="" width={38} height={38} priority className="size-10 object-contain" />
        <span><strong className="block text-xl font-semibold">سكون</strong><span className="text-xs text-[var(--text-muted)]">مساحة الإدارة</span></span>
      </Link>
      {mobile ? <button className="admin-icon-button" aria-label="إغلاق القائمة" onClick={onCloseMobile}><X size={19} /></button> : null}
    </div>
    <div className="admin-workspace"><span className="admin-workspace-mark">S</span><div><strong>إدارة منصة سكون</strong><span>العقارات والمجتمع</span></div></div>
    <label className="admin-nav-filter"><Search size={16} aria-hidden /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="تصفية القائمة…" aria-label="تصفية أقسام الإدارة" /></label>
    <nav aria-label="أقسام الإدارة" className="admin-sidebar-nav">
      {adminNavigation.map((group) => {
        const items = group.items.filter((item) => `${item.title} ${item.description}`.includes(query.trim()));
        if (!items.length) return null;
        const hasActive = group.items.some((item) => item.href === activeHref);
        const isOpen = Boolean(query.trim()) || !(collapsed[group.id] ?? (group.id !== 'overview' && !hasActive));
        const panelId = `nav-${mobile ? 'mobile' : 'desktop'}-${group.id}`;
        return <section key={group.id} className="admin-nav-group">
          <button type="button" className="admin-nav-heading" aria-expanded={isOpen} aria-controls={panelId} onClick={() => setCollapsed((current) => ({ ...current, [group.id]: isOpen }))}>
            <span>{group.title}</span><ChevronDown size={14} className={isOpen ? '' : '-rotate-90'} aria-hidden />
          </button>
          <div id={panelId} hidden={!isOpen}>
            {items.map((item) => {
              const Icon = item.icon;
              const selected = item.href === activeHref;
              return <Link key={item.href} href={item.href} onClick={onCloseMobile} className={`admin-nav-item ${selected ? 'is-active' : ''}`} aria-current={selected ? 'page' : undefined}>
                <Icon size={18} strokeWidth={1.7} aria-hidden /><span>{item.title}</span>
                {item.count && counts[item.count] > 0 && <span className="admin-nav-count">{counts[item.count].toLocaleString('en-US')}</span>}
              </Link>;
            })}
          </div>
        </section>;
      })}
      {query.trim() && !adminNavigation.some((group) => group.items.some((item) => `${item.title} ${item.description}`.includes(query.trim()))) && <p className="px-3 py-6 text-sm text-[var(--text-muted)]">لا توجد أقسام بهذا الاسم.</p>}
    </nav>
    <div className="admin-sidebar-footer">
      <PublicLink href="/ar" className="admin-public-link">زيارة الموقع <ArrowUpLeft size={16} aria-hidden /></PublicLink>
      <div className="admin-sidebar-user"><span className="admin-avatar">{user?.name?.slice(0, 1) || 'س'}</span><div><strong>{user?.name || 'حساب الإدارة'}</strong><span>{user?.role || 'إدارة المنصة'}</span></div></div>
    </div>
  </>;

  return <>
    <aside className="admin-sidebar hidden lg:flex">{content(false)}</aside>
    <dialog ref={drawer} className="admin-mobile-drawer" onCancel={onCloseMobile} onClick={(event) => { if (event.target === event.currentTarget) onCloseMobile?.(); }}><div className="admin-drawer-inner">{content(true)}</div></dialog>
  </>;
}
