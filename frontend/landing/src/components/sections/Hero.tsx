import { ArrowRight } from "lucide-react";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { GradientPill } from "@/components/ui/GradientPill";
import { StoreButtons } from "@/components/ui/StoreButtons";
import { OutlinedWordmark } from "@/components/ui/Decor";
import { PhoneMockup } from "@/components/phone/PhoneMockup";

function JumpLink({ prompt, label, href }: { prompt: string; label: string; href: string }) {
  return (
    <p className="text-sm text-white/75">
      {prompt}{" "}
      <a href={href} className="group inline-flex items-center gap-1 font-semibold text-brand hover:text-brand-soft">
        {label}
        <ArrowRight
          className="size-3.5 transition-transform group-hover:translate-x-0.5 rtl:-scale-x-100 rtl:group-hover:-translate-x-0.5"
          aria-hidden
        />
      </a>
    </p>
  );
}

export function Hero({ dict }: { dict: Dictionary }) {
  const hero = dict.hero;

  return (
    <section className="relative">
      <OutlinedWordmark className="-top-10 end-[-6rem] text-[26rem] opacity-70 max-lg:hidden" />

      <Container className="relative grid items-center gap-16 pb-24 pt-8 lg:grid-cols-[1.1fr_1fr] lg:gap-10 lg:pb-32 lg:pt-12">
        <div className="animate-fade-up">
          <GradientPill>
            <span className="size-2 rounded-full bg-brand shadow-[0_0_0_3px_rgba(4,164,23,0.25)]" aria-hidden />
            {hero.badge}
          </GradientPill>

          <h1 className="mt-7 text-[2.75rem] font-bold leading-[1.1] tracking-tight text-white sm:text-6xl lg:text-[4.25rem]">
            <span className="block">{hero.titleLead}</span>
            <span className="block text-brand">{hero.titleHighlight}</span>
          </h1>

          <p className="mt-6 max-w-xl text-base leading-8 text-white/65 sm:text-lg">{hero.subtitle}</p>

          <StoreButtons dict={dict} className="mt-8" />

          <div className="mt-8 flex max-w-xl flex-col gap-3 border-t border-white/10 pt-6 sm:flex-row sm:flex-wrap sm:gap-x-8 lg:flex-col">
            <JumpLink prompt={hero.tenantPrompt} label={hero.tenantLink} href="#tenants" />
            <JumpLink prompt={hero.ownerPrompt} label={hero.ownerLink} href="#owners" />
          </div>
        </div>

        <PhoneMockup dict={dict} />
      </Container>
    </section>
  );
}
