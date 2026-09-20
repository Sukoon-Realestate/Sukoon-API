export interface DashboardMetric {
  title: string;
  value: string;
  change: string;
  isPositive: boolean;
  icon: 'users' | 'building' | 'clock' | 'revenue' | 'calendar' | 'alert';
}

export interface ActivityItem {
  id: string;
  title: string;
  time: string;
  role?: string;
  roleType?: 'tenant' | 'landlord' | 'property' | 'admin';
  iconType: 'check' | 'alert' | 'building' | 'user' | 'shield';
}

export interface UserItem {
  id: string;
  name: string;
  type: 'مستأجر' | 'مالك';
  email: string;
  status: 'نشط' | 'قيد المراجعة' | 'موقوف';
  kycStatus: 'موثق' | 'قيد المراجعة' | 'مرفوض';
  regDate: string;
  phone?: string;
  visitRequests?: number;
  rating?: number;
  reportsAgainst?: number;
  lastActive?: string;
  activityLog?: Array<{
    id: string;
    title: string;
    time: string;
    type: 'visit' | 'kyc' | 'message' | 'saved';
  }>;
}

export interface ReportItem {
  id: string;
  reportedUser: string;
  userType: 'مالك' | 'مستأجر';
  reason: string;
  reporter: string;
  date: string;
  automationLevel: 'عالي' | 'تلقائي' | 'منخفض';
  status: 'نشط' | 'موقوف مؤقتاً' | 'محظور نهائياً';
}

export const overviewMetrics: DashboardMetric[] = [
  {
    title: 'إجمالي المستخدمين',
    value: '2,847',
    change: '+12%',
    isPositive: true,
    icon: 'users',
  },
  {
    title: 'عقارات نشطة',
    value: '1,203',
    change: '+8%',
    isPositive: true,
    icon: 'building',
  },
  {
    title: 'توثيق معلق',
    value: '487',
    change: '-5%',
    isPositive: false,
    icon: 'clock',
  },
  {
    title: 'إيرادات المنصة',
    value: '89,400 ج',
    change: '+21%',
    isPositive: true,
    icon: 'revenue',
  },
];

export const executiveMetrics: DashboardMetric[] = [
  {
    title: 'المستخدمون النشطون',
    value: '2,847',
    change: '+12%',
    isPositive: true,
    icon: 'users',
  },
  {
    title: 'عقارات نشطة',
    value: '1,203',
    change: '+8%',
    isPositive: true,
    icon: 'building',
  },
  {
    title: 'طلبات الزيارة اليوم',
    value: '143',
    change: '+23%',
    isPositive: true,
    icon: 'calendar',
  },
  {
    title: 'توثيق معلق',
    value: '487',
    change: '-5%',
    isPositive: false,
    icon: 'clock',
  },
  {
    title: 'بلاغات مفتوحة',
    value: '31',
    change: '+7%',
    isPositive: true,
    icon: 'alert',
  },
];

export const userDistributionData = {
  total: 2847,
  tenants: 1924,
  landlords: 923,
  verified: 1920,
  pending: 487,
  suspended: 43,
};

export const mainRecentActivities: ActivityItem[] = [
  {
    id: 'act-1',
    title: 'سارة أحمد أرسلت طلب توثيق',
    time: 'منذ 5 دقائق',
    iconType: 'check',
  },
  {
    id: 'act-2',
    title: 'عقار جديد في مدينة نصر بانتظار المراجعة',
    time: 'منذ 12 دقيقة',
    iconType: 'building',
  },
  {
    id: 'act-3',
    title: 'محمد علي أنشأ حساباً جديداً كمستأجر',
    time: 'منذ 20 دقيقة',
    iconType: 'user',
  },
  {
    id: 'act-4',
    title: 'تم اعتماد توثيق محمود حسن',
    time: 'منذ 35 دقيقة',
    iconType: 'check',
  },
];

export const executiveRecentActivities: ActivityItem[] = [
  {
    id: 'eact-1',
    title: 'تم قبول توثيق سارة أحمد خالد',
    time: 'منذ 2 دقيقة',
    role: 'مستأجر',
    roleType: 'tenant',
    iconType: 'check',
  },
  {
    id: 'eact-2',
    title: 'بلاغ جديد على ستوديو التجمع الخامس',
    time: 'منذ 8 دقائق',
    role: 'عقار',
    roleType: 'property',
    iconType: 'alert',
  },
  {
    id: 'eact-3',
    title: 'عقار جديد بانتظار المراجعة - مدينة نصر',
    time: 'منذ 15 دقيقة',
    role: 'مالك',
    roleType: 'landlord',
    iconType: 'building',
  },
  {
    id: 'eact-4',
    title: 'تسجيل مستخدم جديد: محمد طارق (مستأجر)',
    time: 'منذ 22 دقيقة',
    role: 'مستأجر',
    roleType: 'tenant',
    iconType: 'user',
  },
  {
    id: 'eact-5',
    title: 'تغيير صلاحية: سلمى رشدي ⬅ مراجع كبير',
    time: 'منذ 45 دقيقة',
    role: 'Admin',
    roleType: 'admin',
    iconType: 'shield',
  },
];

