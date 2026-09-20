'use client';

import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      className="relative p-1.5 rounded-full hover:bg-[var(--card-hover)] text-[var(--text-muted)] transition-all duration-200 group"
    >
      <div className="relative w-5 h-5 overflow-hidden">
        {/* Sun icon — visible in dark mode (to switch to light) */}
        <Sun
          className={`w-5 h-5 absolute inset-0 transition-all duration-300 ${
            theme === 'dark'
              ? 'rotate-0 scale-100 opacity-100'
              : 'rotate-90 scale-0 opacity-0'
          }`}
        />
        {/* Moon icon — visible in light mode (to switch to dark) */}
        <Moon
          className={`w-5 h-5 absolute inset-0 transition-all duration-300 ${
            theme === 'light'
              ? 'rotate-0 scale-100 opacity-100'
              : '-rotate-90 scale-0 opacity-0'
          }`}
        />
      </div>
    </button>
  );
};
