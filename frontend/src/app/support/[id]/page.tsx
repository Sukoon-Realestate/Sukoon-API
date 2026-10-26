'use client';
import { useParams } from 'next/navigation';
import SupportDetail from '../../../components/support/SupportDetail';
export default function Page() {
  const { id } = useParams<{ id: string }>();
  return <SupportDetail key={id} id={id} />;
}
