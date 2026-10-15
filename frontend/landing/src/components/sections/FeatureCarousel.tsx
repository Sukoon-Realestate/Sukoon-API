"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Pause, Play } from "lucide-react";
import clsx from "clsx";

type Labels = { previous: string; next: string; carousel: string; pause: string; play: string };

// Horizontal scroll-snap track: swipe/trackpad scroll works natively (and without
// JS); the tabs and arrows just scroll the track. The active slide is whichever
// one is mostly visible, so manual swipes and button clicks stay in sync.
//
// Autoplay is driven by the active chip's progress bar: when its CSS animation
// ends we advance. Pausing (hover, focus, off-screen, pause button) just pauses
// that animation, so the timer and the bar can never drift apart. Under reduced
// motion animations are disabled globally, so the bar never ends and nothing auto-advances.
export function FeatureCarousel({ tabs, slides, labels }: { tabs: string[]; slides: React.ReactNode[]; labels: Labels }) {
  const rootRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const tabsRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [onScreen, setOnScreen] = useState(false);
  const [stopped, setStopped] = useState(false);
  const total = slides.length;
  const playing = onScreen && !hovered && !focused && !stopped;

  // Slide we are programmatically scrolling to; while set, the slides passed on the
  // way are ignored, so the active chip/animations don't flicker through them.
  const targetRef = useRef<number | null>(null);

  useEffect(() => {
    const track = trackRef.current;
    const root = rootRef.current;
    if (!track || !root) return;
    const slideObserver = new IntersectionObserver(
      (entries) => {
        if (targetRef.current !== null) return;
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const index = Number((entry.target as HTMLElement).dataset.index);
            setActive(index);
            centerChip(index);
          }
        }
      },
      { root: track, threshold: 0.6 },
    );
    Array.from(track.children).forEach((slide) => slideObserver.observe(slide));
    // "On screen" = overlapping the middle band of the viewport; a ratio threshold
    // can never be met on phones, where the stacked slide is taller than the screen.
    const viewportObserver = new IntersectionObserver(([entry]) => setOnScreen(entry.isIntersecting), { rootMargin: "-30% 0px" });
    viewportObserver.observe(root);
    const settle = () => (targetRef.current = null);
    track.addEventListener("scrollend", settle);
    return () => {
      slideObserver.disconnect();
      viewportObserver.disconnect();
      track.removeEventListener("scrollend", settle);
    };
  }, []);

  // Keep the active chip visible in the (mobile) scrolling chip row, without moving the page.
  // Instant, and done before the track moves: in Chromium, starting another scroll
  // cancels the track's in-flight smooth scroll.
  function centerChip(index: number) {
    const row = tabsRef.current;
    const chip = row?.children[index] as HTMLElement | undefined;
    if (!row || !chip || row.scrollWidth <= row.clientWidth) return;
    const rowBox = row.getBoundingClientRect();
    const chipBox = chip.getBoundingClientRect();
    row.scrollBy({ left: chipBox.left + chipBox.width / 2 - (rowBox.left + rowBox.width / 2), behavior: "instant" });
  }

  function goTo(target: number) {
    const index = (target + total) % total;
    const track = trackRef.current;
    const slide = track?.children[index] as HTMLElement | undefined;
    if (!track || !slide) return;
    centerChip(index);
    setActive(index);
    targetRef.current = index;
    // Fallback for browsers without `scrollend` (older Safari).
    window.setTimeout(() => targetRef.current === index && (targetRef.current = null), 1200);
    // Measured offset rather than offsetLeft, so it is direction-agnostic (RTL). scrollTo,
    // not scrollBy: Chromium treats scrollBy as a directional scroll, which `snap-always`
    // stops at the very next slide, so multi-slide jumps (chips, wrap-around) fell short.
    const delta = slide.getBoundingClientRect().left - track.getBoundingClientRect().left;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    track.scrollTo({ left: track.scrollLeft + delta, behavior: reduce ? "auto" : "smooth" });
  }

  return (
    <div
      ref={rootRef}
      role="region"
      aria-roledescription="carousel"
      aria-label={labels.carousel}
      className="reveal mt-12"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setFocused(true)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setFocused(false);
      }}
    >
      <div ref={tabsRef} className="-mx-5 flex gap-2 overflow-x-auto px-5 pb-2 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:justify-center sm:px-0 [&::-webkit-scrollbar]:hidden">
        {tabs.map((tab, index) => (
          <button
            key={tab}
            type="button"
            onClick={() => goTo(index)}
            aria-current={index === active}
            className={clsx(
              "relative shrink-0 overflow-hidden rounded-full border px-4 py-2 text-xs font-semibold transition-[color,background-color,border-color,transform] duration-300 sm:text-sm",
              index === active ? "scale-105 border-accent bg-accent text-paper" : "border-line text-muted hover:bg-chip hover:text-fg",
            )}
          >
            {tab}
            {index === active && (
              <span
                key={active}
                aria-hidden
                onAnimationEnd={() => goTo(active + 1)}
                style={{ animationPlayState: playing ? "running" : "paused" }}
                className="carousel-progress absolute inset-x-0 bottom-0 h-0.5 bg-paper/60"
              />
            )}
          </button>
        ))}
      </div>

      <div
        ref={trackRef}
        className="mt-10 flex snap-x snap-mandatory overflow-x-auto overscroll-x-contain [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {slides.map((slide, index) => (
          <div
            key={index}
            data-index={index}
            data-active={index === active || undefined}
            role="group"
            aria-roledescription="slide"
            aria-label={`${index + 1} / ${total}`}
            className="feature-slide w-full shrink-0 snap-start snap-always"
          >
            {slide}
          </div>
        ))}
      </div>

      <div className="mt-8 flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={() => goTo(active - 1)}
          aria-label={labels.previous}
          className="grid size-11 place-items-center rounded-full border border-line text-fg transition-[background-color,transform] hover:bg-chip active:scale-90"
        >
          <ChevronLeft aria-hidden className="size-5 rtl:rotate-180" />
        </button>
        <p dir="ltr" aria-live={playing ? "off" : "polite"} className="min-w-16 text-center text-sm font-semibold tabular-nums text-muted">
          <span key={active} className="carousel-count inline-block text-fg">{String(active + 1).padStart(2, "0")}</span> / {String(total).padStart(2, "0")}
        </p>
        <button
          type="button"
          onClick={() => goTo(active + 1)}
          aria-label={labels.next}
          className="grid size-11 place-items-center rounded-full border border-line text-fg transition-[background-color,transform] hover:bg-chip active:scale-90"
        >
          <ChevronRight aria-hidden className="size-5 rtl:rotate-180" />
        </button>
        <button
          type="button"
          onClick={() => setStopped((value) => !value)}
          aria-label={stopped ? labels.play : labels.pause}
          title={stopped ? labels.play : labels.pause}
          className="grid size-11 place-items-center rounded-full text-muted transition-colors hover:bg-chip hover:text-fg motion-reduce:hidden"
        >
          {stopped ? <Play aria-hidden className="size-4" /> : <Pause aria-hidden className="size-4" />}
        </button>
      </div>
    </div>
  );
}
