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

export interface SupportTicket {
  id: string;
  subject: string;
  user: string;
  userType: 'مستأجر' | 'مالك';
  priority: 'عالي' | 'متوسط' | 'منخفض';
  status: 'مفتوح' | 'قيد المعالجة' | 'محلول' | 'مغلق';
  timeAgo: string;
  assignedTo?: string;
}

export interface OverviewTicket {
  id: string;
  subject: string;
  reporter: string;
  type: 'خلاف' | 'بلاغ عقار' | 'بلاغ مستخدم';
  status: 'مفتوح' | 'قيد المراجعة' | 'محلول' | 'مغلق';
  reviewer: string;
}

export interface TransactionItem {
  id: string;
  description: string;
  landlord: string;
  tenant: string;
  amount: string;
  isPositive: boolean;
  status: 'مدفوع' | 'معلق' | 'مسترد';
}

export interface ModerationItem {
  id: string;
  title: string;
  reason: string;
  riskLevel: 'عالي' | 'متوسط' | 'منخفض';
  type: 'صور' | 'نصوص';
}

export interface NotificationCampaign {
  id: string;
  title: string;
  timeAgo: string;
  body: string;
  openRate: string;
  recipientCount: string;
}

export interface SystemAuditLog {
  id: string;
  time: string;
  action: string;
  typeBadge: 'KYC' | 'عقار' | 'مستخدم' | 'دور' | 'دعم' | 'بلاغ' | 'نظام';
  target: string;
  operator: string;
}

export interface AdminRoleItem {
  id: string;
  name: string;
  userCount: number;
  badges: string[];
  subtext?: string;
  color: string;
}

export interface AdminUserItem {
  id: string;
  name: string;
  roleName: string;
  timeAgo: string;
  avatarColor: string;
}

