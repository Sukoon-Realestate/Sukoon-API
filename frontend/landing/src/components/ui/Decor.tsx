import clsx from "clsx";

// Oversized outlined wordmark used as a faint texture on dark sections.
export function OutlinedWordmark({ className }: { className?: string }) {
  return (
    <span
      aria-hidden
      dir="rtl"
      className={clsx(
        "pointer-events-none absolute select-none font-[family-name:var(--font-arabic)] font-bold leading-none text-transparent [-webkit-text-stroke:1.5px_rgba(74,222,128,0.09)]",
        className,
      )}
    >
      سكون
    </span>
  );
}

// Loose topographic lines for the light "How it works" section.
export function ContourLines({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 1200 300"
      fill="none"
      preserveAspectRatio="none"
      className={clsx("pointer-events-none absolute", className)}
    >
      <g stroke="#04a417" strokeOpacity="0.28" strokeWidth="1.5">
        <path d="M0 140c140-40 260 60 420 20s240-120 400-70 220 120 380 80" />
        <path d="M0 190c160-50 280 50 440 10s250-110 410-60 200 110 350 70" />
        <path d="M0 240c150-30 300 40 460 0s260-100 420-50 190 100 320 60" />
        <path d="M640 300c-30-70 10-130 70-140s110 40 90 100" />
        <path d="M700 300c-20-50 10-90 50-95s70 30 60 75" />
        <path d="M900 300c20-80 90-120 150-100s70 70 40 100" />
      </g>
    </svg>
  );
}
