import { Plus } from "lucide-react";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { SECTION_IDS } from "@/lib/sections";

// Native <details name> gives an exclusive accordion with no client JS.
export function Faq({ dict }: { dict: Dictionary }) {
  const faq = dict.faq;

  return (
    <section id={SECTION_IDS.faq} className="scroll-mt-16 bg-paper py-24 sm:py-32">
      <Container className="grid gap-12 lg:grid-cols-[1fr_1.5fr] lg:gap-20">
        <SectionHeading eyebrow={faq.eyebrow} titleLines={[faq.title]} subtitle={faq.subtitle} className="lg:sticky lg:top-28 lg:self-start" />

        <div className="reveal divide-y divide-line border-y border-line">
          {faq.items.map((item, index) => (
            <details key={item.question} name="faq" open={index === 0} className="group">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-6 py-6 font-display text-lg font-medium text-fg transition-colors hover:text-accent sm:text-xl">
                {item.question}
                <span className="grid size-9 shrink-0 place-items-center rounded-full border border-line text-accent transition-[transform,background-color,color] duration-300 group-open:rotate-45 group-open:border-pine group-open:bg-pine group-open:text-white dark:group-open:border-brand dark:group-open:bg-brand">
                  <Plus className="size-4" aria-hidden />
                </span>
              </summary>
              <p className="faq-answer max-w-2xl pb-6 pe-14 text-base leading-8 text-muted">{item.answer}</p>
            </details>
          ))}
        </div>
      </Container>
    </section>
  );
}
