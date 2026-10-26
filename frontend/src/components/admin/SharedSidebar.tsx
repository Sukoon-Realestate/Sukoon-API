'use client';

import { useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import PublicLink from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronDown, Search, X } from 'lucide-react';
import Link from '@/components/ui/AdminLink';
import logo from '@/assets/brand/logo.png';
import { useAuth } from '@/context/AuthContext';
import { adminRelativePath } from '@/lib/basePath';
import { activeAdminHref, adminNavigation } from '../../lib/admin-navigation';
import { canOpenAdminPath } from '../../lib/admin-access';
import { fetchAdminFollowups } from '../../lib/api/followups';

export function SharedSidebar({ isMobileOpen = false, onCloseMobile, publicSiteHref }: {
  isMobileOpen?: boolean; onCloseMobile?: () => void; publicSiteHref?: string;
}) {
  const { user } = useAuth();
  const selected = activeAdminHref(adminRelativePath(usePathname()));
  const drawer = useRef<HTMLDialogElement>(null);
  const [query, setQuery] = useState('');
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [counts, setCounts] = useState<{ owner: string; values: Record<string, number> } | null>(null);
  useEffect(() => {
    if (!user || user.role === 'security_recovery_reviewer') return;
    const controller = new AbortController();
    void fetchAdminFollowups(controller.signal).then(result => {
      if (!controller.signal.aborted) setCounts({ owner: user.id, values: Object.fromEntries(result.results.filter(row => row.id !== 'escalations').map(row => [row.href, row.count])) });
    }).catch(() => { if (!controller.signal.aborted) setCounts(null); });
    return () => controller.abort();
  }, [user]);
  useEffect(() => {
    const dialog = drawer.current;
    if (isMobileOpen && dialog && !dialog.open) dialog.showModal();
    if (!isMobileOpen && dialog?.open) dialog.close();
    if (!isMobileOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = previous; };
  }, [isMobileOpen]);
  const groups = adminNavigation.map(group => ({ ...group, items: group.items.filter(item =>
    canOpenAdminPath(user?.allowedPaths, item.href) && `${item.title} ${item.description}`.includes(query.trim())) })).filter(group => group.items.length);
  const content = (mobile: boolean) => <div className="flex h-full min-w-0 flex-col">
    <div className="flex items-center justify-between gap-3 p-4">
      <Link href={user?.allowedPaths.includes('/') ? '/' : '/security'} onClick={onCloseMobile} className="flex min-w-0 items-center gap-3">
        <Image src={logo} alt="" width={38} height={38} /><span><strong className="block text-xl">سكون</strong><span className="text-xs">مساحة الإدارة</span></span>
      </Link>
      {mobile && <button className="min-h-12 min-w-12" aria-label="إغلاق القائمة" onClick={onCloseMobile}><X className="mx-auto" /></button>}
    </div>
    <label className="mx-3 flex items-center gap-2 rounded-lg border border-[var(--card-border)] px-3 py-2"><Search size={16} aria-hidden /><input className="min-w-0 w-full bg-transparent py-2 text-sm" aria-label="تصفية أقسام الإدارة" placeholder="تصفية القائمة…" value={query} onChange={event => setQuery(event.target.value)} /></label>
    <nav aria-label="أقسام الإدارة" className="min-h-0 flex-1 space-y-4 overflow-y-auto p-3">
      {groups.map(group => {
        const open = !!query.trim() || !(collapsed[group.id] ?? (group.id !== 'overview' && !group.items.some(item => item.href === selected)));
        const panel = `nav-${mobile ? 'mobile' : 'desktop'}-${group.id}`;
        return <section key={group.id}>
          <button className="flex min-h-12 w-full items-center justify-between gap-2 px-2 text-sm font-semibold" aria-expanded={open} aria-controls={panel} onClick={() => setCollapsed(current => ({ ...current, [group.id]: open }))}>
            {group.title}<ChevronDown size={16} className={open ? '' : '-rotate-90'} aria-hidden />
          </button>
          <div id={panel} hidden={!open}>{group.items.map(item => {
            const Icon = item.icon;
            const count = counts?.owner === user?.id ? counts?.values[`/admin${item.href}`] : undefined;
            return <Link key={item.href} href={item.href} onClick={onCloseMobile} aria-current={selected === item.href ? 'page' : undefined}
              className={`my-1 flex min-h-12 min-w-0 items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-[var(--card-hover)] ${selected === item.href ? 'bg-[var(--card-hover)] font-bold' : ''}`}>
              <Icon size={18} className="shrink-0" aria-hidden /><span className="min-w-0 flex-1">{item.title}</span>{count !== undefined && <span>{count}</span>}
            </Link>;
          })}</div>
        </section>;
      })}
      {!groups.length && <p className="p-3 text-sm">لا توجد أقسام متاحة بهذا الاسم.</p>}
    </nav>
    <div className="space-y-3 border-t border-[var(--card-border)] p-4 text-sm [overflow-wrap:anywhere]">
      {publicSiteHref && <PublicLink href={publicSiteHref}>زيارة موقع سكون</PublicLink>}
      <p>{user?.name}</p><p className="text-xs">{user?.role}</p>
    </div>
  </div>;
  return <>
    <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 border-e border-[var(--card-border)] bg-[var(--card-bg)] lg:block">{content(false)}</aside>
    <dialog ref={drawer} aria-label="قائمة الإدارة" className="fixed inset-0 m-0 h-dvh max-h-none w-80 max-w-[90vw] border-0 bg-[var(--card-bg)] text-[var(--foreground)] backdrop:bg-black/50"
      onCancel={onCloseMobile} onClick={event => { if (event.target === event.currentTarget) onCloseMobile?.(); }}>{content(true)}</dialog>
  </>;
}
