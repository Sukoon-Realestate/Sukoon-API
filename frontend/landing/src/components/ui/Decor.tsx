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

// Concentric doorway arches: the page's "home" motif.
export function ArchLines({ className, count = 6 }: { className?: string; count?: number }) {
  const rise = 120;

  return (
    <svg
      aria-hidden
      viewBox="0 0 400 400"
      fill="none"
      preserveAspectRatio="xMidYMax meet"
      className={clsx("pointer-events-none absolute", className)}
    >
      <g stroke="currentColor" strokeWidth="1.25">
        {Array.from({ length: count }, (_, index) => {
          const r = 60 + index * 28;
          const top = 400 - rise;
          return (
            <path
              key={r}
              d={`M${200 - r} 400V${top}A${r} ${r} 0 0 1 ${200 + r} ${top}V400`}
              strokeOpacity={1 - index / (count + 1)}
            />
          );
        })}
      </g>
    </svg>
  );
}
