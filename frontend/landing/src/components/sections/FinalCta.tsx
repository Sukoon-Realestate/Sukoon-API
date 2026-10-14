import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { Logo } from "@/components/ui/Logo";
import { StoreButtons } from "@/components/ui/StoreButtons";
import { OutlinedWordmark } from "@/components/ui/Decor";
import { SECTION_IDS } from "@/lib/sections";

export function FinalCta({ dict }: { dict: Dictionary }) {
  return (
    <section
      id={SECTION_IDS.download}
      className="relative scroll-mt-4 overflow-hidden bg-ink bg-[radial-gradient(ellipse_at_50%_115%,rgba(4,164,23,0.4),transparent_60%)] py-24 sm:py-28"
    >
      <OutlinedWordmark className="inset-x-0 -bottom-24 text-center text-[18rem] sm:text-[30rem]" />

      <Container className="relative flex flex-col items-center text-center">
        <span className="rounded-full bg-linear-to-br from-accent-pink to-accent-orange p-[3px]">
          <span className="grid size-20 place-items-center rounded-full bg-brand">
            <Logo size="sm" />
          </span>
        </span>

        <h2 className="mt-8 text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl">
          {dict.finalCta.title}
        </h2>
        <p className="mt-4 text-sm text-white/65 sm:text-base">{dict.finalCta.subtitle}</p>

        <StoreButtons dict={dict} className="mt-8 justify-center" />
      </Container>
    </section>
  );
}
