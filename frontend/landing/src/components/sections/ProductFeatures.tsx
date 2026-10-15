import Image from "next/image";
import { ArrowDown, Check } from "lucide-react";
import clsx from "clsx";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { SECTION_IDS } from "@/lib/sections";
import { IPhoneFrame } from "@/components/phone/IPhoneFrame";

const screens = ["discovery", "shortlist", "viewings", "owners", "conversations", "notifications", "reviews", "support"];

export function ProductFeatures({ dict }: { dict: Dictionary }) {
  const content = dict.features;
  return (
    <section id={SECTION_IDS.features} aria-labelledby="features-title" className="scroll-mt-20 bg-paper py-24 sm:py-32">
      <Container>
        <div id="features-title">
          <SectionHeading eyebrow={content.eyebrow} titleLines={content.titleLines} subtitle={content.subtitle} />
        </div>
        <div className="mt-16 space-y-16 sm:space-y-24">
          {content.items.map((item, index) => (
            <article key={item.title} className="reveal grid items-center gap-8 lg:grid-cols-2 lg:gap-20">
              <div className={clsx("max-w-xl", index % 2 === 1 && "lg:order-2")}>
                <p className="flex items-center gap-3 text-xs font-semibold uppercase tracking-widest text-accent">
                  <span className="grid size-9 place-items-center rounded-full border border-line tabular-nums">{String(index + 1).padStart(2, "0")}</span>
                  {item.audience}
                </p>
                <h3 className="mt-5 font-display text-3xl font-semibold leading-tight tracking-tight text-fg sm:text-4xl">{item.title}</h3>
                <p className="mt-5 text-base leading-8 text-muted sm:text-lg">{item.body}</p>
                <ul className="mt-6 space-y-3">
                  {item.points.map((point) => (
                    <li key={point} className="flex items-start gap-3 text-sm leading-7 text-fg sm:text-base">
                      <Check aria-hidden className="mt-1.5 size-4 shrink-0 text-accent" />
                      {point}
                    </li>
                  ))}
                </ul>
                <a href={`#${SECTION_IDS.download}`} className="mt-7 inline-flex items-center gap-2 rounded-full border border-line px-5 py-3 text-sm font-semibold text-accent transition-colors hover:bg-chip">
                  {content.cta}<ArrowDown aria-hidden className="size-4" />
                </a>
              </div>
              <figure className={clsx("relative overflow-hidden rounded-[2rem] border border-line bg-sand px-6 pt-8 text-center sm:pt-10", index % 2 === 1 && "lg:order-1")}>
                <div aria-hidden className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(4,164,23,0.12),transparent_70%)]" />
                <IPhoneFrame>
                  <Image unoptimized src={`/images/app/${screens[index]}-light.png`} alt={item.imageAlt} width={390} height={844} className="block h-auto w-full dark:hidden" />
                  <Image unoptimized src={`/images/app/${screens[index]}-dark.png`} alt="" aria-hidden width={390} height={844} className="hidden h-auto w-full dark:block" />
                </IPhoneFrame>
                <figcaption className="relative mx-auto max-w-sm py-5 text-xs leading-5 text-muted">{content.caption}</figcaption>
              </figure>
            </article>
          ))}
        </div>
      </Container>
    </section>
  );
}
