import Link from "next/link";
import type { Locale } from "@/i18n/config";
import { publicHelp } from "@/i18n/public-help";
import { BUSINESS } from "@/lib/site";
import { contactMailto, deletionMailto } from "@/lib/public-pages";

const buttonClass = "inline-flex min-h-11 items-center justify-center rounded-xl bg-fg px-5 py-3 text-center font-semibold leading-6 text-sand focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-fg";
const sectionClass = "space-y-3 scroll-mt-6";
const headingClass = "text-xl font-semibold leading-snug text-fg";

export function PolicyDetails({ lang }: { lang: Locale }) {
  const text = publicHelp[lang].policyDetails;
  return <section id="policy-details" className="space-y-4 rounded-2xl border border-line bg-paper p-5 text-fg sm:p-6" aria-labelledby="policy-details-title">
    <h2 id="policy-details-title" className={headingClass}>{text.title}</h2>
    <p className="text-sm leading-6 text-muted">{text.draft}</p>
    <dl className="space-y-4 text-base leading-7">
      <div><dt className="font-semibold">{text.timingLabel}</dt><dd data-policy-placeholder="deletion-timing" className="mt-1 wrap-break-word text-muted">{text.timingPlaceholder}</dd></div>
      <div><dt className="font-semibold">{text.retentionLabel}</dt><dd data-policy-placeholder="data-retention" className="mt-1 wrap-break-word text-muted">{text.retentionPlaceholder}</dd></div>
    </dl>
  </section>;
}

function EmailCard({ lang, deletion = false }: { lang: Locale; deletion?: boolean }) {
  const copy = publicHelp[lang];
  const text = deletion ? copy.deletion : copy.support;
  return <section id="request" className="space-y-4 rounded-2xl border border-line bg-paper p-5 sm:p-7" aria-labelledby="request-title">
    <h2 id="request-title" className={headingClass}>{deletion ? copy.deletion.requestTitle : copy.support.emailTitle}</h2>
    <a href={deletion ? deletionMailto(lang) : contactMailto(copy.support.subject)} className={buttonClass}>{text.action}</a>
    <p className="text-sm leading-6 text-muted">{text.emailHint}</p>
    <p className="text-sm text-muted">{copy.emailLabel}<br /><a href={`mailto:${BUSINESS.email}`} dir="ltr" className="inline-flex min-h-11 items-center break-all text-base font-semibold text-accent underline underline-offset-4">{BUSINESS.email}</a></p>
    {deletion && <p>{copy.deletion.requestBody}</p>}
    {deletion && <p className="text-sm leading-6 text-muted">{copy.deletion.manualHint}</p>}
    <p className="border-t border-line pt-4 text-sm leading-6 text-muted">{text.safety}</p>
  </section>;
}

export function AccountDeletionContent({ lang }: { lang: Locale }) {
  const copy = publicHelp[lang];
  const text = copy.deletion;
  return <div className="space-y-9 text-base leading-8 text-fg">
    <p className="text-lg leading-8 text-muted">{text.intro}</p>
    <EmailCard lang={lang} deletion />
    <section className={sectionClass} aria-labelledby="in-app-title">
      <h2 id="in-app-title" className={headingClass}>{text.appTitle}</h2>
      <ol className="list-decimal space-y-2 ps-6">{text.appSteps.map((step) => <li key={step}>{step}</li>)}</ol>
      <p>{text.appNote}</p>
    </section>
    <section id="data-deletion" className={sectionClass} aria-labelledby="data-title">
      <h2 id="data-title" className={headingClass}>{text.dataTitle}</h2><p>{text.dataBody}</p>
    </section>
    <section id="retention" className={sectionClass} aria-labelledby="retention-title">
      <h2 id="retention-title" className={headingClass}>{text.retentionTitle}</h2><p>{text.retentionBody}</p>
      <Link href={`/${lang}/privacy`} className="inline-flex min-h-11 items-center text-accent underline underline-offset-4">{lang === "ar" ? "قراءة سياسة الخصوصية" : "Read the privacy policy"}</Link>
    </section>
    <PolicyDetails lang={lang} />
    <section className={sectionClass} aria-labelledby="next-title">
      <h2 id="next-title" className={headingClass}>{text.nextTitle}</h2><p>{text.nextBody}</p>
      <Link href={`/${lang}/support`} className="inline-flex min-h-11 items-center text-accent underline underline-offset-4">{copy.supportLink}</Link>
    </section>
  </div>;
}

export function SupportContent({ lang }: { lang: Locale }) {
  const text = publicHelp[lang].support;
  return <div className="space-y-9 text-base leading-8 text-fg">
    <p className="text-lg leading-8 text-muted">{text.intro}</p>
    <EmailCard lang={lang} />
    <section className={sectionClass} aria-labelledby="details-title">
      <h2 id="details-title" className={headingClass}>{text.detailsTitle}</h2>
      <ul className="list-disc space-y-2 ps-6">{text.details.map((detail) => <li key={detail}>{detail}</li>)}</ul>
    </section>
    <section className={sectionClass} aria-labelledby="topics-title">
      <h2 id="topics-title" className={headingClass}>{text.topicsTitle}</h2>
      <div className="grid gap-3 sm:grid-cols-3">{text.topics.map((topic) => <Link key={topic.page} href={`/${lang}/${topic.page}`} className="rounded-xl border border-line bg-paper p-4 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-fg">
        <h3 className="font-semibold text-accent underline underline-offset-4">{topic.title}</h3>
        <p className="mt-2 text-sm leading-6 text-muted">{topic.body}</p>
      </Link>)}</div>
    </section>
    <section className={sectionClass} aria-labelledby="report-title">
      <h2 id="report-title" className={headingClass}>{text.reportTitle}</h2><p>{text.reportBody}</p>
    </section>
  </div>;
}
