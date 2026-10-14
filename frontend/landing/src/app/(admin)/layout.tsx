import type { Metadata } from 'next';
import { Cairo } from 'next/font/google';
import '../globals.css';
import { AppLayout } from '@/components/layout/AppLayout';
import { AuthProvider } from '@/context/AuthContext';
import { ThemeProvider } from '@/context/ThemeContext';
import { ToastProvider } from '@/components/ui/Toast';
import { Splash } from '@/components/ui/LogoLoader';
import { loadingInitScript } from '@/lib/loading';

const cairo = Cairo({
  subsets: ['arabic', 'latin'],
  weight: ['400', '500', '600', '700', '800', '900'],
  variable: '--font-cairo',
});

export const metadata: Metadata = {
  title: 'سكون – لوحة تحكم الإدارة',
  description: 'لوحة التحكم والإدارة لمركز عقارات سكون',
  // Private dashboard: keep it out of search results (robots.txt on the landing app also disallows /admin).
  robots: { index: false, follow: false },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ar" dir="rtl" className={`${cairo.variable} h-full antialiased`} suppressHydrationWarning>
      <head>
        {/* ! Inline script to apply theme before paint — prevents flash */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('sukoon_theme');
                  if (!theme) {
                    theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  }
                  if (theme === 'dark') {
                    document.documentElement.classList.add('dark');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
        {/* ! Logo splash flag, set before paint (see lib/loading.ts) */}
        <script dangerouslySetInnerHTML={{ __html: loadingInitScript }} />
      </head>
      <body className="min-h-full flex bg-[var(--background)] text-[var(--foreground)] font-sans">
        <Splash />
        <ThemeProvider>
          <ToastProvider>
            <AuthProvider>
              <AppLayout>{children}</AppLayout>
            </AuthProvider>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
