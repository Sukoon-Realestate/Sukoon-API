import {
  dashboardData,
  executiveData,
  analyticsData,
  usersData,
  propertiesData,
  kycData,
  financialsData,
  moderationData,
  supportData,
  reportsData,
  rolesData,
  systemData,
  settingsData,
  authData,
} from '@/data/mock';
import type { RequestOptions } from './client';

import type { PropertyDetail, KycDetail } from './types';

// Simulated delay to mimic real network behavior and preserve loading states
const MOCK_LATENCY_MS = 60;

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// In-memory clone of settings to allow real-time toggling during development
let currentSettings = { ...settingsData };

export async function handleMockRequest<T = unknown>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  await sleep(MOCK_LATENCY_MS);

  // Normalize endpoint: strip trailing slash and extract query if present
  const [path, queryString] = endpoint.split('?');
  const cleanPath = path.replace(/\/+$/, '');

  // Parse params combining options.params and URL query parameters
  const params: Record<string, string | number | boolean | undefined | null> = {
    ...(options.params || {}),
  };
  if (queryString) {
    const searchParams = new URLSearchParams(queryString);
    searchParams.forEach((val, key) => {
      if (params[key] === undefined) {
        params[key] = val;
      }
    });
  }

  const method = (options.method || 'GET').toUpperCase();

  // 1. Authentication
  if (cleanPath === '/api/v1/auth/login') {
    return {
      message: 'تم تسجيل الدخول بنجاح (وضع البيانات التجريبية)',
      data: {
        access: authData.access,
        refresh: authData.refresh,
        user: authData.user,
      },
      access: authData.access,
      refresh: authData.refresh,
      user: authData.user,
    } as unknown as T;
  }

  if (cleanPath === '/api/v1/auth/logout') {
    return { message: 'تم تسجيل الخروج بنجاح' } as unknown as T;
  }

  // 2. Dashboards
  if (cleanPath === '/api/v1/admin/dashboard/executive') {
    return executiveData as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/dashboard') {
    return dashboardData as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/analytics') {
    return analyticsData as unknown as T;
  }

  // 3. Users Management
  if (cleanPath === '/api/v1/admin/users') {
    const allUsers = [...usersData.users, ...usersData.suspendedUsers];
    let filtered = allUsers;

    if (params.search) {
      const q = String(params.search).toLowerCase();
      filtered = filtered.filter(
        (u) =>
          u.name.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q) ||
          (u.phone && u.phone.includes(q))
      );
    }

    if (params.role) {
      filtered = filtered.filter((u) => u.type === params.role);
    }

    if (params.status && params.status !== 'all') {
      filtered = filtered.filter((u) => u.status === params.status);
    }

    if (params.kyc_status && params.kyc_status !== 'all') {
      filtered = filtered.filter((u) => u.kycStatus === params.kyc_status);
    }

    const page = Number(params.page) || 1;
    const pageSize = Number(params.page_size) || 10;
    const start = (page - 1) * pageSize;
    const results = filtered.slice(start, start + pageSize);

    return {
      count: filtered.length,
      next: start + pageSize < filtered.length ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results,
    } as unknown as T;
  }

  // User detail or user actions
  const userActionMatch = cleanPath.match(/^\/api\/v1\/admin\/users\/([^/]+)\/(suspend|unsuspend)$/);
  if (userActionMatch) {
    const action = userActionMatch[2];
    return {
      message: action === 'suspend' ? 'تم إيقاف حساب المستخدم بنجاح' : 'تم إلغاء إيقاف الحساب بنجاح',
    } as unknown as T;
  }

  const userDetailMatch = cleanPath.match(/^\/api\/v1\/admin\/users\/([^/]+)$/);
  if (userDetailMatch) {
    const userId = userDetailMatch[1];
    const allUsers = [...usersData.users, ...usersData.suspendedUsers];
    const user = allUsers.find((u) => u.id === userId) || usersData.users[0];
    return user as unknown as T;
  }

  // 4. Properties Management
  if (cleanPath === '/api/v1/admin/properties/metrics') {
    return propertiesData.metrics as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/properties') {
    let filtered = propertiesData.properties;

    if (params.search) {
      const q = String(params.search).toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.owner.toLowerCase().includes(q)
      );
    }

    if (params.property_type && params.property_type !== 'all') {
      filtered = filtered.filter(
        (p) => p.type === params.property_type || p.property_type === params.property_type
      );
    }

    if (params.status && params.status !== 'all') {
      filtered = filtered.filter((p) => p.status === params.status);
    }

    const page = Number(params.page) || 1;
    const pageSize = Number(params.page_size) || 10;
    const start = (page - 1) * pageSize;
    const results = filtered.slice(start, start + pageSize);

    return {
      count: filtered.length,
      next: start + pageSize < filtered.length ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results,
    } as unknown as T;
  }

  const propActionMatch = cleanPath.match(
    /^\/api\/v1\/admin\/properties\/([^/]+)\/(approve|reject|revision)$/
  );
  if (propActionMatch) {
    const action = propActionMatch[2];
    const msg =
      action === 'approve'
        ? 'تمت الموافقة على العقار بنجاح'
        : action === 'reject'
        ? 'تم رفض العقار بنجاح'
        : 'تم إرسال طلب التعديل بنجاح';
    return { message: msg } as unknown as T;
  }

  const propDetailMatch = cleanPath.match(/^\/api\/v1\/admin\/properties\/([^/]+)$/);
  if (propDetailMatch) {
    const propId = propDetailMatch[1];
    const detailsMap = propertiesData.details as unknown as Record<string, PropertyDetail>;
    const detail = detailsMap[propId] || detailsMap['prop-1'];
    return detail as unknown as T;
  }

  // 5. KYC Review
  if (cleanPath === '/api/v1/admin/kyc/metrics') {
    return kycData.metrics as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/kyc') {
    let filtered = kycData.requests;

    if (params.status && params.status !== 'all') {
      filtered = filtered.filter((k) => k.status === params.status || k.statusDisplay === params.status);
    }

    if (params.user_type && params.user_type !== 'all') {
      filtered = filtered.filter((k) => k.type === params.user_type);
    }

    const page = Number(params.page) || 1;
    const pageSize = Number(params.page_size) || 10;
    const start = (page - 1) * pageSize;
    const results = filtered.slice(start, start + pageSize);

    return {
      count: filtered.length,
      next: start + pageSize < filtered.length ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results,
    } as unknown as T;
  }

  const kycActionMatch = cleanPath.match(/^\/api\/v1\/admin\/kyc\/([^/]+)\/(approve|reject)$/);
  if (kycActionMatch) {
    const action = kycActionMatch[2];
    return {
      message: action === 'approve' ? 'تم توثيق الحساب بنجاح' : 'تم رفض طلب التوثيق بنجاح',
    } as unknown as T;
  }

  const kycDetailMatch = cleanPath.match(/^\/api\/v1\/admin\/kyc\/([^/]+)$/);
  if (kycDetailMatch) {
    const subId = kycDetailMatch[1];
    const detailsMap = kycData.details as unknown as Record<string, KycDetail>;
    const detail = detailsMap[subId] || detailsMap['kyc-1'];
    return detail as unknown as T;
  }

  // 6. Financials
  if (cleanPath === '/api/v1/admin/financials/summary') {
    return financialsData.summary as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/financials/transactions') {
    let filtered = financialsData.transactions;

    if (params.status && params.status !== 'all') {
      filtered = filtered.filter((t) => t.status === params.status);
    }

    if (params.search) {
      const q = String(params.search).toLowerCase();
      filtered = filtered.filter(
        (t) =>
          t.description.toLowerCase().includes(q) ||
          t.tenant.toLowerCase().includes(q) ||
          t.landlord.toLowerCase().includes(q)
      );
    }

    const page = Number(params.page) || 1;
    const pageSize = Number(params.page_size) || 10;
    const start = (page - 1) * pageSize;
    const results = filtered.slice(start, start + pageSize);

    return {
      count: filtered.length,
      next: start + pageSize < filtered.length ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results,
    } as unknown as T;
  }

  // 7. Moderation
  if (cleanPath === '/api/v1/admin/moderation/metrics') {
    return moderationData.metrics as unknown as T;
  }

  const modDeleteMatch = cleanPath.match(/^\/api\/v1\/admin\/moderation\/([^/]+)\/delete$/);
  if (modDeleteMatch) {
    return { message: 'تم حذف المحتوى المخالف بنجاح' } as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/moderation') {
    return {
      count: moderationData.items.length,
      next: null,
      previous: null,
      results: moderationData.items,
    } as unknown as T;
  }

  // 8. Support
  if (cleanPath === '/api/v1/admin/support/metrics') {
    return supportData.metrics as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/support') {
    let filtered = supportData.tickets;

    if (params.tab && params.tab !== 'all') {
      filtered = filtered.filter((t) => t.statusRaw === params.tab || t.status === params.tab);
    }

    const page = Number(params.page) || 1;
    const pageSize = Number(params.page_size) || 10;
    const start = (page - 1) * pageSize;
    const results = filtered.slice(start, start + pageSize);

    return {
      count: filtered.length,
      next: start + pageSize < filtered.length ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results,
    } as unknown as T;
  }

  // 9. Reports
  if (cleanPath === '/api/v1/admin/reports/metrics') {
    return reportsData.metrics as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/reports/overview') {
    return reportsData.overview as unknown as T;
  }

  const reportActionMatch = cleanPath.match(/^\/api\/v1\/admin\/reports\/([^/]+)\/action$/);
  if (reportActionMatch) {
    return { message: 'تم تنفيذ الإجراء الإداري بنجاح' } as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/reports') {
    let filtered = reportsData.reports;

    if (params.status && params.status !== 'all') {
      filtered = filtered.filter((r) => r.status === params.status);
    }

    if (params.automation_level && params.automation_level !== 'all') {
      filtered = filtered.filter(
        (r) => r.automation_level === params.automation_level || r.automationLevelDisplay === params.automation_level
      );
    }

    const page = Number(params.page) || 1;
    const pageSize = Number(params.page_size) || 10;
    const start = (page - 1) * pageSize;
    const results = filtered.slice(start, start + pageSize);

    return {
      count: filtered.length,
      next: start + pageSize < filtered.length ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results,
    } as unknown as T;
  }

  // 10. Staff & Roles
  if (cleanPath === '/api/v1/admin/staff/roles') {
    return rolesData.roles as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/staff/invite') {
    return { message: 'تم إرسال دعوة الانضمام بنجاح' } as unknown as T;
  }

  const staffDeleteMatch = cleanPath.match(/^\/api\/v1\/admin\/staff\/([^/]+)$/);
  if (staffDeleteMatch && method === 'DELETE') {
    return { message: 'تم حذف المشرف بنجاح' } as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/staff') {
    return {
      count: rolesData.staff.length,
      next: null,
      previous: null,
      results: rolesData.staff,
    } as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/permissions') {
    if (method === 'PATCH' || method === 'POST') {
      let matrix = rolesData.permissionsMatrix;
      if (options.body) {
        try {
          matrix = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
        } catch {
          // ignore
        }
      }
      return { message: 'تم تحديث مصفوفة الصلاحيات بنجاح', matrix } as unknown as T;
    }
    return rolesData.permissionsMatrix as unknown as T;
  }

  // 11. System Health & Logs
  if (cleanPath === '/api/v1/admin/system/health') {
    return systemData.health as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/system/logs') {
    let filtered = systemData.health.auditLogs;

    if (params.type && params.type !== 'all') {
      filtered = filtered.filter((l) => l.typeBadge === params.type);
    }

    if (params.search) {
      const q = String(params.search).toLowerCase();
      filtered = filtered.filter(
        (l) =>
          l.action.toLowerCase().includes(q) ||
          l.operator.toLowerCase().includes(q) ||
          l.target.toLowerCase().includes(q)
      );
    }

    const page = Number(params.page) || 1;
    const pageSize = Number(params.page_size) || 10;
    const start = (page - 1) * pageSize;
    const results = filtered.slice(start, start + pageSize);

    return {
      count: filtered.length,
      next: start + pageSize < filtered.length ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results,
    } as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/system/notifications/send') {
    let bodyData: Record<string, string> = {};
    if (options.body) {
      try {
        bodyData = typeof options.body === 'string' ? JSON.parse(options.body) : (options.body as Record<string, string>);
      } catch {
        // ignore
      }
    }
    const newCampaign = {
      id: `nc-${Date.now()}`,
      title: bodyData.title || 'حملة إشعار جديدة',
      timeAgo: 'الآن',
      body: bodyData.body || '',
      openRate: '0% فتح',
      recipientCount: '2,847 وصل',
    };
    return newCampaign as unknown as T;
  }

  if (cleanPath === '/api/v1/admin/system/notifications') {
    return systemData.pushCampaigns as unknown as T;
  }

  // 12. Settings
  if (cleanPath === '/api/v1/admin/settings') {
    if (method === 'POST') {
      if (options.body) {
        try {
          const parsed = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
          currentSettings = { ...currentSettings, ...parsed };
        } catch {
          // ignore
        }
      }
      return currentSettings as unknown as T;
    }
    return currentSettings as unknown as T;
  }

  // Fallback generic response
  console.warn(`[MockAPI] No specific handler for "${cleanPath}" [${method}], returning empty payload`);
  return {} as T;
}
