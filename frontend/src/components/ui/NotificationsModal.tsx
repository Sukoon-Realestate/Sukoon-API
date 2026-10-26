'use client';

import { AdminFollowupsDialog } from '../analytics/AdminFollowupsDialog';

export function NotificationsModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  return isOpen ? <AdminFollowupsDialog onClose={onClose} /> : null;
}
