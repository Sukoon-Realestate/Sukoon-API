'use client';

import { useEffect, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';
import { Bell, Search, Menu, LogOut, Settings2, ChevronDown, ChevronLeft } from 'lucide-react';
import Link from '@/components/ui/AdminLink';
import { useSidebar } from './AppLayout';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { NotificationsModal } from '@/components/ui/NotificationsModal';
import { CommandMenu } from './CommandMenu';
import { adminRelativePath } from '@/lib/basePath';
import { findAdminSection } from '@/lib/admin-navigation';
import { isBackendEnabled } from '@/lib/api/config';

interface HeaderProps { title: string; subtitle?: string; lastUpdated?: string }

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
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setShowSearch((current) => !current); }
      if (event.key === 'Escape') { setShowProfileMenu(false); setShowNotifications(false); }
    };
    const onPointerDown = (event: PointerEvent) => { if (!profile.current?.contains(event.target as Node)) setShowProfileMenu(false); };
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('pointerdown', onPointerDown);
    return () => { window.removeEventListener('keydown', onKeyDown); window.removeEventListener('pointerdown', onPointerDown); };
  }, []);

  return <>
    <header className="admin-topbar">
      <div className="admin-topbar-context flex min-w-0 items-center gap-3">
        <button type="button" onClick={toggleMobileMenu} className="admin-icon-button admin-mobile-toggle" aria-label="فتح قائمة الأقسام"><Menu size={21} /></button>
        <nav aria-label="مسار القسم" className="admin-topbar-path"><Link href="/">الإدارة</Link><ChevronLeft size={13} aria-hidden /><span>{section?.title || 'سكون'}</span></nav>
      </div>
      <button type="button" onClick={() => setShowSearch(true)} className="admin-search-trigger" aria-label="البحث في أقسام الإدارة"><Search size={17} aria-hidden /><span>ابحث عن قسم…</span><kbd>Ctrl K</kbd></button>
      <div className="admin-topbar-actions flex items-center gap-1.5 sm:gap-3">
        <ThemeToggle />
        <div className="relative"><button onClick={() => { setShowNotifications((value) => !value); setShowProfileMenu(false); }} className="admin-icon-button" aria-label="الإشعارات" aria-expanded={showNotifications}><Bell size={19} /></button><NotificationsModal isOpen={showNotifications} onClose={() => setShowNotifications(false)} /></div>
        <span className="admin-topbar-divider" />
        <div ref={profile} className="relative"><button onClick={() => setShowProfileMenu((value) => !value)} className="admin-profile-trigger" aria-label="قائمة الحساب" aria-expanded={showProfileMenu} aria-controls="admin-profile-menu"><span className="admin-avatar">{user?.name?.slice(0, 1) || 'س'}</span><span className="hidden xl:block text-start"><strong>{user?.name || 'حساب الإدارة'}</strong><small>{user?.role || 'إدارة المنصة'}</small></span><ChevronDown size={14} aria-hidden /></button>
          {showProfileMenu && <div id="admin-profile-menu" className="admin-profile-menu"><p className="px-3 pb-3 text-sm font-medium">{user?.email || 'إدارة حسابك'}</p><Link href="/settings" onClick={() => setShowProfileMenu(false)}><Settings2 size={16} />إعدادات الحساب</Link><button onClick={logout}><LogOut size={16} />تسجيل الخروج</button></div>}
        </div>
      </div>
    </header>
    <div className="admin-page-heading"><div className="min-w-0"><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div><div className="admin-heading-meta">{!isBackendEnabled() && <span className="admin-demo-label">بيانات تجريبية</span>}{lastUpdated && <span className="hidden sm:block">آخر تحديث: {lastUpdated}</span>}</div></div>
    {showSearch && <CommandMenu open={showSearch} onClose={() => setShowSearch(false)} />}
  </>;
}
