import { notFound } from "next/navigation";
import { hasLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Hero } from "@/components/sections/Hero";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { WhySukoon } from "@/components/sections/WhySukoon";
import { ProductFeatures } from "@/components/sections/ProductFeatures";
import { Faq } from "@/components/sections/Faq";
import { FinalCta } from "@/components/sections/FinalCta";
import { TestSubscription } from "@/components/sections/TestSubscription";
import { InViewObserver } from "@/components/layout/InViewObserver";
import { landingPageGraph, serializeJsonLd } from "@/lib/structuredData";

export default async function LandingPage({ params }: PageProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const dict = getDictionary(lang);

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: serializeJsonLd(landingPageGraph(lang, dict)) }}
      />
      <SiteHeader lang={lang} dict={dict} />
      <main>
        <Hero dict={dict} />
        {/* Order matches the header nav (lib/sections.ts), so each nav link lands on the section it names. */}
        <ProductFeatures dict={dict} lang={lang} />
        <HowItWorks dict={dict} />
        <WhySukoon dict={dict} />
        <TestSubscription lang={lang} />
        <Faq dict={dict} />
        <FinalCta dict={dict} />
      </main>
      <SiteFooter dict={dict} />
      <InViewObserver />
    </>
  );
}