export interface PermissionMatrixRow {
  action: string;
  systemOwner: boolean;
  mainAdmin: boolean;
  kycReviewer: boolean;
  propertyReviewer: boolean;
  support: boolean;
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

export const analyticsMetrics = {
  visitRequests: '1,847',
  visitRequestsChange: '+23%',
  completedVisits: '1,204',
  completedVisitsChange: '+15%',
  avgRating: '4.7 ★',
  avgRatingChange: '+0.2',
  retentionRate: '78%',
  retentionRateChange: '-2%',
  topRegions: [
    { name: 'مدينة نصر', count: 380 },
    { name: 'التجمع الخامس', count: 265 },
    { name: 'المهندسين', count: 198 },
    { name: 'المعادي', count: 154 },
  ],
  kycBreakdown: [
    { label: 'موثّق', count: 1920, pct: '67%', color: 'bg-emerald-500' },
    { label: 'معلّق', count: 487, pct: '17%', color: 'bg-amber-500' },
    { label: 'مرفوض', count: 143, pct: '5%', color: 'bg-rose-500' },
    { label: 'جديد (بدون توثيق)', count: 297, pct: '11%', color: 'bg-slate-400' },
  ],
  propertyActivity: [
    { label: 'عرض متاح', count: 890, color: 'bg-emerald-500' },
    { label: 'قيد المراجعة', count: 234, color: 'bg-amber-500' },
    { label: 'مؤجر', count: 512, color: 'bg-blue-600' },
    { label: 'مخفي', count: 67, color: 'bg-slate-400' },
  ],
};

export const moderationMetrics = {
  suspiciousImages: 14,
  misleadingDesc: 8,
  phoneNumInPhotos: 6,
  inappropriateContent: 3,
};

export const mockTransactions: TransactionItem[] = [
  {
    id: 'TXN-8821',
    description: 'إيجار شهري – شقة نصر',
    landlord: 'أحمد محمد',
    tenant: 'سارة أحمد',
    amount: '+6,500 ج',
    isPositive: true,
    status: 'مدفوع',
  },
  {
    id: 'TXN-8820',
    description: 'رسوم توثيق KYC',
    landlord: '–',
    tenant: 'محمد علي',
    amount: '+50 ج',
    isPositive: true,
    status: 'مدفوع',
  },
  {
    id: 'TXN-8819',
    description: 'إيجار – ستوديو تجمع',
    landlord: 'نادر طارق',
    tenant: 'نورا كمال',
    amount: '+4,200 ج',
    isPositive: true,
    status: 'معلق',
  },
  {
    id: 'TXN-8818',
    description: 'استرداد – إلغاء زيارة',
    landlord: '–',
    tenant: 'كريم سالم',
    amount: '-200 ج',
    isPositive: false,
    status: 'مسترد',
  },
];

export const mockModerationItems: ModerationItem[] = [
  {
    id: 'mod-1',
    title: 'شقة مدينة نصر',
    reason: 'رقم هاتف ظاهر في صورة • أحمد محمد',
    riskLevel: 'عالي',
    type: 'صور',
  },
  {
    id: 'mod-2',
    title: 'ستوديو التجمع',
    reason: 'وصف غير دقيق – مساحة مبالغ فيها • نادر طارق',
    riskLevel: 'متوسط',
    type: 'نصوص',
  },
  {
    id: 'mod-3',
    title: 'غرفة المعادي',
    reason: 'صورة غير واضحة • كريم سالم',
    riskLevel: 'منخفض',
    type: 'صور',
  },
];

export const mockPushCampaigns: NotificationCampaign[] = [
  {
    id: 'nc-1',
    title: 'عروض الصيف!',
    timeAgo: 'النهاردة 9:00 ص',
    body: 'احجز زيارتك واستمتع بخصم 20%',
    openRate: '34% فتح',
    recipientCount: '2,847 وصل',
  },
  {
    id: 'nc-2',
    title: 'عقارات جديدة!',
    timeAgo: 'أمس 3:00 م',
    body: 'شقق جديدة في مدينة نصر',
    openRate: '28% فتح',
    recipientCount: '1,924 وصل',
  },
  {
    id: 'nc-3',
    title: 'تذكير توثيق',
    timeAgo: 'قبل 3 أيام',
    body: 'وثّق هويتك وابدأ التواصل',
    openRate: '45% فتح',
    recipientCount: '923 وصل',
  },
];

export const mockAuditLogs: SystemAuditLog[] = [
  {
    id: 'log-1',
    time: '09:41:23',
    action: 'قبول توثيق هوية – سارة أحمد خالد',
    typeBadge: 'KYC',
    target: 'مستأجر',
    operator: 'سلمى رشدي',
  },
  {
    id: 'log-2',
    time: '09:35:10',
    action: 'رفض عقار – كريم سالم فاروق',
    typeBadge: 'عقار',
    target: 'مالك',
    operator: 'أحمد العدل',
  },
  {
    id: 'log-3',
    time: '09:20:04',
    action: 'إيقاف حساب طارق محمد – لغة مسيئة',
    typeBadge: 'مستخدم',
    target: 'مستأجر',
    operator: 'أحمد العدل',
  },
  {
    id: 'log-4',
    time: '09:10:55',
    action: 'تغيير دور دينا حسام ⬅ دعم عملاء',
    typeBadge: 'دور',
    target: 'Admin',
    operator: 'أحمد العدل',
  },
  {
    id: 'log-5',
    time: '08:55:30',
    action: 'حل تذكرة SUP-199 – مشكلة صور',
    typeBadge: 'دعم',
    target: 'مالك',
    operator: 'سلمى رشدي',
  },
  {
    id: 'log-6',
    time: '08:44:18',
    action: 'رفض بلاغ على شقة المعادي – غير مؤكد',
    typeBadge: 'بلاغ',
    target: 'عقار',
    operator: 'كريم فاروق',
  },
  {
    id: 'log-7',
    time: '08:30:00',
    action: 'إرسال إشعار – عروض الصيف 2,847 مستخدم',
    typeBadge: 'نظام',
    target: 'الكل',
    operator: 'أحمد العدل',
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

export const supportMetrics = {
  avgResolutionTime: '4.2h',
  solvedToday: 45,
  inProgress: 18,
  openTickets: 31,
};

export const reportsOverviewMetrics = {
  avgResolutionTime: '4.2 ساعة',
  activeDisputes: 7,
  solvedToday: 18,
  openTickets: 31,
};

export const financialMetrics = {
  totalRevenueMonth: '248,500 ج',
  platformFees: '12,425 ج',
  activeTransactions: '1,203',
  avgRent: '6,200 ج',
};

export const revenueBreakdownData = {
  platformFees: { value: '12,425 ج', percent: 5 },
  managedRentals: { value: '211,225 ج', percent: 85 },
  kycFees: { value: '24,850 ج', percent: 10 },
};

export const sixMonthRevenueTrend = [
  { month: 'أبريل', value: 180000 },
  { month: 'مايو', value: 195000 },
  { month: 'يونيو', value: 210000 },
  { month: 'يوليو', value: 225000 },
  { month: 'أغسطس', value: 238000 },
  { month: 'سبتمبر', value: 248500, isCurrent: true },
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
    email: 'sara@gmail.com',
    status: 'نشط',
    kycStatus: 'قيد المراجعة',
    regDate: '1 يناير 2024',
    phone: '01012345432',
    visitRequests: 3,
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
    id: 'ahmed-farouk',
    name: 'أحمد فاروق إبراهيم',
    type: 'مالك',
    email: 'ahmed.farouk@example.com',
    status: 'نشط',
    kycStatus: 'موثق',
    regDate: '5 مارس 2025',
    phone: '01298765432',
    visitRequests: 14,
    rating: 4.8,
    reportsAgainst: 1,
    lastActive: 'منذ 20 دقيقة',
  },
  {
    id: 'nour-kamal',
    name: 'نورا كمال فؤاد',
    type: 'مستأجر',
    email: 'noura.k@example.com',
    status: 'نشط',
    kycStatus: 'قيد المراجعة',
    regDate: '18 فبراير 2026',
    phone: '01511223344',
    visitRequests: 6,
    rating: 4.6,
    reportsAgainst: 0,
    lastActive: 'منذ ساعتين',
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
    id: 'hassan-monir',
    name: 'حسن منير عبدالفتاح',
    type: 'مالك',
    email: 'hassan.m@example.com',
    status: 'موقوف',
    kycStatus: 'قيد المراجعة',
    regDate: '22 أبريل 2025',
    suspensionReason: 'إدخال بيانت مضللة',
    suspendedDate: '14 أغسطس',
    suspendedBy: 'كريم فاروق',
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
  },
  {
    id: 'prop-2',
    title: 'ستوديو مودرن، التجمع الخامس',
    owner: 'نادر طارق',
    type: 'ستوديو',
    status: 'قيد المراجعة',
    price: '8,500 ج',
    views: 310,
    imagesCount: 3,
    time: 'منذ 4 ساعات',
    riskLevel: 'متوسط الخطر',
    area: '55 م²',
    rooms: 1,
    createdDate: '10 سبتمبر 2026',
    lastUpdated: 'منذ ساعة',
  },
  {
    id: 'prop-3',
    title: 'غرفة خاصة بحمام، المعادي',
    owner: 'محمود حسن علي',
    type: 'غرفة',
    status: 'مقبول',
    price: '4,200 ج',
    views: 890,
    imagesCount: 8,
    time: 'منذ يومين',
    riskLevel: 'منخفض الخطر',
    area: '30 م²',
    rooms: 1,
    createdDate: '15 أغسطس 2026',
    lastUpdated: 'أمس',
  },
  {
    id: 'prop-4',
    title: 'فيلا فاخرة بمسبح، الشروق',
    owner: 'أحمد فاروق إبراهيم',
    type: 'فيلا',
    status: 'مرفوض',
    price: '35,000 ج',
    views: 140,
    imagesCount: 2,
    time: 'منذ 3 أيام',
    riskLevel: 'عالي الخطر',
    area: '350 م²',
    rooms: 5,
    createdDate: '12 سبتمبر 2026',
    lastUpdated: 'منذ 3 أيام',
  },
];

export const mockSupportTickets: SupportTicket[] = [
  {
    id: 'SUP-201',
    subject: 'مشكلة في تأكيد الزيارة',
    user: 'سارة أحمد',
    userType: 'مستأجر',
    priority: 'عالي',
    status: 'مفتوح',
    timeAgo: 'منذ 1 ساعة',
    assignedTo: 'دينا حسام',
  },
  {
    id: 'SUP-202',
    subject: 'استفسار عن طريقة الدفع والعمولة',
    user: 'محمود حسن',
    userType: 'مالك',
    priority: 'متوسط',
    status: 'قيد المعالجة',
    timeAgo: 'منذ 3 ساعات',
    assignedTo: 'سلمى رشدي',
  },
  {
    id: 'SUP-203',
    subject: 'تأخير في توثيق الهوية الوطنية',
    user: 'نورا كمال',
    userType: 'مستأجر',
    priority: 'منخفض',
    status: 'محلول',
    timeAgo: 'منذ يوم',
    assignedTo: 'أحمد العدل',
  },
];

export const mockOverviewTickets: OverviewTicket[] = [
  {
    id: 'TKT-0081',
    subject: 'مالك رفض رد الأمانة',
    reporter: 'سارة أحمد',
    type: 'خلاف',
    status: 'مفتوح',
    reviewer: 'أحمد العدل',
  },
  {
    id: 'TKT-0082',
    subject: 'معلومات عقار مضللة وغير دقيقة',
    reporter: 'محمود حسن',
    type: 'بلاغ عقار',
    status: 'قيد المراجعة',
    reviewer: 'سلمى رشدي',
  },
];

export const disputeReasonsData = [
  { title: 'رد الأمانة', count: 12, color: 'bg-rose-500' },
  { title: 'دقة المعلومات', count: 8, color: 'bg-amber-500' },
  { title: 'إلغاء الزيارة', count: 6, color: 'bg-blue-500' },
  { title: 'التواصل', count: 5, color: 'bg-teal-500' },
];

export const bookingLogData = [
  { id: 'BK-441', title: 'شقة نصر', status: 'مكتمل' },
  { id: 'BK-440', title: 'ستوديو تجمع', status: 'ملغي' },
  { id: 'BK-439', title: 'غرفة معادي', status: 'مكتمل' },
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
    user: 'أحمد فاروق إبراهيم',
    type: 'مالك',
    nationalIdMask: '28...45',
    waitTime: '45 دقيقة',
    status: 'مقبول',
  },
  {
    id: 'kyc-3',
    user: 'نورا كمال فؤاد',
    type: 'مستأجر',
    nationalIdMask: '30...88',
    waitTime: '5 ساعات',
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
    reportedUser: 'حسن منير عبدالفتاح',
    userType: 'مالك',
    reason: 'معلومات غير مطابقة',
    reporter: 'نورا كمال',
    date: 'منذ 3 ساعات',
    automationLevel: 'تلقائي',
    status: 'موقوف مؤقتاً',
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

export const mockAdminRoles: AdminRoleItem[] = [
  {
    id: 'role-1',
    name: 'مالك النظام',
    userCount: 1,
    badges: [],
    subtext: 'كل الصلاحيات',
    color: 'bg-emerald-500',
  },
  {
    id: 'role-2',
    name: 'مشرف رئيسي',
    userCount: 2,
    badges: ['KYC', 'عقارات', 'مستخدمون', 'تقارير'],
    color: 'bg-blue-500',
  },
  {
    id: 'role-3',
    name: 'مراجع KYC',
    userCount: 3,
    badges: ['فقط KYC'],
    color: 'bg-emerald-500',
  },
  {
    id: 'role-4',
    name: 'مراجع عقارات',
    userCount: 2,
    badges: ['عقارات فقط'],
    color: 'bg-amber-500',
  },
  {
    id: 'role-5',
    name: 'دعم العملاء',
    userCount: 4,
    badges: ['تذاكر دعم'],
    color: 'bg-slate-400',
  },
];

export const mockAdminUsers: AdminUserItem[] = [
  {
    id: 'admin-1',
    name: 'أحمد العدل',
    roleName: 'مشرف رئيسي',
    timeAgo: 'الآن',
    avatarColor: 'bg-blue-100 text-blue-600',
  },
  {
    id: 'admin-2',
    name: 'سلمى رشدي',
    roleName: 'مراجع KYC',
    timeAgo: 'منذ 5 دقائق',
    avatarColor: 'bg-emerald-100 text-emerald-600',
  },
  {
    id: 'admin-3',
    name: 'كريم فاروق',
    roleName: 'مراجع عقارات',
    timeAgo: 'أمس',
    avatarColor: 'bg-amber-100 text-amber-600',
  },
  {
    id: 'admin-4',
    name: 'دينا حسام',
    roleName: 'دعم العملاء',
    timeAgo: 'منذ 20 دقيقة',
    avatarColor: 'bg-slate-100 text-slate-600',
  },
];

export const mockPermissionsMatrix: PermissionMatrixRow[] = [
  {
    action: 'مراجعة KYC',
    systemOwner: true,
    mainAdmin: true,
    kycReviewer: true,
    propertyReviewer: false,
    support: false,
  },
  {
    action: 'قبول/رفض عقارات',
    systemOwner: true,
    mainAdmin: true,
    kycReviewer: false,
    propertyReviewer: true,
    support: false,
  },
  {
    action: 'إيقاف مستخدم',
    systemOwner: true,
    mainAdmin: true,
    kycReviewer: false,
    propertyReviewer: false,
    support: false,
  },
  {
    action: 'حل التذاكر',
    systemOwner: true,
    mainAdmin: true,
    kycReviewer: false,
    propertyReviewer: false,
    support: true,
  },
  {
    action: 'تعديل الأدوار',
    systemOwner: true,
    mainAdmin: false,
    kycReviewer: false,
    propertyReviewer: false,
    support: false,
  },
];

export const mockSystemHealthMetrics = {
  uptime: '99.8%',
  uptimeSub: 'آخر 30 يوم',
  responseTime: '142ms',
  responseSub: 'متوسط API',
  errorsToday: '3',
  errorsSub: 'أخطاء 5xx',
  dbStatus: 'طبيعي',
  dbSub: 'اتصال مستقر',
};

export const mockApiPerformanceData = [
  { hour: '12:00', ms: 120, height: '40%' },
  { hour: '12:05', ms: 140, height: '55%' },
  { hour: '12:10', ms: 180, height: '80%' },
  { hour: '12:15', ms: 135, height: '50%' },
  { hour: '12:20', ms: 210, height: '95%' },
  { hour: '12:25', ms: 160, height: '70%' },
  { hour: '12:30', ms: 142, height: '58%' },
  { hour: '12:35', ms: 175, height: '75%' },
  { hour: '12:40', ms: 130, height: '48%' },
  { hour: '12:45', ms: 150, height: '62%' },
  { hour: '12:50', ms: 195, height: '88%' },
  { hour: '12:55', ms: 142, height: '58%' },
];

export const mockInternalAdminNotes = [
  'قاعدة البيانات تعمل بكفاءة 99.8%',
  'خادم CDN مستقر – لا توجد مشاكل',
  'النسخ الاحتياطي اليومي: مكتمل 03:00',
  'تحديث الأمان القادم: الأحد 2:00 ص',
];

