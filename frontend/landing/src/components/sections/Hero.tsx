import { ArrowRight, BadgePercent, Building2, ClipboardCheck, KeyRound, MessagesSquare, ShieldCheck } from "lucide-react";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { StoreButtons } from "@/components/ui/StoreButtons";
import { ArchLines, OutlinedWordmark, SignatureMark } from "@/components/ui/Decor";
import { PhoneMockup } from "@/components/phone/PhoneMockup";

function JumpLink({
  icon,
  prompt,
  label,
  href,
}: {
  icon: React.ReactNode;
  prompt: string;
  label: string;
  href: string;
}) {
  return (
    <a
      href={href}
      className="group flex items-center gap-3.5 rounded-2xl border border-line bg-paper/70 p-3.5 transition hover:-translate-y-0.5 hover:border-brand/40 hover:bg-paper hover:shadow-[0_14px_30px_-18px_rgba(12,42,24,0.5)]"
    >
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-chip text-accent">{icon}</span>
      <span className="min-w-0 flex-1 leading-snug">
        <span className="block text-xs text-muted">{prompt}</span>
        <span className="block text-sm font-semibold text-fg">{label}</span>
      </span>
      <ArrowRight
        className="size-4 shrink-0 text-accent transition-transform group-hover:translate-x-0.5 rtl:-scale-x-100 rtl:group-hover:-translate-x-0.5"
        aria-hidden
      />
    </a>
  );
}

// Shared size and tone for the two halves of the background signature. Only
// shown from lg up: below that the hero stacks and the text has no free side.
const signature =
  "top-4 w-[64rem] text-brand-deep/25 [--sig-fill:0.18] max-lg:hidden dark:text-brand/30 dark:[--sig-fill:0]";

// Staggers the hero's on-load entrance (CSS only, so it never waits for JS).
const enter = (ms: number) => ({ animationDelay: `${ms}ms` });

// Unbroken underline drawn under the highlighted half of the headline; it
// draws itself in once the headline has landed.
function Underline() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 300 14"
      preserveAspectRatio="none"
      className="absolute inset-x-0 -bottom-1 h-3 w-full text-brand/45 sm:-bottom-2 sm:h-4"
    >
      <path
        d="M3 10C60 3 140 2 297 7"
        pathLength={1}
        className="draw-line"
        stroke="currentColor"
        strokeWidth="5"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

function TrustStrip({ dict }: { dict: Dictionary }) {
  const icons = [BadgePercent, ClipboardCheck, ShieldCheck, MessagesSquare];

  return (
    <div className="border-y border-line bg-paper/60">
      <Container>
        <ul aria-label={dict.trust.label} className="grid grid-cols-2 lg:grid-cols-4">
          {dict.trust.items.map((item, index) => {
            const Icon = icons[index];
            return (
              <li
                key={item.title}
                style={{ "--delay": `${index * 90}ms` } as React.CSSProperties}
                className="reveal flex items-center gap-3 border-line py-5 max-lg:odd:border-e max-lg:nth-[n+3]:border-t sm:gap-4 sm:py-6 lg:not-last:border-e lg:px-6 lg:first:ps-0 max-lg:odd:pe-3 max-lg:even:ps-4"
              >
                <Icon className="size-6 shrink-0 text-accent" strokeWidth={1.6} aria-hidden />
                <span className="leading-snug">
                  <span className="block text-sm font-semibold text-fg sm:text-base">{item.title}</span>
                  <span className="block text-xs text-muted sm:text-sm">{item.body}</span>
                </span>
              </li>
            );
          })}
        </ul>
      </Container>
    </div>
  );
}

export function Hero({ dict }: { dict: Dictionary }) {
  const hero = dict.hero;

  return (
    <section className="grain relative overflow-hidden">
      {/* soft morning light behind the arch */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-40 end-[-10%] size-[46rem] animate-drift rounded-full bg-[radial-gradient(closest-side,rgba(4,164,23,0.16),transparent)]"
      />
      {/* the logo's calligraphy engraved into both edges: its end on the right,
          its start on the left, each fading out before it reaches the content */}
      <SignatureMark
        className={`${signature} -right-72 [mask-image:linear-gradient(to_left,black_40%,transparent_72%)]`}
      />
      <SignatureMark
        className={`${signature} -left-10 [mask-image:linear-gradient(to_right,black_30%,transparent_55%)]`}
      />

      <Container className="relative grid items-center gap-14 pb-20 pt-10 sm:pt-14 lg:grid-cols-[1.2fr_1fr] lg:gap-8 lg:pb-24 lg:pt-16">
        <div>
          <p
            style={enter(0)}
            className="animate-fade-up inline-flex items-center gap-2.5 rounded-full border border-line bg-paper/80 px-3.5 py-1.5 text-xs font-medium text-fg/80 sm:text-sm">
            <span className="size-2 animate-pulse-ring rounded-full bg-brand" aria-hidden />
            {hero.badge}
          </p>

          <h1 className="mt-7 font-display text-[2.25rem] font-semibold min-[400px]:text-[2.6rem] leading-[1.08] tracking-tight text-fg sm:text-6xl lg:text-[4rem] xl:text-[4.4rem]">
            <span style={enter(100)} className="block animate-fade-up">
              {hero.titleLead}
            </span>
            <span style={enter(220)} className="relative inline-block animate-fade-up text-accent">
              {hero.titleHighlight}
              <Underline />
            </span>
          </h1>

          <p style={enter(340)} className="mt-7 max-w-xl animate-fade-up text-base leading-8 text-muted sm:text-lg sm:leading-8">
            {hero.subtitle}
          </p>

          <div style={enter(460)} className="animate-fade-up">
            <StoreButtons dict={dict} className="mt-9" />
          </div>

          <div style={enter(580)} className="mt-10 grid max-w-xl animate-fade-up gap-3 sm:grid-cols-2">
            <JumpLink
              icon={<KeyRound className="size-5" aria-hidden />}
              prompt={hero.tenantPrompt}
              label={hero.tenantLink}
              href="#tenants"
            />
            <JumpLink
              icon={<Building2 className="size-5" aria-hidden />}
              prompt={hero.ownerPrompt}
              label={hero.ownerLink}
              href="#owners"
            />
          </div>
        </div>

        {/* the doorway: phone stepping out of an arch */}
        <div className="relative mx-auto w-full max-w-[24rem] animate-fade-up-late sm:max-w-[28rem]">
          <div
            aria-hidden
            className="absolute inset-x-6 bottom-6 top-0 overflow-hidden rounded-t-full bg-linear-to-b from-moss via-pine to-pine sm:inset-x-12"
          >
            <ArchLines animated className="inset-x-0 bottom-0 h-full w-full text-white/15" count={5} />
            <OutlinedWordmark className="inset-x-0 bottom-6 text-center text-[11rem] [-webkit-text-stroke:1.5px_rgba(255,255,255,0.07)]" />
            <div className="absolute inset-x-0 top-0 h-1/2 bg-[radial-gradient(ellipse_at_50%_0%,rgba(127,224,141,0.28),transparent_70%)]" />
          </div>
          <div className="relative animate-float-slow pt-20 sm:pt-24">
            <PhoneMockup dict={dict} />
          </div>
        </div>
      </Container>

      <TrustStrip dict={dict} />
    </section>
  );
}
