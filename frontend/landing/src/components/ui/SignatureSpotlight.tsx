"use client";

import { useEffect, useRef } from "react";
import clsx from "clsx";
import { SignatureMark } from "@/components/ui/Decor";

// A soft light drifts across the engraving automatically. The mask is confined
// to the signature, so its light never spills onto the feature cards.
export function SignatureSpotlight({ className, wordClassName }: { className?: string; wordClassName: string }) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const lit = rootRef.current?.querySelector<SVGSVGElement>(".spotlight-lit");
    if (!lit) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0;
    let visible = false;
    let elapsed = 0;
    let previousTime = 0;
    const paint = () => {
      const phase = (elapsed / 3000) * Math.PI * 2;
      lit.style.setProperty("--x", `${50 + Math.sin(phase) * 35}%`);
      lit.style.setProperty("--y", `${50 + Math.sin(phase * 2) * 12}%`);
    };
    const tick = (time: number) => {
      if (previousTime) elapsed += Math.min(time - previousTime, 64);
      previousTime = time;
      paint();
      frame = requestAnimationFrame(tick);
    };
    const sync = () => {
      cancelAnimationFrame(frame);
      previousTime = 0;
      if (reducedMotion.matches) {
        lit.style.setProperty("--x", "50%");
        lit.style.setProperty("--y", "50%");
      } else if (visible && !document.hidden) {
        frame = requestAnimationFrame(tick);
      }
    };
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting && entry.boundingClientRect.width > 0;
      sync();
    });
    observer.observe(lit);
    document.addEventListener("visibilitychange", sync);
    reducedMotion.addEventListener("change", sync);
    sync();
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      document.removeEventListener("visibilitychange", sync);
      reducedMotion.removeEventListener("change", sync);
    };
  }, []);

  return (
    <div ref={rootRef} aria-hidden className={clsx("pointer-events-none absolute inset-0", className)}>
      {/* the engraving at rest: only just there */}
      <SignatureMark className={clsx(wordClassName, "text-brand-soft/[0.08]")} />
      {/* the same word, revealed by an autonomous pool of light */}
      <SignatureMark
        className={clsx(wordClassName, "spotlight-lit text-brand-soft opacity-70 [--sig-fill:0.16]")}
      />
    </div>
  );
}
