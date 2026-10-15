import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { Logo } from "@/components/ui/Logo";
import { StoreButtons } from "@/components/ui/StoreButtons";
import { ArchLines } from "@/components/ui/Decor";
import { SECTION_IDS } from "@/lib/sections";

export function FinalCta({ dict }: { dict: Dictionary }) {
  return (
    <section id={SECTION_IDS.download} className="scroll-mt-20 bg-sand pb-12 pt-16 sm:pb-16 sm:pt-20">
      <Container>
        <div className="reveal relative isolate overflow-hidden rounded-[2rem] bg-pine px-6 dark:ring-1 dark:ring-white/10 pb-16 pt-20 text-center sm:rounded-[2.75rem] sm:pb-20 sm:pt-24">
          <ArchLines animated count={7} className="parallax [--parallax:40px] inset-x-0 bottom-0 -z-10 mx-auto h-[115%] w-full text-brand-soft/15" />
          <div
            aria-hidden
            className="absolute inset-x-0 bottom-0 -z-10 h-2/3 bg-[radial-gradient(ellipse_at_50%_100%,rgba(4,164,23,0.4),transparent_65%)]"
          />

          <Logo size="lg" className="mx-auto block animate-float-slow brightness-125" />

          <h2 className="mx-auto mt-8 max-w-2xl font-display text-4xl font-semibold leading-tight tracking-tight text-white sm:text-6xl">
            {dict.finalCta.title}
          </h2>
          <p className="mx-auto mt-4 max-w-md text-base leading-7 text-white/65 sm:text-lg">{dict.finalCta.subtitle}</p>

          <StoreButtons dict={dict} tone="light" className="mt-10 justify-center" />
        </div>
      </Container>
    </section>
  );
}
