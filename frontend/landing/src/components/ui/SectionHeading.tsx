import clsx from "clsx";

export function SectionHeading({
  eyebrow,
  titleLines,
  subtitle,
  tone = "light",
  align = "start",
  className,
}: {
  eyebrow: string;
  titleLines: string[];
  subtitle: string;
  tone?: "light" | "dark";
  align?: "start" | "center";
  className?: string;
}) {
  const dark = tone === "dark";
  const centered = align === "center";

  return (
    <div className={clsx("reveal max-w-2xl", centered && "mx-auto text-center", className)}>
      <p
        className={clsx(
          "inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em]",
          dark ? "text-brand-soft" : "text-accent",
        )}
      >
        <span className={clsx("h-px w-6", dark ? "bg-brand-soft/60" : "bg-accent/50")} aria-hidden />
        {eyebrow}
      </p>
      <h2
        className={clsx(
          "mt-4 font-display text-[2.1rem] font-semibold leading-[1.12] tracking-tight sm:text-5xl",
          dark ? "text-white" : "text-fg",
        )}
      >
        {titleLines.map((line) => (
          <span key={line} className="block">
            {line}
          </span>
        ))}
      </h2>
      <p
        className={clsx(
          "mt-4 text-base leading-8 sm:text-lg",
          dark ? "text-white/65" : "text-muted",
          centered && "mx-auto max-w-xl",
        )}
      >
        {subtitle}
      </p>
    </div>
  );
}
