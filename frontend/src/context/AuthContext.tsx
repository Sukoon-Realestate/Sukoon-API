'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
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
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      try {
        return localStorage.getItem('sukoon_admin_auth') === 'true';
      } catch {
        return false;
      }
    }
    return false;
  });

  const [user, setUser] = useState<UserProfile | null>(() => {
    if (typeof window !== 'undefined') {
      try {
        if (localStorage.getItem('sukoon_admin_auth') === 'true') {
          const stored = localStorage.getItem('sukoon_user');
          if (stored) {
            try {
              return JSON.parse(stored);
            } catch {
              // ignore
            }
          }
          return {
            name: 'سيف النظام',
            email: 'admin@sukoon.com',
            role: 'مالك النظام',
          };
        }
      } catch {
        return null;
      }
    }
    return null;
  });

  const isLoading = false;
  const router = useRouter();
  const pathname = usePathname();

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
      } catch (e) {
        console.warn('LocalStorage unavailable:', e);
      }
    }
    setIsAuthenticated(true);
    setUser(profile);
    router.push('/');
  };

  const login = async (email: string, pass: string): Promise<boolean> => {
    try {
      const res: any = await apiClient('/api/v1/auth/login/', {
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
      router.push('/');
      return true;
    } catch (err) {
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
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('sukoon_access_token');
        localStorage.removeItem('sukoon_admin_auth');
        localStorage.removeItem('sukoon_user');
      } catch {}
    }
    router.push('/login');
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
        router.push('/login');
      }
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [pathname, router]);

  // Protected route guard: if not auth and not on /login -> redirect to /login
  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated && pathname !== '/login') {
        router.push('/login');
      } else if (isAuthenticated && pathname === '/login') {
        router.push('/');
      }
    }
  }, [isLoading, isAuthenticated, pathname, router]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, loginDemo, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
