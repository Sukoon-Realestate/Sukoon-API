import Link from "next/link";
import { Globe } from "lucide-react";
import { otherLocale, type Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { SECTION_IDS } from "@/lib/sections";
import { Container } from "@/components/ui/Container";
import { Logo } from "@/components/ui/Logo";

export function SiteHeader({ lang, dict }: { lang: Locale; dict: Dictionary }) {
  const target = otherLocale(lang);
  const sections = [
    { label: dict.nav.howItWorks, id: SECTION_IDS.howItWorks },
    { label: dict.nav.why, id: SECTION_IDS.why },
    { label: dict.nav.faq, id: SECTION_IDS.faq },
  ];

  return (
    <header className="relative z-20">
      <Container className="flex items-center justify-between gap-6 py-5">
        <Link href={`/${lang}`} aria-label={dict.header.homeLabel} className="rounded-md">
          <Logo />
        </Link>

        <nav aria-label={dict.nav.label} className="max-md:hidden">
          <ul className="flex items-center gap-7 text-sm text-white/75">
            {sections.map((section) => (
              <li key={section.id}>
                <a href={`#${section.id}`} className="transition-colors hover:text-white">
                  {section.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center gap-2.5">
          <Link
            href={`/${target}`}
            hrefLang={target}
            lang={target}
            className="inline-flex items-center gap-2 rounded-full border border-white/15 px-3.5 py-2 text-xs font-medium text-white transition-colors hover:bg-white/10"
          >
            <Globe className="size-4" strokeWidth={1.75} aria-hidden />
            {dict.header.switchLanguage}
          </Link>
          <a
            href={`#${SECTION_IDS.download}`}
            className="rounded-full bg-brand px-4 py-2 text-xs font-semibold text-heading transition-colors hover:bg-brand-hover sm:px-5"
          >
            {dict.header.getApp}
          </a>
        </div>
      </Container>
    </header>
  );
}
