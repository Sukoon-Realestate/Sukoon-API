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
} from 'lucide-react';

interface SidebarProps {
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isMobileOpen = false, onCloseMobile }) => {
  const pathname = usePathname();

  const navItems = [
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
      title: 'الأدوار',
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
      title: 'النظام',
      href: '/settings',
      icon: Settings,
      active: pathname === '/settings',
    },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Brand Header */}
      <div className="p-6 flex items-center justify-between border-b border-[var(--sidebar-border)]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-teal-600/20 border border-teal-500/40 flex items-center justify-center text-teal-400 shadow-inner animate-breathe">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-white text-lg leading-tight">سكون – Admin</h1>
            <p className="text-xs text-[var(--sidebar-text)]">لوحة الإدارة المركزية</p>
          </div>
        </div>

        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 text-[var(--sidebar-text)] hover:text-white rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Mode Quick Switcher */}
      <div className="px-4 pt-4 pb-2">
        <div className="bg-slate-800/60 p-1 rounded-xl flex text-xs font-medium border border-slate-700/50">
          <Link
            href="/"
            onClick={onCloseMobile}
            className={`flex-1 text-center py-1.5 rounded-lg transition-all duration-200 ${
              pathname === '/' ? 'bg-[var(--sidebar-active)] text-white font-bold shadow-sm' : 'text-[var(--sidebar-text)] hover:text-white'
            }`}
          >
            الرئيسية
          </Link>
          <Link
            href="/executive"
            onClick={onCloseMobile}
            className={`flex-1 text-center py-1.5 rounded-lg transition-all duration-200 ${
              pathname === '/executive' ? 'bg-[var(--sidebar-active)] text-white font-bold shadow-sm' : 'text-[var(--sidebar-text)] hover:text-white'
            }`}
          >
            التنفيذية
          </Link>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item, idx) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onCloseMobile}
              className={`flex items-center justify-between px-3.5 py-2 rounded-xl font-medium text-xs transition-all duration-200 group animate-slideInFromSide ${
                item.active
                  ? 'bg-[var(--sidebar-active)]/15 text-teal-400 border-r-4 border-[var(--sidebar-active)] font-bold'
                  : 'text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover)] hover:text-slate-200'
              }`}
              style={{ animationDelay: `${idx * 25}ms` }}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 transition-transform duration-200 group-hover:scale-110 ${item.active ? 'text-teal-400' : 'text-[var(--sidebar-text)]'}`} />
                <span>{item.title}</span>
              </div>
              {item.badge && (
                <span className="px-2 py-0.5 text-[10px] font-bold bg-slate-800 text-teal-400 rounded-full border border-slate-700">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-[var(--sidebar-border)] text-xs text-[var(--sidebar-text)] text-center">
        سكون Real Estate v1.0.0
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
