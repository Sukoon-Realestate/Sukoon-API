import type { Dictionary } from "@/i18n/dictionaries";
import { SECTION_IDS } from "@/lib/sections";
import { SOCIAL_LINKS } from "@/lib/site";
import { Container } from "@/components/ui/Container";
import { Logo } from "@/components/ui/Logo";

export function SiteFooter({ dict }: { dict: Dictionary }) {
  const sections = [
    { label: dict.nav.features, href: `#${SECTION_IDS.features}` },
    { label: dict.nav.howItWorks, href: `#${SECTION_IDS.howItWorks}` },
    { label: dict.nav.why, href: `#${SECTION_IDS.why}` },
    { label: dict.nav.faq, href: `#${SECTION_IDS.faq}` },
    { label: dict.nav.download, href: `#${SECTION_IDS.download}` },
  ];

  const links = [
    // TODO: create the privacy policy page (/[lang]/privacy), link it here and add it to sitemap.ts.
    { label: dict.footer.privacy, href: "#" },
    // TODO: create the terms of use page (/[lang]/terms), link it here and add it to sitemap.ts.
    { label: dict.footer.terms, href: "#" },
    // TODO: point at the real contact channel (mailto: with BUSINESS.email in lib/site.ts, or a /contact page).
    { label: dict.footer.contact, href: "#" },
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

        <div className="flex flex-col items-center gap-4 border-t border-line pt-6 text-center sm:flex-row sm:justify-between sm:text-start">
          <nav aria-label={dict.footer.linksLabel}>
            <ul className="flex gap-6 text-sm text-fg/70">
              {links.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="transition-colors hover:text-fg">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
          <p className="text-sm text-fg/50">{dict.footer.copyright}</p>
        </div>
      </Container>
    </footer>
  );
}
