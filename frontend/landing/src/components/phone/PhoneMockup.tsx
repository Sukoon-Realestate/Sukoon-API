import { CalendarCheck, Check, Heart, House, MapPin, MessageCircle, Search, ShieldCheck, User } from "lucide-react";
import clsx from "clsx";
import type { Dictionary } from "@/i18n/dictionaries";
import { BuildingArt, HouseArt } from "./PropertyArt";

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
        "absolute z-10 flex items-center gap-3 rounded-2xl border border-line/80 bg-paper/95 px-3.5 py-3 shadow-[0_20px_40px_-16px_rgba(12,42,24,0.45)] backdrop-blur",
        className,
      )}
    >
      <span
        className={clsx(
          "grid size-9 place-items-center rounded-xl",
          variant === "brand" ? "bg-brand text-white" : "bg-chip text-accent",
        )}
      >
        {icon}
      </span>
      <span className="leading-tight">
        <span className="block text-sm font-semibold text-fg">{title}</span>
        <span className="block text-[0.7rem] text-muted">{subtitle}</span>
      </span>
    </div>
  );
}

export function PhoneMockup({ dict }: { dict: Dictionary }) {
  const phone = dict.phone;
  const [primary, secondary] = phone.listings;
  const tabIcons = [House, Heart, MessageCircle, User];

  return (
    <div className="relative mx-auto w-full max-w-[17rem] sm:max-w-[18.5rem]" aria-hidden>
      <div className="rounded-[2.6rem] bg-[#0b120d] p-2 shadow-[0_40px_80px_-24px_rgba(12,42,24,0.75)] ring-1 ring-white/10">
        <div className="overflow-hidden rounded-[2.2rem] bg-[#f6f8f6]">
          <div className="px-4 pt-5">
            {/* top bar */}
            <div className="flex items-start justify-between">
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

            <p className="mt-3 text-base font-bold text-heading">{phone.title}</p>

            <div className="mt-2 flex items-center gap-1.5 rounded-full border border-black/10 bg-white px-3 py-1.5 text-[0.6rem] text-body">
              <Search className="size-3" aria-hidden />
              {phone.search}
            </div>

            <div className="mt-2.5 flex gap-1.5">
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

            {/* primary listing */}
            <div className="mt-3 overflow-hidden rounded-2xl bg-white shadow-sm">
              <div className="relative h-20">
                <BuildingArt className="size-full" />
                <ReviewedTag label={phone.reviewed} />
                <span className="absolute end-2 top-2 grid size-5 place-items-center rounded-full bg-white">
                  <Heart className="size-2.5 text-heading" aria-hidden />
                </span>
              </div>
              <div className="px-2.5 py-2">
                <div className="flex items-center justify-between text-[0.65rem] font-bold">
                  <span className="text-heading">{primary.title}</span>
                  <span className="text-brand-deep">{primary.price}</span>
                </div>
                <div className="mt-0.5 flex items-center justify-between text-[0.5rem] text-body">
                  <span className="flex items-center gap-0.5">
                    <MapPin className="size-2.5" aria-hidden />
                    {primary.location}
                  </span>
                  <span>{primary.period}</span>
                </div>
              </div>
            </div>

            {/* secondary listing, clipped by the tab bar like in the design */}
            <div className="mt-2.5 h-16 overflow-hidden rounded-t-2xl bg-white shadow-sm">
              <div className="relative h-full" title={secondary.title}>
                <HouseArt className="size-full" />
                <ReviewedTag label={phone.reviewed} />
              </div>
            </div>
          </div>

          {/* tab bar */}
          <div className="grid grid-cols-4 border-t border-black/5 bg-white px-2 pb-3 pt-2">
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
        </div>
      </div>

      <FloatingCard
        variant="brand"
        icon={<ShieldCheck className="size-4" aria-hidden />}
        title={phone.verifiedOwner.title}
        subtitle={phone.verifiedOwner.subtitle}
        className="-end-8 top-[28%] animate-float sm:-end-28"
      />
      <FloatingCard
        variant="light"
        icon={<CalendarCheck className="size-4" aria-hidden />}
        title={phone.viewingBooked.title}
        subtitle={phone.viewingBooked.subtitle}
        className="-start-8 top-[64%] animate-float-delayed sm:-start-24"
      />
    </div>
  );
}
