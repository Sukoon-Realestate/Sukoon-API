"use client";

import { useLayoutEffect, useRef } from "react";
import { useServerInsertedHTML } from "next/navigation";
import type { Locale } from "@/i18n/config";
import { THEME_STORAGE_KEY, themeInitScript } from "@/lib/theme";
import { motionInitScript } from "@/lib/motion";
import { loadingInitScript } from "@/lib/loading";

export function InitialState({ locale }: { locale: Locale }) {
  const inserted = useRef(false);
  // Emit parser-executed initialization into the server's head, never into a
  // client render. This preserves the first-paint theme without HMR warnings.
  useServerInsertedHTML(() => {
    if (inserted.current) return null;
    inserted.current = true;
    return <script id="sukoon-initial-state" dangerouslySetInnerHTML={{ __html: themeInitScript + motionInitScript + loadingInitScript }} />;
  });

  // React can replace root attributes when the locale changes. Restore them
  // before paint without replaying the initial page-loading splash.
  useLayoutEffect(() => {
    const root = document.documentElement;
    let theme = "light";
    try {
      const saved = localStorage.getItem(THEME_STORAGE_KEY);
      if (saved === "light" || saved === "dark") theme = saved;
    } catch {}
    root.dataset.theme = theme;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
      delete root.dataset.motion;
    } else {
      root.dataset.motion = "on";
    }
  }, [locale]);

  return null;
}
