"use client";

import { useEffect } from "react";

const SELECTOR = ".reveal, [data-animate]";

// Marks `.reveal` / `[data-animate]` elements with [data-inview] the first time
// they scroll into view; globals.css keys every entrance animation off that.
export function InViewObserver() {
  useEffect(() => {
    const elements = document.querySelectorAll<HTMLElement>(SELECTOR);
    const show = (element: Element) => element.setAttribute("data-inview", "");

    if (!("IntersectionObserver" in window)) {
      elements.forEach(show);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          show(entry.target);
          observer.unobserve(entry.target);
        }
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.1 },
    );

    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);

  return null;
}
