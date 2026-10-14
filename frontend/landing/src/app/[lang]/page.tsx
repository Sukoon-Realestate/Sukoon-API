import { notFound } from "next/navigation";
import { hasLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Hero } from "@/components/sections/Hero";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { WhySukoon } from "@/components/sections/WhySukoon";
import { Faq } from "@/components/sections/Faq";
import { FinalCta } from "@/components/sections/FinalCta";
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
        <HowItWorks dict={dict} />
        <WhySukoon dict={dict} />
        <Faq dict={dict} />
        <FinalCta dict={dict} />
      </main>
      <SiteFooter dict={dict} />
    </>
  );
}
