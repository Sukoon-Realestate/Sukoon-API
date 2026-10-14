import clsx from "clsx";

// Pill with the pink → orange brand border used for "coming soon" style tags.
export function GradientPill({
  children,
  className,
  innerClassName,
}: {
  children: React.ReactNode;
  className?: string;
  innerClassName?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex rounded-full bg-linear-to-r from-accent-pink to-accent-orange p-px rtl:bg-linear-to-l",
        className,
      )}
    >
      <span
        className={clsx(
          "inline-flex items-center gap-2 rounded-full bg-ink px-3 py-1.5 text-xs font-medium text-white/90",
          innerClassName,
        )}
      >
        {children}
      </span>
    </span>
  );
}
