import { Check, ClipboardCheck } from "lucide-react";
import clsx from "clsx";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { ArchLines } from "@/components/ui/Decor";
import { SECTION_IDS } from "@/lib/sections";

// Stagger helper for the mock-UI choreography inside each card.
const at = (ms: number) => ({ "--d": `${ms}ms` }) as React.CSSProperties;

function BentoCard({
  className,
  delay = 0,
  children,
}: {
  className?: string;
  delay?: number;
  children: React.ReactNode;
}) {
  return (
    <article
      style={{ "--delay": `${delay}ms` } as React.CSSProperties}
      className={clsx(
        "reveal relative overflow-hidden rounded-[1.75rem] border border-white/10 bg-white/[0.04] p-5 hover:-translate-y-1 hover:border-white/20 sm:p-7",
        className,
      )}
    >
      {children}
    </article>
  );
}

// Small mock-UI panel shown at the top of each feature card.
function Preview({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div aria-hidden className={clsx("rounded-2xl border border-white/10 bg-pine/60 p-4", className)}>
      {children}
    </div>
  );
}

function FeatureText({ title, body }: { title: string; body: string }) {
  return (
    <>
      <h3 className="mt-6 font-display text-xl font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-white/60">{body}</p>
    </>
  );
}

export function WhySukoon({ dict }: { dict: Dictionary }) {
  const why = dict.why;
  const { commission, verified, review, chat, booking } = why;

  return (
    <section id={SECTION_IDS.why} className="scroll-mt-16 bg-paper px-2 pb-2 sm:px-4 sm:pb-4">
      <div className="relative overflow-hidden rounded-[2rem] bg-pine py-24 dark:ring-1 dark:ring-white/10 sm:rounded-[2.75rem] sm:py-32">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_50%_0%,rgba(4,164,23,0.22),transparent_65%)]"
        />

        <Container className="relative">
          <SectionHeading eyebrow={why.eyebrow} titleLines={why.titleLines} subtitle={why.subtitle} tone="dark" />

          <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-12">
            {/* 0% commission */}
            <BentoCard className="flex flex-col justify-between gap-8 border-brand/30 bg-linear-to-br from-brand-deep/70 to-pine sm:flex-row sm:items-end sm:p-9 md:col-span-2 lg:col-span-7">
              <ArchLines animated count={5} className="-bottom-6 end-0 size-80 text-white/10" />
              <div className="relative max-w-xs">
                <span className="inline-flex rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-brand-soft ring-1 ring-white/15">
                  {commission.badge}
                </span>
                <h3 className="mt-5 font-display text-3xl font-semibold leading-tight text-white sm:text-4xl lg:text-3xl xl:text-4xl">
                  {commission.titleLines.map((line) => (
                    <span key={line} className="block">
                      {line}
                    </span>
                  ))}
                </h3>
                <p className="mt-3 text-sm leading-6 text-white/65">{commission.body}</p>
              </div>
              <div className="relative text-center sm:text-end">
                <p
                  dir="ltr"
                  className="font-[family-name:var(--font-readex)] text-8xl font-semibold leading-none tracking-tighter text-brand-soft tabular-nums sm:text-[9rem] lg:text-[6.5rem] xl:text-[9rem]"
                >
                  {/* Counts down from 100% to the final 0% (see .countdown in globals.css). */}
                  <span className="sr-only">{commission.stat}</span>
                  <span aria-hidden className="countdown" />
                </p>
                <p className="mt-2 text-sm font-semibold uppercase tracking-[0.2em] text-white/70">{commission.statLabel}</p>
              </div>
            </BentoCard>

            {/* Verified accounts */}
            <BentoCard delay={120} className="flex flex-col justify-between lg:col-span-5">
              <Preview className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span style={at(300)} className="seq-pop grid size-10 shrink-0 place-items-center rounded-full bg-brand-deep text-sm font-bold text-white ring-2 ring-brand/40">
                    {verified.initial}
                  </span>
                  <span className="leading-tight">
                    <span className="block text-sm font-semibold text-white">{verified.name}</span>
                    <span className="block text-xs text-white/50">{verified.role}</span>
                  </span>
                </div>
                <span style={at(750)} className="seq-pop inline-flex shrink-0 items-center gap-1 rounded-full bg-brand px-2.5 py-1 text-xs font-semibold text-white">
                  <Check className="size-3" strokeWidth={3} />
                  {verified.badge}
                </span>
              </Preview>
              <div>
                <FeatureText title={verified.title} body={verified.body} />
              </div>
            </BentoCard>

            {/* Full review */}
            <BentoCard className="lg:col-span-4">
              <Preview>
                <ul className="space-y-3">
                  {review.checks.map((item, index) => (
                    <li key={item} className="flex items-center justify-between text-sm text-white/85">
                      {item}
                      <span style={at(400 + index * 350)} className="seq-pop grid size-5 place-items-center rounded-full bg-brand text-white">
                        <Check className="size-3" strokeWidth={3} />
                      </span>
                    </li>
                  ))}
                </ul>
                <p style={at(400 + review.checks.length * 350)} className="seq-rise mt-3.5 flex items-center gap-1.5 border-t border-white/10 pt-3.5 text-sm font-semibold text-brand-soft">
                  <ClipboardCheck className="size-4" />
                  {review.status}
                </p>
              </Preview>
              <FeatureText title={review.title} body={review.body} />
            </BentoCard>

            {/* In-app chat */}
            <BentoCard delay={120} className="lg:col-span-4">
              <Preview className="space-y-2.5 text-sm leading-6">
                <p style={at(300)} className="seq-rise me-8 rounded-2xl rounded-ss-md bg-white/10 px-3.5 py-2 text-white/85">
                  {chat.question}
                </p>
                {/* the owner "types", then the reply lands in the same spot */}
                <div className="relative">
                  <span
                    style={at(800)}
                    className="typing-bubble absolute end-0 top-0 flex gap-1 rounded-2xl rounded-ee-md bg-brand/25 px-3.5 py-3.5"
                  >
                    <span className="typing-dot size-1.5 rounded-full bg-brand-soft" />
                    <span className="typing-dot size-1.5 rounded-full bg-brand-soft" />
                    <span className="typing-dot size-1.5 rounded-full bg-brand-soft" />
                  </span>
                  <p style={at(1850)} className="seq-rise ms-8 rounded-2xl rounded-ee-md bg-brand px-3.5 py-2 font-medium text-white">
                    {chat.answer}
                  </p>
                </div>
              </Preview>
              <FeatureText title={chat.title} body={chat.body} />
            </BentoCard>

            {/* Viewing booking */}
            <BentoCard delay={240} className="lg:col-span-4">
              <Preview>
                <div className="grid grid-cols-3 gap-1.5">
                  {booking.days.map((day, index) => (
                    <span
                      key={day}
                      style={index === 1 ? at(500) : undefined}
                      className={clsx(
                        "rounded-lg py-1.5 text-center text-xs font-medium",
                        index === 1 ? "seq-pop bg-white text-pine" : "border border-white/12 text-white/70",
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
                      style={index === 1 ? at(850) : undefined}
                      className={clsx(
                        "rounded-lg py-1.5 text-center text-xs font-medium",
                        index === 1 ? "seq-pop border border-brand-soft text-brand-soft" : "border border-white/12 text-white/70",
                      )}
                    >
                      {time}
                    </span>
                  ))}
                </div>
                <span style={at(1250)} className="shine mt-2 block rounded-lg bg-brand py-2 text-center text-xs font-semibold text-white">
                  {booking.confirm}
                </span>
              </Preview>
              <FeatureText title={booking.title} body={booking.body} />
            </BentoCard>
          </div>
        </Container>
      </div>
    </section>
  );
}
