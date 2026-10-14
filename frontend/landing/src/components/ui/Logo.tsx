import clsx from "clsx";

// TODO: swap for the official SVG wordmark once design hands it over.
export function Logo({ className, size = "md" }: { className?: string; size?: "sm" | "md" | "lg" }) {
  return (
    <span
      dir="ltr"
      className={clsx("inline-flex flex-col items-center leading-none text-white select-none", className)}
      aria-hidden
    >
      <span
        className={clsx(
          "font-[family-name:var(--font-arabic)] font-bold",
          size === "sm" && "text-2xl",
          size === "md" && "text-3xl",
          size === "lg" && "text-4xl",
        )}
      >
        سكون
      </span>
      <span
        className={clsx(
          "font-[family-name:var(--font-latin)] font-medium uppercase tracking-[0.18em]",
          size === "lg" ? "text-[0.6rem]" : "text-[0.5rem]",
        )}
      >
        Sukoon
      </span>
    </span>
  );
}
