"use client";

import { useEffect, useRef } from "react";
import clsx from "clsx";
import { SignatureMark } from "@/components/ui/Decor";

// One large signature behind a section, barely there, that a soft light lights
// up under the pointer, like a torch over an engraving. Listens on its parent
// (which must be positioned); without a mouse only the faint word shows.
export function SignatureSpotlight({ className }: { className?: string }) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const area = rootRef.current?.parentElement;
    const lit = rootRef.current?.querySelector<SVGSVGElement>(".spotlight-lit");
    if (!area || !lit) return;

    let frame = 0;
    const move = (event: PointerEvent) => {
      if (event.pointerType !== "mouse") return;
      cancelAnimationFrame(frame);
      // Straight to CSS variables (see .spotlight-lit in globals.css): no React render per move.
      frame = requestAnimationFrame(() => {
        const box = lit.getBoundingClientRect();
        lit.style.setProperty("--x", `${event.clientX - box.left}px`);
        lit.style.setProperty("--y", `${event.clientY - box.top}px`);
        lit.style.opacity = "1";
      });
    };
    const leave = () => {
      cancelAnimationFrame(frame);
      lit.style.opacity = "0";
    };

    area.addEventListener("pointermove", move);
    area.addEventListener("pointerleave", leave);
    return () => {
      cancelAnimationFrame(frame);
      area.removeEventListener("pointermove", move);
      area.removeEventListener("pointerleave", leave);
    };
  }, []);

  const word = "inset-x-0 top-1/2 mx-auto w-[min(100%,74rem)] -translate-y-1/2";

  return (
    <div ref={rootRef} aria-hidden className={clsx("pointer-events-none absolute inset-0", className)}>
      {/* the engraving at rest: only just there */}
      <SignatureMark className={clsx(word, "text-brand-soft/[0.07]")} />
      {/* the same word, shown only inside the pointer's pool of light */}
      <SignatureMark
        className={clsx(word, "spotlight-lit text-brand-soft opacity-0 transition-opacity duration-500 [--sig-fill:0.22]")}
      />
    </div>
  );
}
