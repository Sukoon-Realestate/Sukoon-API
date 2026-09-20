'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';

interface UserProfile {
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: UserProfile | null;
  login: (email: string, pass: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  login: async () => false,
  logout: () => {},
  isLoading: true,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('sukoon_admin_auth') === 'true';
    }
    return false;
  });

  const [user, setUser] = useState<UserProfile | null>(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('sukoon_admin_auth') === 'true') {
      return {
        name: 'أحمد العدل',
        email: 'admin@sukoon.app',
        role: 'مشرف رئيسي',
      };
    }
    return null;
  });

  const isLoading = false;
  const router = useRouter();
  const pathname = usePathname();

  const login = async (email: string, pass: string): Promise<boolean> => {
    // Demo validation
    if (email && pass) {
      setIsAuthenticated(true);
      setUser({
        name: 'أحمد العدل',
        email,
        role: 'مشرف رئيسي',
      });
      localStorage.setItem('sukoon_admin_auth', 'true');
      router.push('/');
      return true;
    }
    return false;
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('sukoon_admin_auth');
    router.push('/login');
  };

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
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
