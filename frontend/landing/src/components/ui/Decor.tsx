import { useId } from "react";
import clsx from "clsx";
import { SIGNATURE_PATH, SIGNATURE_REST_PATH, SIGNATURE_SEEN_PATH, SIGNATURE_VIEWBOX } from "@/assets/brand/signature";

const PATHS = { word: SIGNATURE_PATH, seen: SIGNATURE_SEEN_PATH, rest: SIGNATURE_REST_PATH };

// The logo's "سكون" calligraphy as a thin outlined engraving, used as a large
// background signature. Size and colour come from `className` (text-*); set
// `--sig-fill` (0-1) to tint the inside of the strokes as well. `draw` lets CSS
// draw the outline in (see .signature-draw in globals.css). `part` draws only
// the first letter (seen) or the rest of the word, in its place in the word.
//
// The visible outline keeps a 1.25px non-scaling stroke at any size, but
// non-scaling strokes ignore pathLength, so dash-based drawing happens on a
// thick, ordinary stroke in a mask underneath instead.
export function SignatureMark({
  className,
  draw = false,
  part = "word",
}: {
  className?: string;
  draw?: boolean;
  part?: keyof typeof PATHS;
}) {
  const maskId = useId();
  return (
    <svg
      aria-hidden
      viewBox={SIGNATURE_VIEWBOX}
      className={clsx("pointer-events-none absolute select-none", className)}
    >
      {draw && (
        <mask id={maskId} maskUnits="userSpaceOnUse">
          {/* wide enough to cover a whole letter's thickness from its outline */}
          <path d={PATHS[part]} pathLength={1} className="signature-draw" fill="none" stroke="white" strokeWidth="120" />
        </mask>
      )}
      <path
        d={PATHS[part]}
        mask={draw ? `url(#${maskId})` : undefined}
        className={clsx(draw && "signature-fill-in")}
        fill="currentColor"
        style={{ fillOpacity: "var(--sig-fill, 0)" }}
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

// Shared size and tone for the two halves of EdgeSignature.
const edgeSignature =
  "w-[64rem] text-brand-deep/25 [--sig-fill:0.18] max-lg:hidden dark:text-brand/30 dark:[--sig-fill:0]";

// The signature split across both edges of a section: its first letter (س)
// alone on the right, the rest of the word (كون) on the left, each fading out
// before it reaches the content.
// Only from lg up: below that sections stack and the text has no free side.
// `className` sets the vertical position (e.g. top-4); the parent must be
// positioned and clip overflow. With `draw`, a [data-animate] parent makes it
// write itself in once in view (see .signature-draw in globals.css).
export function EdgeSignature({ className, draw = false }: { className?: string; draw?: boolean }) {
  return (
    <>
      <SignatureMark
        draw={draw}
        part="seen"
        className={clsx(edgeSignature, "right-0 [mask-image:linear-gradient(to_left,black_26%,rgb(0_0_0/0.35)_46%)]", className)}
      />
      <SignatureMark
        draw={draw}
        part="rest"
        className={clsx(edgeSignature, "-left-10 [mask-image:linear-gradient(to_right,black_45%,transparent_68%)]", className)}
      />
    </>
  );
}

// One oversized signature spanning the width behind a section (the 72rem
// content plus 60% of the margins): its start sits in the left margin, its end
// in the right one, and the middle runs on faintly
// behind the 72rem content column so it still reads as a single word. Only on
// very wide screens, where those margins are really empty; the parent must be
// positioned and clip overflow, and `className` sets the vertical position.
// Give the parent [data-animate] and the word draws itself in when it scrolls
// into view (see .signature-draw in globals.css).
export function WideSignature({ className }: { className?: string }) {
  return (
    <SignatureMark
      draw
      className={clsx(
        "inset-x-0 mx-auto hidden w-[calc(60vw_+_28.8rem)] text-brand-deep/25 [--sig-fill:0.14] min-[1700px]:block dark:text-brand/30 dark:[--sig-fill:0]",
        "[mask-image:linear-gradient(to_right,black_calc(50%_-_37rem),rgb(0_0_0/0.12)_calc(50%_-_31rem),rgb(0_0_0/0.12)_calc(50%_+_31rem),black_calc(50%_+_37rem))]",
        className,
      )}
    />
  );
}

// The word's outline kept very faint, with a short light that keeps running
// along the letters (see .signature-trace in globals.css). Outline colour from
// text-*, the light's from --trace (brand green by default).
export function SignatureTrace({ className }: { className?: string }) {
  const maskId = useId();
  return (
    <svg
      aria-hidden
      viewBox={SIGNATURE_VIEWBOX}
      fill="none"
      className={clsx("signature-trace pointer-events-none absolute select-none", className)}
    >
      {/* the moving dash lives in a mask (non-scaling strokes ignore pathLength) */}
      <mask id={maskId} maskUnits="userSpaceOnUse">
        <path d={SIGNATURE_PATH} pathLength={1} className="signature-trace-light" stroke="white" strokeWidth="40" strokeLinecap="round" />
      </mask>
      <path d={SIGNATURE_PATH} stroke="currentColor" strokeOpacity="0.22" strokeWidth="1.25" vectorEffect="non-scaling-stroke" />
      <path
        d={SIGNATURE_PATH}
        mask={`url(#${maskId})`}
        className="signature-trace-glow"
        // var() only resolves in CSS, not in SVG presentation attributes
        style={{ stroke: "var(--trace, var(--color-brand))" }}
        strokeWidth="2.5"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

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

// Concentric doorway arches: the page's "home" motif. `animated` ripples them
// outwards from the innermost arch.
export function ArchLines({
  className,
  count = 6,
  animated = false,
}: {
  className?: string;
  count?: number;
  animated?: boolean;
}) {
  const rise = 120;

  return (
    <svg
      aria-hidden
      viewBox="0 0 400 400"
      fill="none"
      preserveAspectRatio="xMidYMax meet"
      className={clsx("pointer-events-none absolute", className)}
    >
      <g stroke="currentColor" strokeWidth="1.25" className={clsx(animated && "arch-ripple")}>
        {Array.from({ length: count }, (_, index) => {
          const r = 60 + index * 28;
          const top = 400 - rise;
          return (
            <path
              key={r}
              d={`M${200 - r} 400V${top}A${r} ${r} 0 0 1 ${200 + r} ${top}V400`}
              strokeOpacity={1 - index / (count + 1)}
              style={{ "--i": index } as React.CSSProperties}
            />
          );
        })}
      </g>
    </svg>
  );
}
