import { CalendarCheck, Check, Heart, House, MapPin, MessageCircle, Search, ShieldCheck, User } from "lucide-react";
import Image from "next/image";
import clsx from "clsx";
import type { Dictionary } from "@/i18n/dictionaries";

// Listing photo on a mock card; decorative, since the whole mockup is aria-hidden.
function ListingPhoto({ src }: { src: string }) {
  return (
    <Image
      unoptimized
      src={src}
      alt=""
      width={640}
      height={400}
      className="size-full object-cover"
    />
  );
}

function ReviewedTag({ label }: { label: string }) {
  return (
    <span className="absolute start-2 top-2 inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 text-[0.55rem] font-semibold text-brand-deep shadow-sm">
      <Check className="size-2.5" strokeWidth={3} aria-hidden />
      {label}
    </span>
  );
}

function FloatingCard({
  icon,
  title,
  subtitle,
  variant,
  className,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  variant: "brand" | "light";
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "absolute z-10 flex items-center gap-2.5 rounded-2xl border border-line/80 bg-paper/95 px-3 py-2.5 shadow-[0_20px_40px_-16px_rgba(12,42,24,0.45)] backdrop-blur sm:gap-3 sm:px-3.5 sm:py-3",
        className,
      )}
    >
      <span
        className={clsx(
          "grid size-8 place-items-center rounded-xl sm:size-9",
          variant === "brand" ? "bg-brand text-white" : "bg-chip text-accent",
        )}
      >
        {icon}
      </span>
      <span className="leading-tight">
        <span className="block text-xs font-semibold text-fg sm:text-sm">{title}</span>
        <span className="block text-[0.65rem] text-muted sm:text-[0.7rem]">{subtitle}</span>
      </span>
    </div>
  );
}

function ListingCard({
  listing,
  art,
  reviewed,
  delay,
  imageClassName,
}: {
  listing: Dictionary["phone"]["listings"][number];
  art: React.ReactNode;
  reviewed: string;
  delay: number;
  imageClassName: string;
}) {
  return (
    <div
      style={{ animationDelay: `${delay}ms` }}
      className="shrink-0 animate-fade-up overflow-hidden rounded-2xl bg-white shadow-[0_2px_10px_-4px_rgba(12,42,24,0.25)]"
    >
      <div className={clsx("relative", imageClassName)}>
        {art}
        <ReviewedTag label={reviewed} />
        <span className="absolute end-2 top-2 grid size-5 place-items-center rounded-full bg-white">
          <Heart className="size-2.5 text-heading" aria-hidden />
        </span>
      </div>
      <div className="px-2.5 py-2">
        <div className="flex items-center justify-between gap-2 text-[0.65rem] font-bold">
          <span className="truncate text-heading">{listing.title}</span>
          <span className="shrink-0 text-brand-deep">{listing.price}</span>
        </div>
        <div className="mt-0.5 flex items-center justify-between gap-2 text-[0.5rem] text-body">
          <span className="flex min-w-0 items-center gap-0.5">
            <MapPin className="size-2.5 shrink-0" aria-hidden />
            <span className="truncate">{listing.location}</span>
          </span>
          <span className="shrink-0">{listing.period}</span>
        </div>
      </div>
    </div>
  );
}

// iOS-style status bar glyphs (signal bars, Wi-Fi, battery).
function StatusIcons() {
  return (
    <span dir="ltr" className="flex items-center gap-1">
      <svg viewBox="0 0 17 11" className="h-[0.5rem] w-auto" fill="currentColor">
        <rect x="0" y="7" width="3" height="4" rx="0.8" />
        <rect x="4.5" y="5" width="3" height="6" rx="0.8" />
        <rect x="9" y="2.5" width="3" height="8.5" rx="0.8" />
        <rect x="13.5" y="0" width="3" height="11" rx="0.8" />
      </svg>
      <svg viewBox="0 0 16 11" className="h-[0.5rem] w-auto" fill="currentColor">
        <path d="M8 2.2c2.3 0 4.4.9 6 2.4l1.2-1.3A10.4 10.4 0 0 0 8 .4 10.4 10.4 0 0 0 .8 3.3L2 4.6a8.6 8.6 0 0 1 6-2.4Zm0 3.4c1.4 0 2.6.5 3.6 1.4l1.2-1.3A7 7 0 0 0 8 3.8a7 7 0 0 0-4.8 1.9L4.4 7c1-.9 2.2-1.4 3.6-1.4Zm0 3.3c-.6 0-1.1.2-1.5.6L8 11l1.5-1.5c-.4-.4-.9-.6-1.5-.6Z" />
      </svg>
      <svg viewBox="0 0 25 12" className="h-[0.55rem] w-auto" fill="none">
        <rect x="0.5" y="0.5" width="21" height="11" rx="3" stroke="currentColor" strokeOpacity="0.4" />
        <rect x="2" y="2" width="18" height="8" rx="1.8" fill="currentColor" />
        <path d="M23 4v4c.8-.3 1.3-1.1 1.3-2S23.8 4.3 23 4Z" fill="currentColor" fillOpacity="0.45" />
      </svg>
    </span>
  );
}

