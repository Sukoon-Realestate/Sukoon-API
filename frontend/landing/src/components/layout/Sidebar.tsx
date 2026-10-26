'use client';
import { SharedSidebar } from '../../../../src/components/admin/SharedSidebar';
export function Sidebar(props: { isMobileOpen?: boolean; onCloseMobile?: () => void }) {
  return <SharedSidebar {...props} publicSiteHref="/ar" />;
}
