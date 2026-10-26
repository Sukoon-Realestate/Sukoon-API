'use client';

import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { apiClient, ApiError } from '@/lib/api/client';
import { isBackendEnabled } from '@/lib/api/config';
import { adminPath, adminRelativePath } from '@/lib/basePath';
import { ADMIN_ROUTE_PATHS, canOpenAdminPath } from '../lib/admin-access';

interface UserProfile { id: string; name: string; email: string; role: string; canManageStaff: boolean; allowedPaths: string[]; }
interface AuthContextType {
  isAuthenticated: boolean; user: UserProfile | null; isLoading: boolean;
  login: (email: string, pass: string) => Promise<boolean>; loginDemo: () => void; logout: () => void;
}
const AuthContext = createContext<AuthContextType>({ isAuthenticated: false, user: null, isLoading: true, login: async () => false, loginDemo: () => {}, logout: () => {} });
export const useAuth = () => useContext(AuthContext);
const demoProfile: UserProfile = { id: 'demo', name: 'Demo administrator', email: 'admin@sukoon.com', role: 'system_owner', canManageStaff: true, allowedPaths: [...ADMIN_ROUTE_PATHS] };
function confirmedProfile(value: UserProfile): UserProfile {
  const roles = new Set(['system_owner', 'main_admin', 'kyc_reviewer', 'property_reviewer', 'support', 'financial_approver', 'psp_reconciliation', 'payout_operator', 'refund_operator', 'dispute_resolver', 'support_supervisor', 'account_closure_reviewer', 'security_recovery_reviewer', 'staff']);
  if (!value || typeof value.id !== 'string' || !value.id.trim() ||
      typeof value.name !== 'string' || typeof value.email !== 'string' ||
      !roles.has(value.role) || typeof value.canManageStaff !== 'boolean' ||
      value.canManageStaff !== (value.role === 'system_owner') || !Array.isArray(value.allowedPaths) ||
      value.allowedPaths.some(path => !ADMIN_ROUTE_PATHS.includes(path as typeof ADMIN_ROUTE_PATHS[number]))) throw new Error('Invalid administrative session');
  return value;
}
function clearStoredAuth() {
  for (const key of ['sukoon_access_token', 'sukoon_admin_auth', 'sukoon_user', 'sukoon_admin_mode']) localStorage.removeItem(key);
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [restoreError, setRestoreError] = useState(false);
  const [restoreAttempt, setRestoreAttempt] = useState(0);
  const generation = useRef(0);
  const router = useRouter();
  const pathname = adminRelativePath(usePathname());
  const isPasswordReset = pathname.startsWith('/password-reset/');
  const isAuthenticated = user !== null;

  useEffect(() => {
    const epoch = ++generation.current;
    const restore = async () => {
      try {
        const mode = isBackendEnabled() ? 'live' : 'demo';
        if (localStorage.getItem('sukoon_admin_mode') !== mode) { clearStoredAuth(); return; }
        const profile = mode === 'live' ? confirmedProfile(await apiClient<UserProfile>('/api/v1/admin/session/')) : demoProfile;
        if (epoch === generation.current) setUser(profile);
      } catch (error) {
        if (epoch === generation.current) {
          setUser(null);
          if (error instanceof ApiError && (error.status === 401 || error.status === 403)) clearStoredAuth();
          else setRestoreError(true);
        }
      }
      finally { if (epoch === generation.current) setIsLoading(false); }
    };
    void restore();
    const sessionGeneration = generation;
    return () => { sessionGeneration.current++; };
  }, [restoreAttempt]);

  const loginDemo = () => {
    if (isBackendEnabled()) return;
    generation.current++;
    clearStoredAuth();
    localStorage.setItem('sukoon_admin_mode', 'demo');
    setUser(demoProfile);
    router.push(adminPath('/'));
  };
  const login = async (email: string, password: string): Promise<boolean> => {
    if (!isBackendEnabled()) return false; // Demo entry is explicit, never a password fallback.
    const epoch = ++generation.current;
    try {
      const result = await apiClient<{ access: string }>('/api/v1/auth/login/', { method: 'POST', body: { email: email.trim(), password } });
      if (epoch !== generation.current) return false;
      if (!result.access || result.access.startsWith('mock_')) throw new Error('Missing authoritative session');
      localStorage.setItem('sukoon_access_token', result.access);
      const profile = confirmedProfile(await apiClient<UserProfile>('/api/v1/admin/session/'));
      if (epoch !== generation.current) return false;
      localStorage.setItem('sukoon_admin_mode', 'live');
      setUser(profile);
      router.push(adminPath(profile.role === 'security_recovery_reviewer' ? '/security' : '/'));
      return true;
    } catch {
      if (epoch === generation.current) { clearStoredAuth(); setUser(null); }
      return false;
    }
  };
  const logout = async () => {
    generation.current++;
    setUser(null);
    const command = isBackendEnabled() ? apiClient('/api/v1/auth/logout/', { method: 'POST' }) : Promise.resolve();
    clearStoredAuth();
    router.push(adminPath('/login'));
    try { await command; } catch { /* Local access remains cleared; the server session may require revocation. */ }
  };
  useEffect(() => {
    const unauthorized = () => { generation.current++; clearStoredAuth(); setUser(null); setIsLoading(false); };
    window.addEventListener('auth:unauthorized', unauthorized);
    return () => window.removeEventListener('auth:unauthorized', unauthorized);
  }, []);
  useEffect(() => {
    if (isLoading || restoreError || isPasswordReset) return;
    if (!isAuthenticated && pathname !== '/login') router.push(adminPath('/login'));
    else if (isAuthenticated && user?.role === 'security_recovery_reviewer' && pathname !== '/security') router.push(adminPath('/security'));
    else if (isAuthenticated && pathname === '/login') router.push(adminPath('/'));
  }, [isLoading, restoreError, isAuthenticated, pathname, router, user?.role, isPasswordReset]);
  return <AuthContext.Provider value={{ isAuthenticated, user, login, loginDemo, logout, isLoading }}>
    {!isBackendEnabled() && <div role="status">DEMO — simulated records; no live commands.</div>}
    {isPasswordReset ? children : restoreError ? <div role="alert" className="m-auto p-6">
      <p>تعذّر تأكيد جلسة الإدارة. أعد المحاولة عند عودة الاتصال.</p>
      <button type="button" onClick={() => { setIsLoading(true); setRestoreError(false); setRestoreAttempt(value => value + 1); }}>إعادة المحاولة</button>
      <button type="button" onClick={() => { clearStoredAuth(); setRestoreError(false); setUser(null); router.push(adminPath('/login')); }}>العودة لتسجيل الدخول</button>
    </div> : !isLoading && isAuthenticated && pathname !== '/login' && !canOpenAdminPath(user?.allowedPaths, pathname)
      ? <div role="alert" className="m-auto max-w-xl space-y-4 p-6" dir="rtl">
        <p>هذا القسم غير متاح لصلاحيات حسابك الحالية.</p>
        <button className="rounded border px-4 py-3" onClick={() => router.push(adminPath(user?.allowedPaths.includes('/') ? '/' : '/security'))}>العودة إلى المساحة المخولة</button>
        <button className="rounded border px-4 py-3" onClick={() => void logout()}>تسجيل الخروج</button>
      </div> : !isLoading && (isAuthenticated || pathname === '/login') ? children
      : <div role="status" className="m-auto p-6">جاري التحقق من جلسة الإدارة…</div>}
  </AuthContext.Provider>;
};
