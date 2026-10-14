'use client';

import React, { useState, createContext, useContext } from 'react';
import { usePathname } from 'next/navigation';
import { adminRelativePath } from '@/lib/basePath';
import { Sidebar } from './Sidebar';

interface SidebarContextType {
  isMobileOpen: boolean;
  toggleMobileMenu: () => void;
  closeMobileMenu: () => void;
}

const SidebarContext = createContext<SidebarContextType>({
  isMobileOpen: false,
  toggleMobileMenu: () => {},
  closeMobileMenu: () => {},
});

export const useSidebar = () => useContext(SidebarContext);

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const pathname = adminRelativePath(usePathname());

  const toggleMobileMenu = () => setIsMobileOpen((prev) => !prev);
  const closeMobileMenu = () => setIsMobileOpen(false);

  if (pathname === '/login') {
    return <>{children}</>;
  }

  return (
    <SidebarContext.Provider value={{ isMobileOpen, toggleMobileMenu, closeMobileMenu }}>
      <div className="admin-shell min-h-full flex text-[var(--foreground)] font-sans w-full">
        <a href="#admin-main" className="admin-skip-link">انتقل إلى المحتوى</a>
        <Sidebar isMobileOpen={isMobileOpen} onCloseMobile={closeMobileMenu} />
        <main id="admin-main" className="admin-main flex-1 min-w-0 flex flex-col min-h-screen">
          {children}
        </main>
      </div>
    </SidebarContext.Provider>
  );
};
