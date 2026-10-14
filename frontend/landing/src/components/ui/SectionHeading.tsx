import clsx from "clsx";

export function SectionHeading({
  eyebrow,
  titleLines,
  subtitle,
  tone = "light",
  className,
}: {
  eyebrow: string;
  titleLines: string[];
  subtitle: string;
  tone?: "light" | "dark";
  className?: string;
}) {
  const dark = tone === "dark";

  return (
    <div className={clsx("max-w-xl", className)}>
      <p className={clsx("text-xs font-semibold", dark ? "text-brand" : "text-brand-deep")}>{eyebrow}</p>
      <h2
        className={clsx(
          "mt-3 text-3xl font-bold leading-[1.15] tracking-tight sm:text-4xl",
          dark ? "text-white" : "text-heading",
        )}
      >
        {titleLines.map((line) => (
          <span key={line} className="block">
            {line}
          </span>
        ))}
      </h2>
      <p className={clsx("mt-3 text-sm leading-7 sm:text-base", dark ? "text-white/60" : "text-body")}>
        {subtitle}
      </p>
    </div>
  );
}
