'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { adminPath, adminRelativePath } from '@/lib/basePath';
import { apiClient } from '@/lib/api/client';

interface UserProfile {
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: UserProfile | null;
  login: (email: string, pass: string) => Promise<boolean>;
  loginDemo: () => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  login: async () => false,
  loginDemo: () => {},
  logout: () => {},
  isLoading: true,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Hydrate persisted auth after the initial render so server and client agree.
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    void Promise.resolve().then(() => {
      try {
        const authenticated = localStorage.getItem('sukoon_admin_auth') === 'true';
        const stored = localStorage.getItem('sukoon_user');
        setIsAuthenticated(authenticated);
        if (authenticated && stored) {
          try { setUser(JSON.parse(stored)); } catch { setUser(null); }
        }
      } catch {
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    });
  }, []);

  const router = useRouter();
  const pathname = adminRelativePath(usePathname());

  const loginDemo = () => {
    const profile: UserProfile = {
      name: 'سيف النظام',
      email: 'admin@sukoon.com',
      role: 'مالك النظام',
    };
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('sukoon_access_token', 'mock_jwt_access_token_demo_mode');
        localStorage.setItem('sukoon_admin_auth', 'true');
        localStorage.setItem('sukoon_user', JSON.stringify(profile));
      } catch {}
    }
    setIsAuthenticated(true);
    setUser(profile);
    router.push(adminPath('/'));
  };

  const login = async (email: string, pass: string): Promise<boolean> => {
    try {
      const res = await apiClient<{ access?: string; data?: { access?: string } }>('/api/v1/auth/login/', {
        method: 'POST',
        body: JSON.stringify({ email: email.trim(), password: pass.trim() }),
      });

      // Extract access token if returned (support both direct and GenericJsonRenderer wrappers)
      const accessToken = res?.data?.access || res?.access || 'mock_jwt_access_token_demo_mode';
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('sukoon_access_token', accessToken);
        } catch {}
      }

      const profile: UserProfile = {
        name: email.startsWith('admin') ? 'سيف النظام' : email.split('@')[0],
        email: email.trim(),
        role: email.startsWith('admin') ? 'مالك النظام' : 'مشرف',
      };

      setIsAuthenticated(true);
      setUser(profile);
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('sukoon_admin_auth', 'true');
          localStorage.setItem('sukoon_user', JSON.stringify(profile));
        } catch {}
      }
      router.push(adminPath('/'));
      return true;
    } catch {
      return false;
    }
  };

  const logout = async () => {
    try {
      await apiClient('/api/v1/auth/logout/', { method: 'POST' });
    } catch {
      // ignore
    }
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('sukoon_access_token');
    localStorage.removeItem('sukoon_admin_auth');
    localStorage.removeItem('sukoon_user');
    router.push(adminPath('/login'));
  };

  // Listen for unauthorized 401 events across the app
  useEffect(() => {
    const handleUnauthorized = () => {
      setIsAuthenticated(false);
      setUser(null);
      if (typeof window !== 'undefined') {
        try {
          localStorage.removeItem('sukoon_access_token');
          localStorage.removeItem('sukoon_admin_auth');
          localStorage.removeItem('sukoon_user');
        } catch {}
      }
      if (pathname !== '/login') {
        router.push(adminPath('/login'));
      }
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [pathname, router]);

  // Protected route guard: if not auth and not on /login -> redirect to /login
  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated && pathname !== '/login') {
        router.push(adminPath('/login'));
      } else if (isAuthenticated && pathname === '/login') {
        router.push(adminPath('/'));
      }
    }
  }, [isLoading, isAuthenticated, pathname, router]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, loginDemo, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
