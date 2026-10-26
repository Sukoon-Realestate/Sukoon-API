import type { Metadata } from 'next';
import StaffPasswordReset from '../../../../components/security/StaffPasswordReset';

export const metadata: Metadata = { referrer: 'no-referrer', robots: { index: false, follow: false } };
export default async function Page({ params }: { params: Promise<{ uid: string; token: string }> }) {
  return <StaffPasswordReset {...await params} />;
}
