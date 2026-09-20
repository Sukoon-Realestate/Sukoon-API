'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  ShieldCheck,
  Building2,
  FileText,
  Shield,
  Settings,
  ShieldAlert,
  UserX,
  ClipboardList,
  Headphones,
  DollarSign,
  Receipt,
  BarChart3,
  ShieldBan,
  BellRing,
  History,
  Activity,
  X,
  Radio,
} from 'lucide-react';

interface SidebarProps {
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isMobileOpen = false, onCloseMobile }) => {
  const pathname = usePathname();

  const section1 = [
    {
      title: 'لوحة التحكم',
      href: '/',
      icon: LayoutDashboard,
      active: pathname === '/' || pathname === '/executive',
    },
    {
      title: 'المستخدمون',
      href: '/users',
      icon: Users,
      active: pathname === '/users' || pathname.startsWith('/users/sara'),
    },
    {
      title: 'الموقوفون والمحظورون',
      href: '/users/suspended',
      icon: UserX,
      badge: '43',
      active: pathname === '/users/suspended',
    },
    {
      title: 'التوثيق KYC',
      href: '/kyc',
      icon: ShieldCheck,
      badge: '487',
      active: pathname === '/kyc' || pathname === '/kyc/review',
    },
    {
      title: 'إدارة العقارات',
      href: '/properties',
      icon: Building2,
      active: pathname === '/properties',
    },
    {
      title: 'مراجعة العقارات',
      href: '/properties/review',
      icon: ClipboardList,
      badge: '234',
      active: pathname === '/properties/review' || pathname.startsWith('/properties/prop-1'),
    },
  ];

  const section2 = [
    {
      title: 'مراجعة المحتوى',
      href: '/moderation',
      icon: ShieldBan,
      badge: '14',
      active: pathname === '/moderation',
    },
    {
      title: 'طابور البلاغات',
      href: '/users/reports',
      icon: ShieldAlert,
      badge: '31',
      active: pathname === '/users/reports',
    },
    {
      title: 'دعم العملاء',
      href: '/support',
      icon: Headphones,
      badge: '31',
      active: pathname.startsWith('/support'),
    },
    {
      title: 'التقارير والتذاكر',
      href: '/reports/overview',
      icon: FileText,
      active: pathname === '/reports/overview' || pathname === '/reports',
    },
    {
      title: 'التحليلات والتقارير',
      href: '/analytics',
      icon: BarChart3,
      active: pathname === '/analytics',
    },
  ];

  const section3 = [
    {
      title: 'الإيرادات والمالية',
      href: '/financials',
      icon: DollarSign,
      active: pathname === '/financials',
    },
    {
      title: 'سجل المعاملات',
      href: '/financials/transactions',
      icon: Receipt,
      active: pathname === '/financials/transactions',
    },
    {
      title: 'الإشعارات المدفوعة',
      href: '/notifications',
      icon: BellRing,
      active: pathname === '/notifications',
    },
    {
      title: 'سجل النشاط',
      href: '/system/logs',
      icon: History,
      active: pathname === '/system/logs',
    },
    {
      title: 'الأدوار والصلاحيات',
      href: '/roles',
      icon: Shield,
      active: pathname === '/roles',
    },
    {
      title: 'صحة النظام',
      href: '/system/health',
      icon: Activity,
      active: pathname === '/system/health',
    },
    {
      title: 'إعدادات النظام',
      href: '/settings',
      icon: Settings,
      active: pathname === '/settings',
    },
  ];

  const renderNavGroup = (items: typeof section1, startIndex: number) => (
    <div className="space-y-1">
      {items.map((item, idx) => {
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onCloseMobile}
            className={`relative flex items-center justify-between px-3.5 py-2.5 rounded-xl font-bold text-xs transition-all duration-200 group animate-slideInFromSide cursor-pointer ${
              item.active
                ? 'bg-teal-500/15 text-teal-400 font-extrabold shadow-xs border border-teal-500/20'
                : 'text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover)] hover:text-slate-100'
            }`}
            style={{ animationDelay: `${(startIndex + idx) * 20}ms` }}
          >
            {item.active && (
              <span className="absolute right-0 top-2 bottom-2 w-1.5 rounded-l-full bg-teal-400 glow-teal-sm"></span>
            )}
            <div className="flex items-center gap-3 pr-1">
              <Icon
                className={`w-4 h-4 transition-transform duration-200 group-hover:scale-110 ${
                  item.active ? 'text-teal-400' : 'text-[var(--sidebar-text)] group-hover:text-slate-200'
                }`}
              />
              <span>{item.title}</span>
            </div>
            {item.badge && (
              <span className="px-2 py-0.5 text-[10px] font-extrabold bg-slate-800/90 text-teal-400 rounded-full border border-teal-500/30">
                {item.badge}
              </span>
            )}
          </Link>
        );
      })}
    </div>
  );

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Brand Header */}
      <div className="p-5 flex items-center justify-between border-b border-[var(--sidebar-border)] bg-slate-950/40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-400 shadow-inner glow-teal-sm animate-breathe">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-black text-white text-base tracking-tight leading-tight">سكون – Sukoon Admin</h1>
            <p className="text-[11px] font-semibold text-[var(--sidebar-text)] mt-0.5">منظومة المراجعة والتوثيق</p>
          </div>
        </div>

        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 text-[var(--sidebar-text)] hover:text-white rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Mode Quick Switcher */}
      <div className="px-4 pt-4 pb-2">
        <div className="bg-slate-900/80 p-1 rounded-xl flex text-xs font-bold border border-slate-800 shadow-inner">
          <Link
            href="/"
            onClick={onCloseMobile}
            className={`flex-1 text-center py-1.5 rounded-lg transition-all duration-200 cursor-pointer ${
              pathname === '/' ? 'bg-teal-600 text-white font-extrabold shadow-sm' : 'text-[var(--sidebar-text)] hover:text-white'
            }`}
          >
            الرئيسية
          </Link>
          <Link
            href="/executive"
            onClick={onCloseMobile}
            className={`flex-1 text-center py-1.5 rounded-lg transition-all duration-200 cursor-pointer ${
              pathname === '/executive' ? 'bg-teal-600 text-white font-extrabold shadow-sm' : 'text-[var(--sidebar-text)] hover:text-white'
            }`}
          >
            التنفيذية
          </Link>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-3 space-y-4 overflow-y-auto">
        <div>
          <div className="px-3 pb-1 text-[10px] font-extrabold tracking-wider text-teal-400/80 uppercase">
            الإدارة الرئيسية
          </div>
          {renderNavGroup(section1, 0)}
        </div>

        <div>
          <div className="px-3 pb-1 text-[10px] font-extrabold tracking-wider text-cyan-400/80 uppercase">
            المراقبة والدعم
          </div>
          {renderNavGroup(section2, section1.length)}
        </div>

        <div>
          <div className="px-3 pb-1 text-[10px] font-extrabold tracking-wider text-emerald-400/80 uppercase">
            المالية والنظام
          </div>
          {renderNavGroup(section3, section1.length + section2.length)}
        </div>
      </nav>

      {/* Footer Info */}
      <div className="p-3.5 border-t border-[var(--sidebar-border)] bg-slate-950/40 text-[11px] text-[var(--sidebar-text)] flex items-center justify-between">
        <span className="font-bold">Sukoon Real Estate</span>
        <span className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full text-[10px] font-extrabold">
          <Radio className="w-3 h-3 animate-pulse" />
          متصل • v1.4.0
        </span>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Sidebar */}
      <aside className="hidden lg:flex w-64 bg-[var(--sidebar-bg)] text-slate-300 min-h-screen flex-col border-l border-[var(--sidebar-border)] shrink-0">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs animate-fadeIn"
            onClick={onCloseMobile}
          />
          {/* Drawer Panel */}
          <aside className="relative w-72 max-w-[80vw] bg-[var(--sidebar-bg)] text-slate-300 h-full flex flex-col shadow-2xl border-l border-[var(--sidebar-border)] z-10 animate-slideInDrawer">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
};
