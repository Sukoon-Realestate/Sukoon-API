import type { Metadata } from 'next';
import { Cairo } from 'next/font/google';
import './globals.css';
import { AppLayout } from '@/components/layout/AppLayout';

const cairo = Cairo({
  subsets: ['arabic', 'latin'],
  weight: ['400', '500', '600', '700', '800', '900'],
  variable: '--font-cairo',
});

export const metadata: Metadata = {
  title: 'سكون – لوحة تحكم الإدارة',
  description: 'لوحة التحكم والإدارة لمركز عقارات سكون',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ar" dir="rtl" className={`${cairo.variable} h-full antialiased`}>
      <body className="min-h-full flex bg-[#F3F5F8] text-slate-800 font-sans">
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
