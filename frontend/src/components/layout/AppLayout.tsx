'use client';

import React, { useState, createContext, useContext } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/layout/Sidebar';
import { adminRelativePath } from '@/lib/basePath';

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

  if (pathname === '/login' || pathname.startsWith('/password-reset/')) {
    return <>{children}</>;
  }

  return (
    <SidebarContext.Provider value={{ isMobileOpen, toggleMobileMenu, closeMobileMenu }}>
      <div className="min-h-full flex bg-[var(--background)] text-[var(--foreground)] font-sans w-full overflow-x-hidden">
        <a href="#admin-main" className="sr-only focus:not-sr-only">انتقل إلى المحتوى</a>
        <Sidebar isMobileOpen={isMobileOpen} onCloseMobile={closeMobileMenu} />
        <main id="admin-main" className="flex-1 min-w-0 flex flex-col min-h-screen">
          {children}
        </main>
      </div>
    </SidebarContext.Provider>
  );
};
