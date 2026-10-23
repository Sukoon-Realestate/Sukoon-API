import { ArrowDown, Check } from "lucide-react";
import type { Locale } from "@/i18n/config";
import { FeaturePhoneScreen } from "@/components/phone/FeaturePhoneScreen";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { SECTION_IDS } from "@/lib/sections";
import { IPhoneFrame } from "@/components/phone/IPhoneFrame";
import { SignatureMark, WideSignature } from "@/components/ui/Decor";
import { FeatureCarousel } from "./FeatureCarousel";

// Staggers the slide-entrance animation (see .feature-slide in globals.css).
const delay = (ms: number) => ({ "--d": `${ms}ms` }) as React.CSSProperties;

export function ProductFeatures({ dict, lang }: { dict: Dictionary; lang: Locale }) {
  const content = dict.features;
  return (
    <section id={SECTION_IDS.features} aria-labelledby="features-title" data-animate className="relative isolate scroll-mt-20 overflow-hidden bg-paper py-24 sm:py-32">
      <WideSignature className="parallax top-1/2 -z-10 -translate-y-[42%] [--parallax:70px]" />
      <Container>
        <div id="features-title">
          <SectionHeading eyebrow={content.eyebrow} titleLines={content.titleLines} subtitle={content.subtitle} />
        </div>
        <FeatureCarousel
          key={lang}
          tabs={content.items.map((item) => item.audience)}
          labels={content.carousel}
          slides={content.items.map((item, index) => (
            <article key={item.title} className="grid items-center gap-8 lg:grid-cols-2 lg:gap-20">
              <div className="max-w-xl">
                <p className="slide-rise flex items-center gap-3 text-xs font-semibold uppercase tracking-widest text-accent">
                  <span className="grid size-9 place-items-center rounded-full border border-line tabular-nums">{String(index + 1).padStart(2, "0")}</span>
                  {item.audience}
                </p>
                <h3 style={delay(80)} className="slide-rise mt-5 font-display text-3xl font-semibold leading-tight tracking-tight text-fg sm:text-4xl">{item.title}</h3>
                <p style={delay(160)} className="slide-rise mt-5 text-base leading-8 text-muted sm:text-lg">{item.body}</p>
                <ul className="mt-6 space-y-3">
                  {item.points.map((point, pointIndex) => (
                    <li key={point} style={delay(240 + pointIndex * 70)} className="slide-rise flex items-start gap-3 text-sm leading-7 text-fg sm:text-base">
                      <Check aria-hidden className="mt-1.5 size-4 shrink-0 text-accent" />
                      {point}
                    </li>
                  ))}
                </ul>
                <a href={`#${SECTION_IDS.download}`} style={delay(480)} className="slide-rise mt-7 inline-flex items-center gap-2 rounded-full border border-line px-5 py-3 text-sm font-semibold text-accent transition-colors hover:bg-chip">
                  {content.cta}<ArrowDown aria-hidden className="size-4" />
                </a>
              </div>
              <figure className="relative px-6 pt-8 text-center sm:pt-10">
                <div aria-hidden className="slide-glow absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(4,164,23,0.12),transparent_70%)]" />
                {/* the whole word stamped behind the phone; it redraws each time its slide comes in.
                    Hidden where the section's WideSignature takes over, so the two never overlap. */}
                <SignatureMark draw className="min-[1700px]:hidden inset-x-0 top-[42%] w-full -translate-y-1/2 text-brand-deep/25 [--sig-fill:0.14] dark:text-brand/30 dark:[--sig-fill:0]" />
                <div className="slide-phone relative">
                  <IPhoneFrame>
                    <FeaturePhoneScreen index={index} lang={lang} />
                  </IPhoneFrame>
                </div>
                <figcaption className="relative mx-auto max-w-sm py-5 text-xs leading-5 text-muted">{content.caption}</figcaption>
              </figure>
            </article>
          ))}
        />
      </Container>
    </section>
  );
}
