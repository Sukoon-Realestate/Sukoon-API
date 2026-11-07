import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { hasLocale, locales, type Locale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Logo } from "@/components/ui/Logo";
import { AccountDeletionContent, PolicyDetails, SupportContent } from "@/components/public-pages/HelpContent";
import { publicHelp } from "@/i18n/public-help";
import { publicPageKeys, publicPages, type PublicPage } from "@/lib/public-pages";
import { absoluteUrl, SITE_NAME } from "@/lib/site";

type Props = { params: Promise<{ lang: string; legal: string }> };

export const dynamicParams = false;
export const revalidate = 3600;
export function generateStaticParams() {
  return locales.flatMap((lang) => publicPageKeys.map((legal) => ({ lang, legal })));
}
function resolve(lang: string, legal: string): { lang: Locale; legal: PublicPage } {
  if (!hasLocale(lang) || !Object.hasOwn(publicPages, legal)) notFound();
  return { lang, legal: legal as PublicPage };
}
async function content(lang: Locale, legal: "privacy" | "terms") {
  // Same public, localized source used by the mobile legal screens. Never use
  // fixture policies or manufacture fallback legal promises when it is unavailable.
  const endpoint = legal === "privacy" ? "privacy-policy" : "terms";
  const response = await fetch(`https://api.sukoon.rent/api/v1/pages/${endpoint}/`, {
    headers: { "Accept-Language": lang },
    next: { revalidate: 3600 },
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) throw new Error(`Legal content unavailable: ${response.status}`);
  const result: unknown = await response.json();
  const data = (result as { data?: { content?: unknown; updated_at?: unknown; revision?: unknown } })?.data;
  if (typeof data?.content !== "string" || !data.content.trim()) throw new Error("Legal content is empty");
  return {
    text: data.content,
    updatedAt: typeof data.updated_at === "string" && Number.isFinite(Date.parse(data.updated_at)) ? data.updated_at : null,
    revision: typeof data.revision === "number" && Number.isInteger(data.revision) ? data.revision : null,
  };
}
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { lang, legal } = await params;
  const route = resolve(lang, legal);
  const title = `${publicPages[route.legal].title[route.lang]} | ${SITE_NAME}`;
  const description = publicPages[route.legal].description[route.lang];
  const path = `/${route.lang}/${route.legal}`;
  return {
    title, description,
    alternates: { canonical: path, languages: { ar: `/ar/${route.legal}`, en: `/en/${route.legal}`, "x-default": `/ar/${route.legal}` } },
    openGraph: { title, description, url: absoluteUrl(path), type: "website", siteName: SITE_NAME },
    twitter: { card: "summary_large_image", title, description },
  };
}
export default async function LegalPage({ params }: Props) {
  const { lang: rawLang, legal: rawLegal } = await params;
  const { lang, legal } = resolve(rawLang, rawLegal);
  const title = publicPages[legal].title[lang];
  const copy = publicHelp[lang];
  const document = legal === "privacy" || legal === "terms" ? await content(lang, legal) : null;
  return <>
    <header className="border-b border-line px-5 py-4 sm:px-8">
      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-4">
        <Link href={`/${lang}`} aria-label={getDictionary(lang).header.homeLabel} className="inline-flex min-h-11 items-center"><Logo size="sm" /></Link>
        <Link href={`/${lang === "ar" ? "en" : "ar"}/${legal}`} hrefLang={lang === "ar" ? "en" : "ar"} className="inline-flex min-h-11 items-center rounded-xl border border-line px-4 font-semibold focus-visible:outline-2 focus-visible:outline-offset-4">{lang === "ar" ? "English" : "العربية"}</Link>
      </div>
      <nav aria-label={copy.navigation} className="mx-auto mt-4 flex max-w-3xl flex-wrap gap-x-5 gap-y-1 border-t border-line pt-2 text-sm text-muted">
        {publicPageKeys.map((page) => <Link key={page} href={`/${lang}/${page}`} aria-current={page === legal ? "page" : undefined} className="inline-flex min-h-11 items-center rounded-lg underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 aria-[current=page]:font-semibold aria-[current=page]:text-accent aria-[current=page]:underline">{copy.links[page]}</Link>)}
      </nav>
    </header>
    <main className="mx-auto max-w-3xl px-5 py-8 sm:px-8 sm:py-12">
      <nav aria-label={lang === "ar" ? "مسار الصفحة" : "Breadcrumb"} className="mb-6 flex flex-wrap items-center gap-2 text-sm text-fg">
        <Link href={`/${lang}`} className="inline-flex min-h-11 items-center underline underline-offset-4">{lang === "ar" ? "الرئيسية" : "Home"}</Link>
        <span aria-hidden="true">/</span><span aria-current="page">{title}</span>
      </nav>
      <h1 className="mb-8 text-3xl font-bold leading-snug text-fg sm:text-4xl">{title}</h1>
      {document && <>
      {(document.updatedAt || document.revision !== null) && <p className="-mt-4 mb-8 flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted">
        {document.updatedAt && <span>{copy.updated}: <time dateTime={document.updatedAt}>{new Intl.DateTimeFormat(lang === "ar" ? "ar-EG" : "en", { dateStyle: "long", timeZone: "UTC" }).format(new Date(document.updatedAt))}</time></span>}
        {document.revision !== null && <span>{copy.revision}: {document.revision}</span>}
      </p>}
      {legal === "privacy" && <PrivacyChoices lang={lang} />}
      <article className="space-y-8 wrap-break-word text-base leading-8 text-fg">
        {document.text.split(/\n\s*\n/).map((section, index) => {
          const [heading, ...body] = section.split("\n");
          return <section key={index}>
            {body.length > 0 ? <><h2 className="mb-2 text-lg font-semibold">{heading}</h2><p className="whitespace-pre-wrap">{body.join("\n")}</p></> : <p>{heading}</p>}
          </section>;
        })}
      </article>
      {legal === "privacy" && <div className="mt-9"><PolicyDetails lang={lang} /></div>}
      </>}
      {legal === "delete-account" && <AccountDeletionContent lang={lang} />}
      {legal === "support" && <SupportContent lang={lang} />}
      <Link href={`/${lang}`} className="mt-10 inline-flex min-h-11 items-center rounded-xl bg-fg px-5 py-3 font-semibold text-sand focus-visible:outline-2 focus-visible:outline-offset-4">{lang === "ar" ? "العودة إلى سكون" : "Return to Sukoon"}</Link>
    </main>
    <SiteFooter dict={getDictionary(lang)} lang={lang} />
  </>;
}

function PrivacyChoices({ lang }: { lang: Locale }) {
  const copy = publicHelp[lang];
  return <section id="data-deletion" className="mb-9 space-y-3 rounded-2xl border border-line bg-paper p-5 text-fg sm:p-6" aria-labelledby="privacy-choices-title">
    <h2 id="privacy-choices-title" className="text-lg font-semibold">{copy.privacyChoices}</h2>
    <p className="leading-7 text-muted">{copy.privacyBody}</p>
    <div className="flex flex-wrap gap-x-6 gap-y-1">
      <Link href={`/${lang}/delete-account`} className="inline-flex min-h-11 items-center font-semibold text-accent underline underline-offset-4">{copy.deletionLink}</Link>
      <Link href={`/${lang}/support`} className="inline-flex min-h-11 items-center font-semibold text-accent underline underline-offset-4">{copy.supportLink}</Link>
    </div>
  </section>;
}
