import { redirect } from 'next/navigation';
import { adminPath } from '@/lib/basePath';

export default function ReportsPage() {
  redirect(adminPath('/reports/overview'));
}