export const mockUsers: UserItem[] = [
  {
    id: 'sara-ahmed',
    name: 'سارة أحمد خالد',
    type: 'مستأجر',
    email: 'sara@example.com',
    status: 'نشط',
    kycStatus: 'موثق',
    regDate: '14 يناير 2026',
    phone: '01012345432',
    visitRequests: 12,
    rating: 4.7,
    reportsAgainst: 0,
    lastActive: 'منذ 5 دقائق',
    activityLog: [
      { id: 'al-1', title: 'حجز زيارة – شقة مدينة نصر', time: 'اليوم 9:30 ص', type: 'visit' },
      { id: 'al-2', title: 'تم توثيق الهوية', time: 'أمس 3:00 م', type: 'kyc' },
      { id: 'al-3', title: 'إرسال رسالة للمالك أحمد', time: 'أمس 2:45 م', type: 'message' },
      { id: 'al-4', title: 'حفظ عقار ستوديو التجمع', time: 'الأحد 10:00 ص', type: 'saved' },
    ],
  },
  {
    id: 'mahmoud-hassan',
    name: 'محمود حسن علي',
    type: 'مالك',
    email: 'mahmoud@example.com',
    status: 'نشط',
    kycStatus: 'موثق',
    regDate: '12 يناير 2026',
    phone: '01123456789',
    visitRequests: 28,
    rating: 4.9,
    reportsAgainst: 0,
    lastActive: 'منذ ساعة',
  },
  {
    id: 'noura-mohamed',
    name: 'نورا محمد عمر',
    type: 'مستأجر',
    email: 'noura@example.com',
    status: 'نشط',
    kycStatus: 'قيد المراجعة',
    regDate: '10 يناير 2026',
    phone: '01298765432',
    visitRequests: 5,
    rating: 4.5,
    reportsAgainst: 1,
    lastActive: 'منذ 3 ساعات',
  },
  {
    id: 'karim-tarek',
    name: 'كريم طارق سالم',
    type: 'مالك',
    email: 'karim@example.com',
    status: 'موقوف',
    kycStatus: 'مرفوض',
    regDate: '8 يناير 2026',
    phone: '01511223344',
    visitRequests: 2,
    rating: 3.2,
    reportsAgainst: 4,
    lastActive: 'منذ يومين',
  },
];

export const mockReports: ReportItem[] = [
  {
    id: 'rep-1',
    reportedUser: 'كريم طارق سالم',
    userType: 'مالك',
    reason: 'احتيال محتمل',
    reporter: 'سارة أحمد',
    date: 'منذ 1 ساعة',
    automationLevel: 'عالي',
    status: 'نشط',
  },
  {
    id: 'rep-2',
    reportedUser: 'محمود حسن',
    userType: 'مستأجر',
    reason: 'لغة مسيئة',
    reporter: 'النظام الآلي',
    date: 'منذ 3 ساعات',
    automationLevel: 'تلقائي',
    status: 'نشط',
  },
  {
    id: 'rep-3',
    reportedUser: 'نورا عمر',
    userType: 'مستأجر',
    reason: 'معلومات مضللة',
    reporter: 'خالد فاروق',
    date: 'منذ 5 ساعات',
    automationLevel: 'منخفض',
    status: 'نشط',
  },
  {
    id: 'rep-4',
    reportedUser: 'طارق محمد',
    userType: 'مالك',
    reason: 'رقم هاتف ظاهر',
    reporter: 'النظام الآلي',
    date: 'أمس',
    automationLevel: 'تلقائي',
    status: 'نشط',
  },
];

export const monthlyUserChartData = [
  { day: 1, value: 35 },
  { day: 3, value: 48 },
  { day: 6, value: 30 },
  { day: 9, value: 65 },
  { day: 12, value: 42 },
  { day: 15, value: 85 },
  { day: 18, value: 55 },
  { day: 21, value: 92 },
  { day: 24, value: 78 },
  { day: 27, value: 88 },
  { day: 30, value: 105, isCurrent: true },
];

export const reportTrendData = [
  { day: 1, value: 12 },
  { day: 3, value: 15 },
  { day: 6, value: 10 },
  { day: 9, value: 22 },
  { day: 12, value: 18 },
  { day: 15, value: 25 },
  { day: 18, value: 14 },
  { day: 21, value: 28 },
  { day: 24, value: 32 },
  { day: 27, value: 29 },
  { day: 30, value: 31, isCurrent: true },
];
