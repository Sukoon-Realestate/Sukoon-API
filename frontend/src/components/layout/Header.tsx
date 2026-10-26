'use client';

import { useEffect, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';
import { Bell, Search, Menu, LogOut, ChevronDown } from 'lucide-react';
import Link from '@/components/ui/AdminLink';
import { useSidebar } from '@/components/layout/AppLayout';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '../ui/ThemeToggle';
import { NotificationsModal } from '../ui/NotificationsModal';
import { CommandMenu } from './CommandMenu';
import { adminRelativePath } from '@/lib/basePath';
import { findAdminSection } from '../../lib/admin-navigation';
import { canOpenAdminPath } from '../../lib/admin-access';

interface HeaderProps { title: string; subtitle?: string; lastUpdated?: string }
const iconButton = 'flex min-h-12 min-w-12 items-center justify-center rounded-lg hover:bg-[var(--card-hover)]';
export function Header({ title, subtitle, lastUpdated }: HeaderProps) {
  const { toggleMobileMenu } = useSidebar();
  const { logout, user } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const profile = useRef<HTMLDivElement>(null);
  const section = findAdminSection(adminRelativePath(usePathname()));
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setShowSearch(value => !value); }
      if (event.key === 'Escape') { setShowProfileMenu(false); setShowNotifications(false); }
    };
    const onPointerDown = (event: PointerEvent) => { if (!profile.current?.contains(event.target as Node)) setShowProfileMenu(false); };
    window.addEventListener('keydown', onKeyDown); window.addEventListener('pointerdown', onPointerDown);
    return () => { window.removeEventListener('keydown', onKeyDown); window.removeEventListener('pointerdown', onPointerDown); };
  }, []);
  return <>
    <header className="flex min-w-0 flex-wrap items-center justify-between gap-2 border-b border-[var(--header-border)] bg-[var(--header-bg)] px-4 py-2 text-sm sm:px-6" dir="rtl">
      <div className="flex min-w-0 flex-1 items-center gap-2">
        <button type="button" onClick={toggleMobileMenu} className={`${iconButton} lg:hidden`} aria-label="فتح قائمة الأقسام"><Menu size={21} /></button>
        <nav aria-label="مسار القسم" className="flex min-w-0 flex-wrap gap-2"><Link href={user?.allowedPaths.includes('/') ? '/' : '/security'}>الإدارة</Link><span aria-hidden>/</span><span>{section?.title || 'سكون'}</span></nav>
      </div>
      <div className="flex flex-wrap items-center gap-1">
        <button type="button" className={iconButton} onClick={() => setShowSearch(true)} aria-label="البحث في أقسام الإدارة"><Search size={20} /></button>
        <ThemeToggle />
        {user?.role !== 'security_recovery_reviewer' && <button className={iconButton} aria-label="متابعات الإدارة" aria-expanded={showNotifications} onClick={() => { setShowNotifications(true); setShowProfileMenu(false); }}><Bell size={20} /></button>}
        <div ref={profile} className="relative">
          <button type="button" className={`${iconButton} gap-2 px-2`} aria-label="قائمة الحساب" aria-expanded={showProfileMenu} aria-controls="admin-profile-menu" onClick={() => { setShowProfileMenu(value => !value); setShowNotifications(false); }}>
            <span className="flex size-9 items-center justify-center rounded-full bg-[var(--primary-subtle)]">{user?.name?.slice(0, 1) || 'س'}</span><ChevronDown size={14} />
          </button>
          {showProfileMenu && <div id="admin-profile-menu" className="absolute end-0 top-full z-40 w-60 max-w-[80vw] space-y-2 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-3 shadow-lg [overflow-wrap:anywhere]">
            <p>{user?.name}</p><p className="text-xs">{user?.email}</p><p className="text-xs">{user?.role}</p>
            {[
              ['/security', 'أمان الحساب وعامل التحقق'], ['/settings', 'إعدادات الحساب والنظام'], ['/roles', 'الفريق والصلاحيات'],
            ].filter(([path]) => canOpenAdminPath(user?.allowedPaths, path)).map(([path, label]) => <Link key={path} href={path} className="block min-h-12 rounded-lg px-2 py-3 hover:bg-[var(--card-hover)]" onClick={() => setShowProfileMenu(false)}>{label}</Link>)}
            <button className="flex min-h-12 w-full items-center gap-2 border-t px-2 py-3" onClick={() => void logout()}><LogOut size={18} />تسجيل الخروج</button>
          </div>}
        </div>
      </div>
    </header>
    <div dir="rtl" className="space-y-2 px-4 pt-6 pb-3 sm:px-6 lg:px-8 [overflow-wrap:anywhere]"><h1 className="text-xl font-bold sm:text-2xl">{title}</h1>
      {subtitle && <p className="text-sm text-[var(--text-muted)]">{subtitle}</p>}{lastUpdated && <p className="text-xs text-[var(--text-subtle)]">آخر قراءة: {lastUpdated}</p>}
    </div>
    <NotificationsModal isOpen={showNotifications} onClose={() => setShowNotifications(false)} />
    {showSearch && <CommandMenu open onClose={() => setShowSearch(false)} />}
  </>;
}
