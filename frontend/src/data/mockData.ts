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
  status: 'نشط' | 'قيد المراجعة' | 'موقوف' | 'محظور';
  kycStatus: 'موثق' | 'قيد المراجعة' | 'مرفوض';
  regDate: string;
  phone?: string;
  visitRequests?: number;
  rating?: number;
  reportsAgainst?: number;
  lastActive?: string;
  suspensionReason?: string;
  suspendedBy?: string;
  suspendedDate?: string;
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

export interface PropertyItem {
  id: string;
  title: string;
  owner: string;
  type: 'شقة' | 'ستوديو' | 'غرفة' | 'فيلا';
  status: 'مقبول' | 'قيد المراجعة' | 'مرفوض';
  price: string;
  views: number;
  imagesCount?: number;
  time?: string;
  riskLevel?: 'عالي الخطر' | 'متوسط الخطر' | 'منخفض الخطر';
  area?: string;
  rooms?: number;
  createdDate?: string;
  lastUpdated?: string;
  auditLogs?: Array<{
    title: string;
    date: string;
    actor: string;
    status: 'accepted' | 'pending' | 'sent';
  }>;
}

export interface KycRequest {
  id: string;
  user: string;
  type: 'مستأجر' | 'مالك';
  nationalIdMask: string;
  waitTime: string;
  hasWarning?: boolean;
  status: 'انتظار المراجعة' | 'مقبول' | 'مرفوض';
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

export const propertyMetrics = {
  total: 1203,
  active: 890,
  pending: 234,
  rejected: 79,
  openReports: 31,
  rejectedToday: 12,
  acceptedToday: 89,
};

export const suspendedUsersMetrics = {
  tempSuspended: 43,
  permanentlyBanned: 12,
  pendingDecision: 8,
};

export const kycMetrics = {
  pendingReview: 487,
  reviewedToday: 124,
  acceptedToday: 108,
  rejectedToday: 16,
};

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

export const mockSuspendedUsers: UserItem[] = [
  {
    id: 'tarek-mohamed',
    name: 'طارق محمد علي',
    type: 'مستأجر',
    email: 'tarek@example.com',
    status: 'موقوف',
    kycStatus: 'قيد المراجعة',
    regDate: '3 مايو 2025',
    suspensionReason: 'لغة مسيئة',
    suspendedDate: '3 يونيو',
    suspendedBy: 'أحمد العدل',
  },
  {
    id: 'karim-salem',
    name: 'كريم سالم',
    type: 'مالك',
    email: 'karim.s@example.com',
    status: 'محظور',
    kycStatus: 'مرفوض',
    regDate: '15 يناير 2025',
    suspensionReason: 'احتيال',
    suspendedDate: '10 يونيو',
    suspendedBy: 'سلمى رشدي',
  },
  {
    id: 'hoda-mahmoud',
    name: 'هدى محمود',
    type: 'مستأجر',
    email: 'hoda@example.com',
    status: 'موقوف',
    kycStatus: 'قيد المراجعة',
    regDate: '20 فبراير 2025',
    suspensionReason: 'معلومات مضللة',
    suspendedDate: '28 مايو',
    suspendedBy: 'أحمد العدل',
  },
];

export const mockProperties: PropertyItem[] = [
  {
    id: 'prop-1',
    title: 'شقة مفروشة، مدينة نصر',
    owner: 'أحمد محمد إبراهيم',
    type: 'شقة',
    status: 'مقبول',
    price: '12,000 ج',
    views: 540,
    imagesCount: 6,
    time: 'منذ 2 ساعة',
    riskLevel: 'عالي الخطر',
    area: '90 م²',
    rooms: 3,
    createdDate: '1 مايو 2025',
    lastUpdated: 'اليوم',
    auditLogs: [
      { title: 'تم قبول العقار', date: '1 مايو 9:30 ص', actor: 'أحمد العدل', status: 'accepted' },
      { title: 'مراجعة أولية آلية – لم تُكتشف مشاكل', date: '1 مايو 9:20 ص', actor: 'النظام', status: 'pending' },
      { title: 'إرسال العقار من المالك', date: '1 مايو 9:00 ص', actor: 'أحمد محمد', status: 'sent' },
    ],
  },
  {
    id: 'prop-2',
    title: 'ستوديو، التجمع الخامس',
    owner: 'منى علي',
    type: 'ستوديو',
    status: 'قيد المراجعة',
    price: '7,500 ج',
    views: 0,
    imagesCount: 4,
    time: 'منذ 4 ساعات',
    riskLevel: 'متوسط الخطر',
    area: '60 م²',
    rooms: 1,
    createdDate: '3 مايو 2025',
    lastUpdated: 'منذ 4 ساعات',
  },
  {
    id: 'prop-3',
    title: 'غرفة، المعادي',
    owner: 'كريم سالم',
    type: 'غرفة',
    status: 'مرفوض',
    price: '4,000 ج',
    views: 120,
    imagesCount: 9,
    time: 'منذ 6 ساعات',
    riskLevel: 'منخفض الخطر',
    area: '25 م²',
    rooms: 1,
    createdDate: '28 أبريل 2025',
    lastUpdated: 'منذ يوم',
  },
  {
    id: 'prop-4',
    title: 'شقة، المهندسين',
    owner: 'نادر طارق',
    type: 'شقة',
    status: 'مقبول',
    price: '15,000 ج',
    views: 325,
    imagesCount: 3,
    time: 'منذ يوم',
    riskLevel: 'عالي الخطر',
    area: '140 م²',
    rooms: 3,
    createdDate: '10 أبريل 2025',
    lastUpdated: 'أمس',
  },
];

export const propertyVerificationChecklist = [
  { id: 'c1', title: 'صور واضحة (9-10 صور)', passed: false },
  { id: 'c2', title: 'عنوان العقار مكتمل', passed: true },
  { id: 'c3', title: 'السعر منطقي للمنطقة', passed: true },
  { id: 'c4', title: 'لا يوجد رقم هاتف في الصور', passed: false },
  { id: 'c5', title: 'وصف غير مضلل', passed: true },
  { id: 'c6', title: 'بيانات المالك موثقة', passed: true },
  { id: 'c7', title: 'الموقع الجغرافي صحيح', passed: true },
];

export const propertyRiskFlags = [
  'رقم هاتف محتمل في صورة 3',
  'عدد الصور أقل من المطلوب',
];

export const mockKycRequests: KycRequest[] = [
  {
    id: 'kyc-1',
    user: 'سارة أحمد خالد',
    type: 'مستأجر',
    nationalIdMask: '29...12',
    waitTime: '2 ساعة',
    status: 'انتظار المراجعة',
  },
  {
    id: 'kyc-2',
    user: 'أحمد محمد إبراهيم',
    type: 'مالك',
    nationalIdMask: '28...34',
    waitTime: '4 ساعات',
    hasWarning: true,
    status: 'انتظار المراجعة',
  },
  {
    id: 'kyc-3',
    user: 'نورا عمر طارق',
    type: 'مستأجر',
    nationalIdMask: '30...56',
    waitTime: '6 ساعات',
    status: 'انتظار المراجعة',
  },
  {
    id: 'kyc-4',
    user: 'كريم سالم فاروق',
    type: 'مالك',
    nationalIdMask: '27...78',
    waitTime: '8 ساعات',
    status: 'انتظار المراجعة',
  },
  {
    id: 'kyc-5',
    user: 'منى حسام علي',
    type: 'مستأجر',
    nationalIdMask: '29...90',
    waitTime: 'يوم',
    hasWarning: true,
    status: 'انتظار المراجعة',
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
