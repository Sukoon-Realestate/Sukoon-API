export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface DashboardMetric {
  title: string;
  value: string;
  change: string;
  isPositive: boolean;
  icon: 'users' | 'building' | 'clock' | 'alert' | 'calendar' | 'revenue';
}

export interface UserDistribution {
  total: number;
  tenants: number;
  landlords: number;
  verified: number;
  pending: number;
  suspended: number;
}

export interface ActivityItem {
  id: string;
  title: string;
  time: string;
  role?: string;
  roleType?: 'tenant' | 'landlord' | 'property' | 'admin';
  iconType: 'check' | 'alert' | 'building' | 'user' | 'shield';
}

export interface DashboardStatsResponse {
  metrics: DashboardMetric[];
  user_distribution: UserDistribution;
  chart_data: Array<{ label: string; value: number }>;
  recent_activities: ActivityItem[];
}

export interface ExecutiveDashboardStats {
  executiveMetrics: DashboardMetric[];
  monthlyUserChartData: Array<{ day: number; value: number; isCurrent?: boolean }>;
  reportTrendData: Array<{ day: number; value: number; isCurrent?: boolean }>;
  userDistribution: UserDistribution;
  executiveActivities: ActivityItem[];
}

export interface PlatformSettings {
  maxReviewHours: boolean;
  tenantDocsRequired: boolean;
  landlordDocsRequired: boolean;
  autoVerification: boolean;
  maxPhotosLimit: boolean;
  reviewPeriodDays: boolean;
  approxLocation: boolean;
  hidePhoneDefault: boolean;
}

export interface UserItem {
  id: string;
  name: string;
  first_name?: string;
  last_name?: string;
  email: string;
  type: 'مستأجر' | 'مالك';
  status: 'نشط' | 'قيد المراجعة' | 'موقوف' | 'محظور';
  kycStatus: 'موثق' | 'قيد المراجعة' | 'مرفوض';
  regDate: string;
  phone?: string;
  national_id?: string;
  avatar?: string | null;
  visitRequests?: number;
  properties_count?: number;
  reportsAgainst?: number;
  is_active?: boolean;
  is_verified?: boolean;
  activityLog?: Array<{
    id: string;
    title: string;
    time: string;
    type: 'visit' | 'kyc' | 'message' | 'saved';
  }>;
}

export interface KycRequest {
  id: string;
  user: string;
  userId?: string;
  type: 'مستأجر' | 'مالك';
  nationalIdMask: string;
  waitTime: string;
  status: 'pending' | 'approved' | 'rejected';
  statusDisplay: string;
  hasWarning?: boolean;
  created_at?: string;
}

export interface KycMetrics {
  pendingReview: number;
  acceptedToday: number;
  rejectedToday: number;
  reviewedToday: number;
}

export interface KycDetail {
  id: string;
  user_id: string;
  userName: string;
  userEmail: string;
  userPhone: string;
  userType: 'مستأجر' | 'مالك';
  nationalId: string;
  birthDate: string;
  gender: string;
  idFaceUrl: string | null;
  idBackUrl: string | null;
  selfieUrl: string | null;
  status: string;
  statusDisplay: string;
  submittedAt: string;
  rejectionReason: string;
  reviewedBy: string | null;
  reviewedAt: string | null;
}

export interface ReportItem {
  id: string;
  reportedUser: string;
  reportedUserId: string;
  userType: 'مالك' | 'مستأجر';
  reason: string;
  reason_type?: string;
  reporter: string;
  date: string;
  automation_level: 'high' | 'auto' | 'low';
  automationLevelDisplay: string;
  status: string;
  statusDisplay: string;
  notes?: string;
}

export interface AdminRoleItem {
  id: string;
  name: string;
  subtext?: string;
  userCount: number;
  color: string;
  badges?: string[];
}

export interface AdminUserItem {
  id: string;
  name: string;
  email: string;
  roleName: string;
  display_role?: string;
  timeAgo: string;
  avatarColor: string;
  is_active?: boolean;
}

export interface PermissionsMatrixRow {
  id: string;
  action?: string;
  name?: string;
  desc?: string;
  systemOwner?: boolean;
  mainAdmin?: boolean;
  kycReviewer?: boolean;
  propertyReviewer?: boolean;
  support?: boolean;
  superAdmin?: boolean;
  complianceOfficer?: boolean;
  supportRep?: boolean;
  contentModerator?: boolean;
  [key: string]: any;
}

export interface PropertyItem {
  id: string;
  title: string;
  owner?: string;
  owner_id?: string;
  owner_name?: string;
  owner_email?: string;
  price: number | string;
  price_period?: string;
  type: string;
  property_type?: string;
  location?: string;
  city?: string;
  governorate?: string;
  district?: string;
  bedrooms?: number;
  bathrooms?: number;
  area?: number | string;
  views?: number;
  time?: string;
  imagesCount?: number;
  riskLevel?: string;
  status: string;
  is_verified: boolean;
  is_furnished?: boolean;
  main_image?: string | null;
  image?: string | null;
  created_at?: string;
}

