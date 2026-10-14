import type { Dictionary } from "@/i18n/dictionaries";
import { SECTION_IDS } from "@/lib/sections";
import { Container } from "@/components/ui/Container";
import { Logo } from "@/components/ui/Logo";

export function SiteFooter({ dict }: { dict: Dictionary }) {
  const sections = [
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
