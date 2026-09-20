'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, ChevronLeft } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
}

const ROUTE_LABELS: Record<string, string> = {
  users: 'إدارة المستخدمين',
  suspended: 'الموقوفون والمحظورون',
  kyc: 'التوثيق KYC',
  review: 'المراجعة والاعتماد',
  properties: 'إدارة العقارات',
  moderation: 'مراجعة المحتوى والبلاغات',
  reports: 'التقارير والبلاغات',
  overview: 'نظرة عامة',
  analytics: 'التحليلات والتقارير',
  financials: 'الإيرادات والمالية',
  transactions: 'سجل المعاملات',
  notifications: 'الإشعارات المدفوعة',
  support: 'دعم العملاء والتذاكر',
  roles: 'الأدوار والصلاحيات',
  system: 'إدارة النظام',
  health: 'صحة النظام والخدمات',
  logs: 'سجل الأنشطة والأحداث',
  settings: 'إعدادات المنصة',
  executive: 'لوحة القيادة التنفيذية',
};

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items }) => {
  const pathname = usePathname();

  let breadcrumbs: BreadcrumbItem[] = [];

  if (items && items.length > 0) {
    breadcrumbs = items;
  } else {
    const segments = pathname.split('/').filter(Boolean);
    let currentPath = '';

    breadcrumbs = segments.map((segment) => {
      currentPath += `/${segment}`;
      const label = ROUTE_LABELS[segment] || (segment.startsWith('prop-') ? 'تفاصيل العقار' : segment.length > 10 ? 'تفاصيل السجل' : segment);
      return {
        label,
        href: currentPath,
      };
    });
  }

  if (pathname === '/') return null;

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs font-bold text-[var(--text-subtle)] mb-4 flex-wrap animate-fadeIn">
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-[var(--text-muted)] hover:text-teal-600 dark:hover:text-teal-400 transition-colors"
      >
        <Home className="w-3.5 h-3.5" />
        <span>الرئيسية</span>
      </Link>

      {breadcrumbs.map((item, index) => {
        const isLast = index === breadcrumbs.length - 1;

        return (
          <React.Fragment key={index}>
            <ChevronLeft className="w-3.5 h-3.5 text-[var(--text-subtle)] shrink-0" />
            {isLast || !item.href ? (
              <span className="px-2 py-0.5 rounded-lg bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20 font-extrabold">
                {item.label}
              </span>
            ) : (
              <Link
                href={item.href}
                className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors"
              >
                {item.label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};
