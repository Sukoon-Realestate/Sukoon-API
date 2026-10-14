import Image from "next/image";
import clsx from "clsx";
import wordmark from "@/assets/brand/wordmark.png";

// Rendered height in px; the width follows the lockup's aspect ratio.
const HEIGHTS = { sm: 44, md: 52, lg: 96 } as const;

// Arabic + Latin wordmark; the master file lives at docs/brand/wordmark.png.
// Favicons and the OG image keep the square mark (docs/brand/logo.png).
export function Logo({
  className,
  size = "md",
  preload,
}: {
  className?: string;
  size?: keyof typeof HEIGHTS;
  preload?: boolean;
}) {
  const height = HEIGHTS[size];
  const width = Math.round((height * wordmark.width) / wordmark.height);

  return (
    <Image
      src={wordmark}
      alt=""
      aria-hidden
      width={width}
      height={height}
      preload={preload}
      className={clsx("select-none", className)}
      style={{ height, width: "auto" }}
    />
  );
}
