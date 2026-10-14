import Link from "next/link";
import { Globe, LayoutDashboard } from "lucide-react";
import { otherLocale, type Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { SECTION_IDS } from "@/lib/sections";
import { Container } from "@/components/ui/Container";
import { Logo } from "@/components/ui/Logo";
import { ThemeToggle } from "./ThemeToggle";

export function SiteHeader({ lang, dict }: { lang: Locale; dict: Dictionary }) {
  const target = otherLocale(lang);
  const sections = [
    { label: dict.nav.features, id: SECTION_IDS.features },
    { label: dict.nav.howItWorks, id: SECTION_IDS.howItWorks },
    { label: dict.nav.why, id: SECTION_IDS.why },
    { label: dict.nav.faq, id: SECTION_IDS.faq },
  ];

  return (
    <header className="header-lift sticky top-0 z-40 border-b border-line/70 bg-sand/80 backdrop-blur-lg backdrop-saturate-150">
      {/* reading progress; only shown where scroll-driven animations exist */}
      <span
        aria-hidden
        className="scroll-progress absolute inset-x-0 -bottom-px hidden h-0.5 origin-left bg-linear-to-r from-brand-deep via-brand to-brand-soft rtl:origin-right"
      />
      <Container className="flex min-h-16 flex-wrap items-center justify-between gap-x-3 gap-y-2 py-3 sm:min-h-18 lg:flex-nowrap">
        <Link href={`/${lang}`} aria-label={dict.header.homeLabel} className="shrink-0 rounded-lg">
          <Logo size="sm" preload />
        </Link>

        <nav aria-label={dict.nav.label} className="max-lg:hidden">
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

        <div className="flex shrink-0 items-center gap-1 sm:gap-2">
          {/* Temporary shortcut to the dashboard. */}
          <Link
            href="/admin"
            aria-label={dict.header.adminDashboard}
            title={dict.header.adminDashboard}
            className="inline-flex min-h-9 items-center gap-2 rounded-full border border-line px-2.5 py-2 text-sm font-semibold text-accent transition-colors hover:bg-chip sm:px-4"
          >
            <LayoutDashboard className="size-4 shrink-0" aria-hidden />
            <span className="max-sm:sr-only">{dict.header.adminDashboard}</span>
          </Link>
          <ThemeToggle label={dict.header.toggleTheme} />
          <Link
            href={`/${target}`}
            hrefLang={target}
            lang={target}
            className="inline-flex items-center gap-1.5 rounded-full px-2 py-2 text-sm font-medium text-fg/80 sm:px-3 transition-colors hover:bg-sand-deep hover:text-fg"
          >
            <Globe className="size-4" strokeWidth={1.75} aria-hidden />
            {/* globe only on the narrowest phones; the label stays for screen readers */}
            <span className="max-[400px]:sr-only">{dict.header.switchLanguage}</span>
          </Link>
          <a
            href={`#${SECTION_IDS.download}`}
            className="whitespace-nowrap rounded-full bg-pine px-3.5 py-2 text-xs font-semibold text-white min-[400px]:text-sm transition-colors hover:bg-moss sm:px-5 dark:bg-brand dark:hover:bg-brand-hover"
          >
            {dict.header.getApp}
          </a>
        </div>
      </Container>
    </header>
  );
}
