import type { Dictionary } from "@/i18n/dictionaries";
import { SECTION_IDS } from "@/lib/sections";
import { BUSINESS, SOCIAL_LINKS } from "@/lib/site";
import { Container } from "@/components/ui/Container";
import { Logo } from "@/components/ui/Logo";
import { SignatureMark } from "@/components/ui/Decor";

export function SiteFooter({ dict }: { dict: Dictionary }) {
  const sections = [
    { label: dict.nav.features, href: `#${SECTION_IDS.features}` },
    { label: dict.nav.howItWorks, href: `#${SECTION_IDS.howItWorks}` },
    { label: dict.nav.why, href: `#${SECTION_IDS.why}` },
    { label: dict.nav.faq, href: `#${SECTION_IDS.faq}` },
    { label: dict.nav.download, href: `#${SECTION_IDS.download}` },
  ];

  const destination = (value: string | undefined) => {
    if (!value) return undefined;
    try { const url = new URL(value); return url.protocol === 'https:' ? url.href : undefined; } catch { return undefined; }
  };
  const links = [
    { label: dict.footer.privacy, href: destination(process.env.NEXT_PUBLIC_PRIVACY_URL) },
    { label: dict.footer.terms, href: destination(process.env.NEXT_PUBLIC_TERMS_URL) },
    { label: dict.footer.contact, href: `mailto:${BUSINESS.email}` },
  ];

  return (
    <footer className="bg-sand">
      <Container className="flex flex-col gap-8 pb-10 pt-6">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-3">
            <Logo size="md" />
            <p className="font-display text-lg font-semibold text-fg">{dict.finalCta.title}</p>
          </div>
          <nav aria-label={dict.nav.label}>
            <ul className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-fg/70">
              {sections.map((section) => (
                <li key={section.href}>
                  <a href={section.href} className="transition-colors hover:text-fg">
                    {section.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <nav aria-label={dict.footer.socialLabel}>
          <ul className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-fg/70 sm:justify-start">
            {SOCIAL_LINKS.map((link) => (
              <li key={link.href}>
                <a
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-11 items-center gap-2 transition-colors hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-fg"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="size-5 shrink-0"
                    aria-hidden="true"
                  >
                    {link.label === "Instagram" ? (
                      <>
                        <rect x="3" y="3" width="18" height="18" rx="5" />
                        <circle cx="12" cy="12" r="4" />
                        <circle cx="17.5" cy="6.5" r="0.5" />
                      </>
                    ) : (
                      <path d="M14 3h3a5 5 0 0 0 4 4v3a8 8 0 0 1-4-1v7a6 6 0 1 1-6-6v3a3 3 0 1 0 3 3V3Z" />
                    )}
                  </svg>
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex flex-col items-center gap-4 rounded-2xl border-t border-line px-4 py-6 text-center transition-[background-color,box-shadow,border-color] duration-300 hover:border-brand/40 hover:bg-brand/5 hover:shadow-[0_0_32px_rgba(4,164,23,0.15)] focus-within:border-brand/40 focus-within:bg-brand/5 focus-within:shadow-[0_0_32px_rgba(4,164,23,0.15)] sm:flex-row sm:justify-between sm:text-start">
          <nav aria-label={dict.footer.linksLabel}>
            <ul className="flex gap-6 text-sm text-fg/70">
              {links.map((link) => (
                <li key={link.label}>
                  {link.href ? <a href={link.href} className="rounded-lg px-2 py-2 transition-[color,background-color,box-shadow] duration-300 hover:bg-brand/10 hover:text-accent hover:shadow-[0_0_20px_rgba(4,164,23,0.3)] focus-visible:bg-brand/10 focus-visible:text-accent focus-visible:shadow-[0_0_20px_rgba(4,164,23,0.3)] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand">{link.label}</a>
                    : <span aria-disabled="true" title={dict.footer.unavailableHelp}>{link.label} — {dict.footer.unavailable}</span>}
                </li>
              ))}
            </ul>
          </nav>
          <p className="text-sm text-fg/50">{dict.footer.copyright}</p>
        </div>
      </Container>
      {/* the page signs off: a large word cropped by the bottom edge, written in once in view */}
      <div data-animate aria-hidden className="mx-auto aspect-[1455/430] w-full max-w-6xl overflow-hidden px-5 sm:px-8">
        <SignatureMark draw className="relative! block w-full text-brand-deep/30 [--sig-fill:0.1] dark:text-brand/35 dark:[--sig-fill:0]" />
      </div>
    </footer>
  );
}
