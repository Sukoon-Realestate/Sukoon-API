import { Minus, Plus } from "lucide-react";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { SECTION_IDS } from "@/lib/sections";

// Native <details name> gives an exclusive accordion with no client JS.
export function Faq({ dict }: { dict: Dictionary }) {
  const faq = dict.faq;

  return (
    <section id={SECTION_IDS.faq} className="bg-mint py-20 sm:py-24">
      <Container className="grid gap-10 lg:grid-cols-[1fr_1.6fr] lg:gap-16">
        <SectionHeading eyebrow={faq.eyebrow} titleLines={[faq.title]} subtitle={faq.subtitle} />

        <div className="space-y-2.5">
          {faq.items.map((item, index) => (
            <details
              key={item.question}
              name="faq"
              open={index === 0}
              className="group rounded-2xl border border-black/8 bg-white px-5 transition-shadow open:shadow-sm"
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-4 text-sm font-semibold text-heading sm:text-base">
                {item.question}
                <Plus className="size-4 shrink-0 text-brand-deep group-open:hidden" aria-hidden />
                <Minus className="hidden size-4 shrink-0 text-brand-deep group-open:block" aria-hidden />
              </summary>
              <p className="pb-5 text-sm leading-7 text-body">{item.answer}</p>
            </details>
          ))}
        </div>
      </Container>
    </section>
  );
}
