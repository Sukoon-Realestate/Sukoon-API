import type { Metadata, Viewport } from "next";
import { notFound } from "next/navigation";
import clsx from "clsx";
import "../../globals.css";
import { defaultLocale, directionOf, hasLocale, locales } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { lexend, plexArabic, readex } from "@/lib/fonts";
import { SITE_NAME, SITE_URL, THEME_COLOR, THEME_COLOR_DARK } from "@/lib/site";
import { themeInitScript } from "@/lib/theme";
import { motionInitScript } from "@/lib/motion";
import { loadingInitScript } from "@/lib/loading";
import { Splash } from "@/components/ui/LogoLoader";

export const dynamicParams = false;

export function generateStaticParams() {
  return locales.map((lang) => ({ lang }));
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: THEME_COLOR },
    { media: "(prefers-color-scheme: dark)", color: THEME_COLOR_DARK },
  ],
};

export async function generateMetadata({ params }: LayoutProps<"/[lang]">): Promise<Metadata> {
  const { lang } = await params;
  if (!hasLocale(lang)) return {};
  const dict = getDictionary(lang);

  return {
    metadataBase: new URL(SITE_URL),
    title: dict.meta.title,
    description: dict.meta.description,
    applicationName: SITE_NAME,
    alternates: {
      canonical: `/${lang}`,
      languages: { ar: "/ar", en: "/en", "x-default": `/${defaultLocale}` },
    },
    openGraph: {
      title: dict.meta.title,
      description: dict.meta.description,
      url: `/${lang}`,
      siteName: SITE_NAME,
      locale: lang === "ar" ? "ar_EG" : "en_US",
      alternateLocale: lang === "ar" ? "en_US" : "ar_EG",
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: dict.meta.title,
      description: dict.meta.description,
    },
  };
}

export default async function LocaleLayout({ children, params }: LayoutProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();

  return (
    <html
      lang={lang}
      dir={directionOf(lang)}
      // The init scripts set data-theme / data-motion before hydration.
      suppressHydrationWarning
      className={clsx(
        plexArabic.variable,
        lexend.variable,
        readex.variable,
        // Arabic pages lead with Plex Arabic; English pages lead with Lexend.
        lang === "ar"
          ? "[--font-primary:var(--font-arabic)] [--font-secondary:var(--font-latin)]"
          : "[--font-primary:var(--font-latin)] [--font-secondary:var(--font-arabic)]",
        "antialiased",
      )}
    >
      <head>
        {/* ! Plain inline script on purpose: it must run during HTML parsing so the theme
            never flashes. next/script "beforeInteractive" only queues inline code until the
            main bundle loads. React may log a dev-only warning when HMR re-renders this layout. */}
        <script dangerouslySetInnerHTML={{ __html: themeInitScript + motionInitScript + loadingInitScript }} />
      </head>
      <body className="min-h-dvh bg-sand font-sans">
        <Splash label={getDictionary(lang).loading} />
        {children}
      </body>
    </html>
  );
}