export interface PropertyMetrics {
  total: number;
  active: number;
  pending: number;
  rejected: number;
  acceptedToday: number;
  rejectedToday: number;
  openReports: number;
}

export interface PropertyDetail {
  id: string;
  title: string;
  description: string;
  price: string;
  price_raw: number;
  price_period: string;
  type: string;
  property_type_slug: string;
  status: string;
  status_raw: string;
  is_verified: boolean;
  owner: string;
  owner_id: string;
  owner_email: string;
  owner_phone: string;
  governorate: string;
  city: string;
  district: string;
  location: string;
  area: string;
  rooms: number;
  bathrooms: number;
  floor: number;
  views: number;
  visits: number;
  reports: number;
  riskLevel: string;
  imagesCount: number;
  images: string[];
  createdDate: string;
  lastUpdated: string;
}

export interface ModerationItem {
  id: string;
  rawId?: string;
  property_id?: string;
  title: string;
  reason: string;
  riskLevel: 'عالي' | 'متوسط' | 'منخفض';
  type: 'صور' | 'نصوص';
}

export interface ModerationMetrics {
  suspiciousImages: number;
  misleadingDesc: number;
  phoneNumInPhotos: number;
  inappropriateContent: number;
}

export interface SupportTicket {
  id: string;
  rawId?: string;
  subject: string;
  user: string;
  userType: 'مستأجر' | 'مالك';
  priority: 'عالي' | 'متوسط' | 'منخفض';
  status: 'مفتوح' | 'قيد المعالجة' | 'محلول' | 'مغلق';
  statusRaw?: string;
  timeAgo: string;
  assignedTo?: string;
  notes?: string;
}

export interface SupportMetrics {
  avgResolutionTime: string;
  solvedToday: number;
  inProgress: number;
  openTickets: number;
}

export interface OverviewTicket {
  id: string;
  rawId?: string;
  subject: string;
  reporter: string;
  type: 'خلاف' | 'بلاغ عقار' | 'بلاغ مستخدم';
  status: 'مفتوح' | 'قيد المراجعة' | 'محلول' | 'مغلق';
  reviewer: string;
}

export interface ReportsOverviewStats {
  metrics: {
    avgResolutionTime: string;
    activeDisputes: number;
    solvedToday: number;
    openTickets: number;
  };
  tickets: OverviewTicket[];
  disputeReasons: Array<{
    title: string;
    count: number;
    color: string;
  }>;
  bookingLog: Array<{
    id: string;
    title: string;
    status: 'مكتمل' | 'ملغي';
  }>;
}

export interface ReportMetrics {
  active: number;
  suspended: number;
  banned: number;
  dismissed: number;
  total: number;
}

export interface AnalyticsStats {
  visitRequests: string;
  visitRequestsChange: string;
  completedVisits: string;
  completedVisitsChange: string;
  avgRating: string;
  avgRatingChange: string;
  retentionRate: string;
  retentionRateChange: string;
  topRegions: Array<{
    name: string;
    count: number;
  }>;
  kycBreakdown: Array<{
    label: string;
    count: number;
    pct: string;
    color: string;
  }>;
  propertyActivity: Array<{
    label: string;
    count: number;
    color: string;
  }>;
  dailyChart: Array<{
    label: string;
    value: number;
  }>;
}

export interface FinancialSummary {
  metrics: {
    avgRent: string;
    activeTransactions: string;
    platformFees: string;
    totalRevenueMonth: string;
  };
  revenueBreakdown: {
    platformFees: { value: string; percent: number };
    managedRentals: { value: string; percent: number };
    kycFees: { value: string; percent: number };
  };
  sixMonthTrend: Array<{
    month: string;
    value: number;
    isCurrent?: boolean;
  }>;
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

export interface AuditLogItem {
  id: string;
  time: string;
  action: string;
  typeBadge: 'KYC' | 'عقار' | 'مستخدم' | 'دور' | 'دعم' | 'بلاغ' | 'نظام';
  target: string;
  operator: string;
}

export interface SystemHealth {
  metrics: {
    uptime: string;
    uptimeSub: string;
    responseTime: string;
    responseSub: string;
    errorsToday: string;
    errorsSub: string;
    dbStatus: string;
    dbSub: string;
  };
  auditLogs: AuditLogItem[];
  apiPerformanceData: Array<{
    hour: string;
    ms: number;
    height: string;
  }>;
  internalAdminNotes: string[];
}

export interface PushCampaign {
  id: string;
  title: string;
  timeAgo: string;
  body: string;
  openRate: string;
  recipientCount: string;
}