export function PhoneMockup({ dict }: { dict: Dictionary }) {
  const phone = dict.phone;
  const [primary, secondary] = phone.listings;
  const tabIcons = [House, Heart, MessageCircle, User];

  return (
    // iPhone 15 Pro proportions (71.6 x 146.6 mm), so the mock reads as a real phone.
    <div className="relative mx-auto aspect-[71.6/146.6] w-full max-w-[15.5rem] sm:max-w-[17rem]" aria-hidden>
      {/* side buttons: action + volume on the left, power on the right (physical sides, not RTL-aware) */}
      <span className="absolute -left-[3px] top-[17%] h-[4%] w-[3px] rounded-l-sm bg-[#2a332d]" />
      <span className="absolute -left-[3px] top-[25%] h-[8%] w-[3px] rounded-l-sm bg-[#2a332d]" />
      <span className="absolute -left-[3px] top-[35%] h-[8%] w-[3px] rounded-l-sm bg-[#2a332d]" />
      <span className="absolute -right-[3px] top-[28%] h-[12%] w-[3px] rounded-r-sm bg-[#2a332d]" />

      {/* titanium band → black bezel → screen */}
      <div className="size-full rounded-[2.9rem] bg-linear-to-b from-[#3a443d] via-[#1c231e] to-[#2c352f] p-[3px] shadow-[0_40px_80px_-24px_rgba(12,42,24,0.75)]">
        <div className="size-full rounded-[2.75rem] bg-black p-[7px]">
          <div className="relative flex size-full flex-col overflow-hidden rounded-[2.3rem] bg-[#f6f8f6]">
            {/* Dynamic Island */}
            <span className="absolute left-1/2 top-2 z-10 h-[1.35rem] w-[34%] -translate-x-1/2 rounded-full bg-black" />

            {/* status bar */}
            <div className="flex h-10 shrink-0 items-center justify-between px-6 pt-1 text-heading">
              <span dir="ltr" className="font-[family-name:var(--font-latin)] text-[0.62rem] font-semibold">
                9:41
              </span>
              <StatusIcons />
            </div>

            <div className="flex min-h-0 flex-1 flex-col px-4 pt-1">
              {/* top bar */}
              <div className="flex shrink-0 items-start justify-between">
                <div>
                  <p className="text-[0.55rem] text-body">{phone.locationLabel}</p>
                  <p className="mt-0.5 flex items-center gap-1 text-[0.7rem] font-semibold text-heading">
                    <MapPin className="size-3 text-brand" aria-hidden />
                    {phone.location}
                  </p>
                </div>
                <span className="grid size-7 place-items-center rounded-full bg-brand-deep text-[0.65rem] font-bold text-white">
                  {phone.avatar}
                </span>
              </div>

              <p className="mt-3 shrink-0 text-base font-bold text-heading">{phone.title}</p>

              <div className="mt-2 flex shrink-0 items-center gap-1.5 rounded-full border border-black/10 bg-white px-3 py-1.5 text-[0.6rem] text-body">
                <Search className="size-3" aria-hidden />
                {phone.search}
              </div>

              <div className="mt-2.5 flex shrink-0 gap-1.5">
                {phone.filters.map((filter, index) => (
                  <span
                    key={filter}
                    className={clsx(
                      "rounded-full px-2.5 py-1 text-[0.55rem] font-medium",
                      index === 0 ? "bg-heading text-white" : "border border-black/10 bg-white text-heading",
                    )}
                  >
                    {filter}
                  </span>
                ))}
              </div>

              {/* listings scroll on under the tab bar, like a real feed */}
              <div className="mt-3 flex min-h-0 flex-1 flex-col gap-2.5 overflow-hidden">
                <ListingCard
                  listing={primary}
                  art={<ListingPhoto src="/images/listings/apartment.jpg" />}
                  reviewed={phone.reviewed}
                  delay={700}
                  imageClassName="h-24"
                />
                <ListingCard
                  listing={secondary}
                  art={<ListingPhoto src="/images/listings/studio.jpg" />}
                  reviewed={phone.reviewed}
                  delay={850}
                  imageClassName="h-24"
                />
              </div>
            </div>

            {/* tab bar + home indicator */}
            <div className="relative shrink-0 border-t border-black/5 bg-white/95 px-2 pb-5 pt-2 backdrop-blur">
              <div className="grid grid-cols-4">
                {phone.tabs.map((tab, index) => {
                  const Icon = tabIcons[index];
                  return (
                    <span
                      key={tab}
                      className={clsx(
                        "flex flex-col items-center gap-0.5 text-[0.5rem]",
                        index === 0 ? "font-semibold text-brand-deep" : "text-body",
                      )}
                    >
                      <Icon className="size-3.5" aria-hidden />
                      {tab}
                    </span>
                  );
                })}
              </div>
              <span className="absolute bottom-1.5 left-1/2 h-1 w-[36%] -translate-x-1/2 rounded-full bg-heading/85" />
            </div>
          </div>
        </div>
      </div>

      <FloatingCard
        variant="brand"
        icon={<ShieldCheck className="size-4" aria-hidden />}
        title={phone.verifiedOwner.title}
        subtitle={phone.verifiedOwner.subtitle}
        className="-end-3 top-[41%] animate-float min-[400px]:-end-14 sm:-end-28 lg:-end-12 xl:-end-28"
      />
      {/* both cards sit over listing photos so they never hide a title or price */}
      <FloatingCard
        variant="light"
        icon={<CalendarCheck className="size-4" aria-hidden />}
        title={phone.viewingBooked.title}
        subtitle={phone.viewingBooked.subtitle}
        className="-start-3 top-[72%] animate-float-delayed min-[400px]:-start-14 sm:-start-24 lg:-start-10 xl:-start-24"
      />
    </div>
  );
}
