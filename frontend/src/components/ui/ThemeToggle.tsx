'use client';

import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return <button type="button" onClick={toggleTheme} className="flex min-h-12 min-w-12 items-center justify-center rounded-lg hover:bg-[var(--card-hover)]" aria-label="تبديل المظهر الفاتح والداكن">
    <Sun size={20} className="hidden dark:block" aria-hidden /><Moon size={20} className="dark:hidden" aria-hidden />
    <span className="sr-only">{theme === 'dark' ? 'الوضع الفاتح' : 'الوضع الداكن'}</span>
  </button>;
}
