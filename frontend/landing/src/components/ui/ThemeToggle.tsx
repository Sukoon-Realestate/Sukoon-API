'use client';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return <button type="button" onClick={toggleTheme} className="admin-icon-button" aria-label="تبديل المظهر الفاتح والداكن" title="تبديل المظهر"><Sun size={19} className="hidden dark:block" aria-hidden /><Moon size={19} className="dark:hidden" aria-hidden /><span className="sr-only">{theme === 'dark' ? 'الوضع الفاتح' : 'الوضع الداكن'}</span></button>;
}
