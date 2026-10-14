import {
  LayoutDashboard, ChartNoAxesCombined, Gauge, Building2, ClipboardCheck,
  Users, ShieldCheck, UserRoundX, ShieldAlert, Flag, Headphones, Files,
  Wallet, ArrowLeftRight, Megaphone, Settings2, KeyRound, History, Activity,
  type LucideIcon,
} from 'lucide-react';

export interface AdminNavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  description: string;
  count?: 'kyc' | 'properties' | 'support';
}
export interface AdminNavGroup {
  id: string;
  title: string;
  items: AdminNavItem[];
}

export const adminNavigation: AdminNavGroup[] = [
  { id: 'overview', title: 'نظرة عامة', items: [
    { title: 'ملخص المنصة', href: '/', icon: LayoutDashboard, description: 'الأداء، المراجعات، وآخر الأنشطة' },
    { title: 'التقرير التنفيذي', href: '/executive', icon: Gauge, description: 'مؤشرات الإدارة وأداء المنصة' },
    { title: 'التحليلات', href: '/analytics', icon: ChartNoAxesCombined, description: 'النمو وسلوك المستخدمين' },
  ] },
  { id: 'properties', title: 'العقارات', items: [
    { title: 'جميع العقارات', href: '/properties', icon: Building2, description: 'إدارة الإعلانات وتفاصيل العقارات' },
    { title: 'طلبات المراجعة', href: '/properties/review', icon: ClipboardCheck, description: 'اعتماد العقارات الجديدة', count: 'properties' },
  ] },
  { id: 'community', title: 'المستخدمون والتوثيق', items: [
    { title: 'جميع المستخدمين', href: '/users', icon: Users, description: 'حسابات الملاك والمستأجرين' },
    { title: 'توثيق الهوية', href: '/kyc', icon: ShieldCheck, description: 'مراجعة مستندات التوثيق KYC', count: 'kyc' },
    { title: 'الحسابات الموقوفة', href: '/users/suspended', icon: UserRoundX, description: 'الإيقاف والحظر ورفع القيود' },
  ] },
  { id: 'trust', title: 'السلامة والدعم', items: [
    { title: 'مراجعة المحتوى', href: '/moderation', icon: ShieldAlert, description: 'متابعة سلامة المحتوى المنشور' },
    { title: 'بلاغات المستخدمين', href: '/users/reports', icon: Flag, description: 'البلاغات والمخالفات' },
    { title: 'دعم العملاء', href: '/support', icon: Headphones, description: 'التذاكر والمحادثات المفتوحة', count: 'support' },
    { title: 'متابعة البلاغات', href: '/reports/overview', icon: Files, description: 'حالات البلاغات وتسويتها' },
  ] },
  { id: 'business', title: 'المالية والتواصل', items: [
    { title: 'الإيرادات', href: '/financials', icon: Wallet, description: 'الإيرادات والرسوم وأداء الأعمال' },
    { title: 'المعاملات', href: '/financials/transactions', icon: ArrowLeftRight, description: 'المدفوعات وسجل المعاملات' },
    { title: 'حملات الإشعارات', href: '/notifications', icon: Megaphone, description: 'إدارة الحملات والتواصل' },
  ] },
  { id: 'platform', title: 'إدارة المنصة', items: [
    { title: 'الفريق والصلاحيات', href: '/roles', icon: KeyRound, description: 'أدوار المشرفين وصلاحيات الوصول' },
    { title: 'سجل النشاط', href: '/system/logs', icon: History, description: 'الإجراءات والأحداث المسجلة' },
    { title: 'صحة النظام', href: '/system/health', icon: Activity, description: 'الخدمات وحالة التشغيل' },
    { title: 'الإعدادات', href: '/settings', icon: Settings2, description: 'ضوابط وإعدادات المنصة' },
  ] },
];

export function activeAdminHref(pathname: string): string | undefined {
  return adminNavigation.flatMap((group) => group.items)
    .filter((item) => item.href === '/' ? pathname === '/' : pathname === item.href || pathname.startsWith(`${item.href}/`))
    .sort((a, b) => b.href.length - a.href.length)[0]?.href;
}

export function findAdminSection(pathname: string) {
  const href = activeAdminHref(pathname);
  return adminNavigation.find((group) => group.items.some((item) => item.href === href));
}

export function searchAdminNavigation(query: string) {
  const normalize = (value: string) => value.toLowerCase().normalize('NFKD').replace(/[\u064B-\u065F\u0670]/g, '').replace(/[أإآ]/g, 'ا').trim();
  const term = normalize(query);
  return adminNavigation.flatMap((group) => group.items.map((item) => ({ ...item, group: group.title })))
    .filter((item) => normalize(`${item.title} ${item.description} ${item.group}`).includes(term));
}
