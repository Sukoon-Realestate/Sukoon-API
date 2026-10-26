'use client';

import { useAuth } from '@/context/AuthContext';
import PushCampaigns from '../../../notifications/PushCampaigns';

export default function Page() {
  const { user } = useAuth();
  return <PushCampaigns owner={user?.id} canOperate={user?.role === 'system_owner'} />;
}
