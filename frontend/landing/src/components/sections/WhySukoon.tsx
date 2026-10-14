import { Check, ClipboardCheck } from "lucide-react";
import clsx from "clsx";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { GradientPill } from "@/components/ui/GradientPill";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { SECTION_IDS } from "@/lib/sections";

function BentoCard({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <article className={clsx("relative overflow-hidden rounded-3xl border border-white/8 bg-ink-card p-5 sm:p-6", className)}>
      {children}
    </article>
  );
}

// Small mock-UI panel shown at the top of each feature card.
function Preview({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div aria-hidden className={clsx("rounded-2xl border border-white/8 bg-white/3 p-3.5", className)}>
      {children}
    </div>
  );
}

function FeatureText({ title, body }: { title: string; body: string }) {
  return (
    <>
      <h3 className="mt-6 text-lg font-bold text-white sm:text-xl">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-white/60">{body}</p>
    </>
  );
}

export function WhySukoon({ dict }: { dict: Dictionary }) {
  const why = dict.why;
  const { commission, verified, review, chat, booking } = why;

  return (
    <section id={SECTION_IDS.why} className="bg-ink py-20 sm:py-28">
      <Container>
        <SectionHeading eyebrow={why.eyebrow} titleLines={why.titleLines} subtitle={why.subtitle} tone="dark" />

        <div className="mt-12 grid gap-4 lg:grid-cols-12">
          {/* 0% commission */}
          <BentoCard className="flex flex-col justify-between gap-8 bg-[radial-gradient(ellipse_at_70%_120%,rgba(4,164,23,0.35),transparent_60%)] sm:flex-row sm:items-center sm:p-8 lg:col-span-7">
            <div className="max-w-xs">
              <GradientPill innerClassName="bg-ink-card py-1 text-[0.65rem]">{commission.badge}</GradientPill>
              <h3 className="mt-5 text-2xl font-bold leading-tight text-white sm:text-3xl">
                {commission.titleLines.map((line) => (
                  <span key={line} className="block">
                    {line}
                  </span>
                ))}
              </h3>
              <p className="mt-3 text-sm leading-6 text-white/60">{commission.body}</p>
            </div>
            <div className="text-center">
              <p dir="ltr" className="font-[family-name:var(--font-latin)] text-8xl font-bold leading-none tracking-tighter text-brand sm:text-9xl">
                {commission.stat}
              </p>
              <p className="mt-3 text-sm font-semibold text-white">{commission.statLabel}</p>
            </div>
          </BentoCard>

          {/* Verified accounts */}
          <BentoCard className="lg:col-span-5">
            <Preview className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="grid size-9 place-items-center rounded-full bg-brand-deep text-sm font-bold text-white">
                  {verified.initial}
                </span>
                <span className="leading-tight">
                  <span className="block text-sm font-semibold text-white">{verified.name}</span>
                  <span className="block text-[0.65rem] text-white/50">{verified.role}</span>
                </span>
              </div>
              <span className="inline-flex items-center gap-1 rounded-full bg-brand px-2.5 py-1 text-[0.65rem] font-semibold text-heading">
                <Check className="size-3" strokeWidth={3} />
                {verified.badge}
              </span>
            </Preview>
            <FeatureText title={verified.title} body={verified.body} />
          </BentoCard>

          {/* Full review */}
          <BentoCard className="lg:col-span-4">
            <Preview>
              <ul className="space-y-2.5">
                {review.checks.map((item) => (
                  <li key={item} className="flex items-center justify-between text-xs text-white/85">
                    {item}
                    <span className="grid size-4.5 place-items-center rounded-full bg-brand text-heading">
                      <Check className="size-3" strokeWidth={3} />
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 flex items-center gap-1.5 border-t border-white/8 pt-3 text-xs font-semibold text-brand-soft">
                <ClipboardCheck className="size-3.5" />
                {review.status}
              </p>
            </Preview>
            <FeatureText title={review.title} body={review.body} />
          </BentoCard>

          {/* In-app chat */}
          <BentoCard className="lg:col-span-4">
            <Preview className="space-y-2.5 text-xs leading-5">
              <p className="me-6 rounded-xl rounded-ss-sm bg-white/8 px-3 py-2 text-white/85">{chat.question}</p>
              <p className="ms-6 rounded-xl rounded-ee-sm bg-brand px-3 py-2 font-medium text-heading">{chat.answer}</p>
            </Preview>
            <FeatureText title={chat.title} body={chat.body} />
          </BentoCard>

          {/* Viewing booking */}
          <BentoCard className="lg:col-span-4">
            <Preview>
              <div className="grid grid-cols-3 gap-1.5">
                {booking.days.map((day, index) => (
                  <span
                    key={day}
                    className={clsx(
                      "rounded-lg py-1.5 text-center text-[0.65rem] font-medium",
                      index === 1 ? "bg-white text-heading" : "border border-white/12 text-white/70",
                    )}
                  >
                    {day}
                  </span>
                ))}
              </div>
              <div className="mt-1.5 grid grid-cols-2 gap-1.5">
                {booking.times.map((time, index) => (
                  <span
                    key={time}
                    className={clsx(
                      "rounded-lg py-1.5 text-center text-[0.65rem] font-medium",
                      index === 1 ? "border border-brand text-brand-soft" : "border border-white/12 text-white/70",
                    )}
                  >
                    {time}
                  </span>
                ))}
              </div>
              <span className="mt-2 block rounded-lg bg-brand py-2 text-center text-xs font-semibold text-heading">
                {booking.confirm}
              </span>
            </Preview>
            <FeatureText title={booking.title} body={booking.body} />
          </BentoCard>
        </div>
      </Container>
    </section>
  );
}
