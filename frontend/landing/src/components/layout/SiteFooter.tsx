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
    <footer className="border-t border-white/10 bg-ink">
      <Container className="flex flex-col gap-6 py-8">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
          <Logo size="sm" />
          <nav aria-label={dict.nav.label}>
            <ul className="flex flex-wrap justify-center gap-x-5 gap-y-2 text-xs text-white/80">
              {sections.map((section) => (
                <li key={section.href}>
                  <a href={section.href} className="transition-colors hover:text-white">
                    {section.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="flex flex-col items-center gap-4 border-t border-white/10 pt-6 text-center sm:flex-row sm:justify-between sm:text-start">
          <nav aria-label={dict.footer.linksLabel}>
            <ul className="flex gap-5 text-xs text-white/80">
              {links.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="transition-colors hover:text-white">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
          <p className="text-xs text-white/50">{dict.footer.copyright}</p>
        </div>
      </Container>
    </footer>
  );
}
