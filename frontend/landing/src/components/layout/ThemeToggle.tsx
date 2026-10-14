"use client";

import { Moon, Sun } from "lucide-react";
import { THEME_STORAGE_KEY } from "@/lib/theme";

// Flips html[data-theme] and remembers the choice. The icons swap through the
// `dark:` variant, so nothing here depends on state and hydration stays clean.
export function ThemeToggle({ label }: { label: string }) {
  function toggle() {
    const root = document.documentElement;
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try {
      localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch {
      // Storage blocked (private mode etc.); the choice just won't persist.
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={label}
      title={label}
      className="grid size-9 place-items-center rounded-full text-fg/80 transition-colors hover:bg-sand-deep hover:text-fg"
    >
      <Moon className="size-4.5 dark:hidden" strokeWidth={1.75} aria-hidden />
      <Sun className="hidden size-4.5 dark:block" strokeWidth={1.75} aria-hidden />
    </button>
  );
}
