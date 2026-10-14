'use client';

import React, { createContext, useContext, useCallback, useSyncExternalStore } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'light',
  toggleTheme: () => {},
});

export const useTheme = () => useContext(ThemeContext);

// ! The `dark` class on <html> is the single source of truth. The inline head script in
// ! app/layout.tsx sets it before paint (saved choice, else system preference), so React
// ! only reads it. Mirroring it in state used to strip it on mount and flash dark users to light.
const subscribe = (onChange: () => void) => {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  return () => observer.disconnect();
};

const getSnapshot = (): Theme => (document.documentElement.classList.contains('dark') ? 'dark' : 'light');
const getServerSnapshot = (): Theme => 'light';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const toggleTheme = useCallback(() => {
    const root = document.documentElement;
    const next: Theme = root.classList.contains('dark') ? 'light' : 'dark';

    // ? Transitioning class gives the switch a smooth cross-fade
    root.classList.add('theme-transitioning');
    root.classList.toggle('dark', next === 'dark');
    try {
      localStorage.setItem('sukoon_theme', next);
    } catch {
      // ? Storage blocked (private mode etc.); the choice just won't persist
    }
    window.setTimeout(() => root.classList.remove('theme-transitioning'), 450);
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
