import Link from "next/link";
import { Globe } from "lucide-react";
import { otherLocale, type Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { SECTION_IDS } from "@/lib/sections";
import { Container } from "@/components/ui/Container";
import { Logo } from "@/components/ui/Logo";
import { ThemeToggle } from "./ThemeToggle";

export function SiteHeader({ lang, dict }: { lang: Locale; dict: Dictionary }) {
  const target = otherLocale(lang);
  const sections = [
    { label: dict.nav.howItWorks, id: SECTION_IDS.howItWorks },
    { label: dict.nav.why, id: SECTION_IDS.why },
    { label: dict.nav.faq, id: SECTION_IDS.faq },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-sand/80 backdrop-blur-lg backdrop-saturate-150">
      <Container className="flex h-16 items-center justify-between gap-6 sm:h-18">
        <Link href={`/${lang}`} aria-label={dict.header.homeLabel} className="rounded-lg">
          <Logo size="sm" preload />
        </Link>

        <nav aria-label={dict.nav.label} className="max-md:hidden">
          <ul className="flex items-center gap-1 text-sm font-medium text-fg/70">
            {sections.map((section) => (
              <li key={section.id}>
                <a
                  href={`#${section.id}`}
                  className="rounded-full px-4 py-2 transition-colors hover:bg-sand-deep hover:text-fg"
                >
                  {section.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <ThemeToggle label={dict.header.toggleTheme} />
          <Link
            href={`/${target}`}
            hrefLang={target}
            lang={target}
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-medium text-fg/80 transition-colors hover:bg-sand-deep hover:text-fg"
          >
            <Globe className="size-4" strokeWidth={1.75} aria-hidden />
            {dict.header.switchLanguage}
          </Link>
          <a
            href={`#${SECTION_IDS.download}`}
            className="rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-moss sm:px-5 dark:bg-brand dark:hover:bg-brand-hover"
          >
            {dict.header.getApp}
          </a>
        </div>
      </Container>
    </header>
  );
}
