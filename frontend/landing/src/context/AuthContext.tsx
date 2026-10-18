'use client';

import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { apiClient } from '@/lib/api/client';
import { isBackendEnabled } from '@/lib/api/config';
import { adminPath, adminRelativePath } from '@/lib/basePath';

interface UserProfile { id: string; name: string; email: string; role: string; canManageStaff: boolean; }
interface AuthContextType {
  isAuthenticated: boolean; user: UserProfile | null; isLoading: boolean;
  login: (email: string, pass: string) => Promise<boolean>; loginDemo: () => void; logout: () => void;
}
const AuthContext = createContext<AuthContextType>({ isAuthenticated: false, user: null, isLoading: true, login: async () => false, loginDemo: () => {}, logout: () => {} });
export const useAuth = () => useContext(AuthContext);
const demoProfile: UserProfile = { id: 'demo', name: 'Demo administrator', email: 'admin@sukoon.com', role: 'system_owner', canManageStaff: true };
function confirmedProfile(value: UserProfile): UserProfile {
  const roles = new Set(['system_owner', 'main_admin', 'kyc_reviewer', 'property_reviewer', 'support', 'financial_approver', 'psp_reconciliation', 'payout_operator', 'refund_operator', 'dispute_resolver', 'staff']);
  if (!value || typeof value.id !== 'string' || !value.id.trim() ||
      typeof value.name !== 'string' || typeof value.email !== 'string' ||
      !roles.has(value.role) || typeof value.canManageStaff !== 'boolean' ||
      value.canManageStaff !== (value.role === 'system_owner')) throw new Error('Invalid administrative session');
  return value;
}
function clearStoredAuth() {
  for (const key of ['sukoon_access_token', 'sukoon_admin_auth', 'sukoon_user', 'sukoon_admin_mode']) localStorage.removeItem(key);
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const generation = useRef(0);
  const router = useRouter();
  const pathname = adminRelativePath(usePathname());
  const isAuthenticated = user !== null;

  useEffect(() => {
    const epoch = ++generation.current;
    const restore = async () => {
      try {
        const mode = isBackendEnabled() ? 'live' : 'demo';
        if (localStorage.getItem('sukoon_admin_mode') !== mode) { clearStoredAuth(); return; }
        const profile = mode === 'live' ? confirmedProfile(await apiClient<UserProfile>('/api/v1/admin/session/')) : demoProfile;
        if (epoch === generation.current) setUser(profile);
      } catch { if (epoch === generation.current) { clearStoredAuth(); setUser(null); } }
      finally { if (epoch === generation.current) setIsLoading(false); }
    };
    void restore();
    return () => { generation.current++; };
  }, []);

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
      router.push(adminPath('/'));
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
    if (isLoading) return;
    if (!isAuthenticated && pathname !== '/login') router.push(adminPath('/login'));
    else if (isAuthenticated && pathname === '/login') router.push(adminPath('/'));
  }, [isLoading, isAuthenticated, pathname, router]);
  return <AuthContext.Provider value={{ isAuthenticated, user, login, loginDemo, logout, isLoading }}>
    {!isBackendEnabled() && <div role="status">DEMO — simulated records; no live commands.</div>}
    {children}
  </AuthContext.Provider>;
};
