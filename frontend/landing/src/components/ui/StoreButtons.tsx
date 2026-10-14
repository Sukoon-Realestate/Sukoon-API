import { Smartphone } from "lucide-react";
import clsx from "clsx";
import type { Dictionary } from "@/i18n/dictionaries";

// Store links aren't live yet, so these render as non-interactive badges.
export function StoreButtons({ dict, className }: { dict: Dictionary; className?: string }) {
  const stores = [dict.store.appStore, dict.store.googlePlay];

  return (
    <ul className={clsx("flex flex-wrap gap-2.5", className)}>
      {stores.map((store) => (
        <li key={store}>
          <span
            aria-label={`${dict.store.comingSoon} ${store}`}
            className="flex min-w-36 items-center gap-3 rounded-xl bg-brand px-5 py-2.5 text-heading shadow-[0_8px_24px_-8px_rgba(4,164,23,0.6)] sm:min-w-37"
          >
            <Smartphone className="size-5 shrink-0" strokeWidth={1.75} aria-hidden />
            <span className="flex flex-col items-start leading-tight" aria-hidden>
              <span className="text-[0.6rem] font-medium">{dict.store.comingSoon}</span>
              <span className="font-[family-name:var(--font-latin)] text-sm font-semibold">{store}</span>
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}
