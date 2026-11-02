import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { hasLocale, locales, type Locale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Logo } from "@/components/ui/Logo";
import { absoluteUrl, SITE_NAME } from "@/lib/site";

const documents = {
  privacy: { endpoint: "privacy-policy", en: "Privacy policy", ar: "سياسة الخصوصية" },
  terms: { endpoint: "terms", en: "Terms and conditions", ar: "الشروط والأحكام" },
} as const;
type Legal = keyof typeof documents;
type Props = { params: Promise<{ lang: string; legal: string }> };

export const dynamicParams = false;
export const revalidate = 3600;
export function generateStaticParams() {
  return locales.flatMap((lang) => Object.keys(documents).map((legal) => ({ lang, legal })));
}
function resolve(lang: string, legal: string): { lang: Locale; legal: Legal } {
  if (!hasLocale(lang) || !Object.hasOwn(documents, legal)) notFound();
  return { lang, legal: legal as Legal };
}
async function content(lang: Locale, legal: Legal) {
  // Same public, localized source used by the mobile legal screens. Never use
  // fixture policies or manufacture fallback legal promises when it is unavailable.
  const response = await fetch(`https://api.sukoon.rent/api/v1/pages/${documents[legal].endpoint}/`, {
    headers: { "Accept-Language": lang },
    next: { revalidate: 3600 },
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) throw new Error(`Legal content unavailable: ${response.status}`);
  const result: unknown = await response.json();
  const data = (result as { data?: { content?: unknown } })?.data;
  if (typeof data?.content !== "string" || !data.content.trim()) throw new Error("Legal content is empty");
  return data.content;
}
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { lang, legal } = await params;
  const route = resolve(lang, legal);
  const title = `${documents[route.legal][route.lang]} | ${SITE_NAME}`;
  const descriptions = {
    privacy: {
      en: "How Sukoon uses account details and identity documents to operate accounts and rental services.",
      ar: "كيف يستخدم سكون بيانات الحساب ومستندات الهوية لتشغيل الحسابات وخدمات الإيجار.",
    },
    terms: {
      en: "Read Sukoon's terms for using accounts and rental services.",
      ar: "اقرأ شروط سكون لاستخدام الحسابات وخدمات الإيجار.",
    },
  };
  const description = descriptions[route.legal][route.lang];
  const path = `/${route.lang}/${route.legal}`;
  return {
    title, description,
    alternates: { canonical: path, languages: { ar: `/ar/${route.legal}`, en: `/en/${route.legal}` } },
    openGraph: { title, description, url: absoluteUrl(path), type: "website", siteName: SITE_NAME },
    twitter: { card: "summary_large_image", title, description },
  };
}
export default async function LegalPage({ params }: Props) {
  const { lang: rawLang, legal: rawLegal } = await params;
  const { lang, legal } = resolve(rawLang, rawLegal);
  const title = documents[legal][lang];
  const text = await content(lang, legal);
  return <>
    <header className="border-b border-line px-5 py-4 sm:px-8">
      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-4">
        <Link href={`/${lang}`} aria-label={getDictionary(lang).header.homeLabel} className="inline-flex min-h-11 items-center"><Logo size="sm" /></Link>
        <Link href={`/${lang === "ar" ? "en" : "ar"}/${legal}`} hrefLang={lang === "ar" ? "en" : "ar"} className="inline-flex min-h-11 items-center rounded-xl border border-line px-4 font-semibold focus-visible:outline-2 focus-visible:outline-offset-4">{lang === "ar" ? "English" : "العربية"}</Link>
      </div>
    </header>
    <main className="mx-auto max-w-3xl px-5 py-8 sm:px-8 sm:py-12">
      <nav aria-label={lang === "ar" ? "مسار الصفحة" : "Breadcrumb"} className="mb-6 flex flex-wrap items-center gap-2 text-sm text-fg">
        <Link href={`/${lang}`} className="inline-flex min-h-11 items-center underline underline-offset-4">{lang === "ar" ? "الرئيسية" : "Home"}</Link>
        <span aria-hidden="true">/</span><span aria-current="page">{title}</span>
      </nav>
      <h1 className="mb-8 text-3xl font-bold leading-snug text-fg sm:text-4xl">{title}</h1>
      <article className="space-y-8 wrap-break-word text-base leading-8 text-fg">
        {text.split(/\n\s*\n/).map((section, index) => {
          const [heading, ...body] = section.split("\n");
          return <section key={index}>
            {body.length > 0 ? <><h2 className="mb-2 text-lg font-semibold">{heading}</h2><p className="whitespace-pre-wrap">{body.join("\n")}</p></> : <p>{heading}</p>}
          </section>;
        })}
      </article>
      <Link href={`/${lang}`} className="mt-10 inline-flex min-h-11 items-center rounded-xl bg-fg px-5 py-3 font-semibold text-sand focus-visible:outline-2 focus-visible:outline-offset-4">{lang === "ar" ? "العودة إلى سكون" : "Return to Sukoon"}</Link>
    </main>
    <SiteFooter dict={getDictionary(lang)} lang={lang} />
  </>;
}
