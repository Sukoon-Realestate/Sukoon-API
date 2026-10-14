import type { Metadata } from "next";
import Link from "next/link";
import clsx from "clsx";
import "./globals.css";
import { getDictionary } from "@/i18n/dictionaries";
import { lexend, plexArabic } from "@/lib/fonts";
import { SITE_NAME } from "@/lib/site";
import { Logo } from "@/components/ui/Logo";
import { OutlinedWordmark } from "@/components/ui/Decor";

// Handles every unmatched URL. It renders outside the [lang] layout, so it
// can't know the visitor's locale and shows both languages instead.
const ar = getDictionary("ar").notFound;
const en = getDictionary("en").notFound;

export const metadata: Metadata = {
  title: `${en.title} · ${ar.title} – ${SITE_NAME}`,
  description: `${en.body} ${ar.body}`,
};

export default function GlobalNotFound() {
  return (
    <html
      lang="ar"
      dir="rtl"
      className={clsx(
        plexArabic.variable,
        lexend.variable,
        "[--font-primary:var(--font-arabic)] [--font-secondary:var(--font-latin)] antialiased",
      )}
    >
      <body className="min-h-dvh font-sans">
        <main className="relative isolate flex min-h-dvh flex-col items-center justify-center overflow-hidden bg-ink bg-[radial-gradient(ellipse_at_50%_115%,rgba(4,164,23,0.35),transparent_60%)] px-5 py-16 text-center">
          <OutlinedWordmark className="inset-x-0 -bottom-24 -z-10 text-center text-[18rem] sm:text-[30rem]" />

          <Link href="/ar" aria-label={getDictionary("ar").header.homeLabel} className="rounded-md">
            <Logo preload />
          </Link>

          <p
            dir="ltr"
            className="mt-10 font-[family-name:var(--font-latin)] text-7xl font-bold leading-none tracking-tighter text-brand sm:text-8xl"
          >
            404
          </p>

          <h1 className="mt-6 text-3xl font-bold leading-tight text-white sm:text-4xl">
            <span className="block">{ar.title}</span>
            <span lang="en" dir="ltr" className="mt-1 block font-[family-name:var(--font-latin)] text-xl font-semibold text-white/70 sm:text-2xl">
              {en.title}
            </span>
          </h1>

          <p className="mt-5 max-w-md text-sm leading-7 text-white/65 sm:text-base">{ar.body}</p>
          <p lang="en" dir="ltr" className="max-w-md font-[family-name:var(--font-latin)] text-sm leading-7 text-white/65 sm:text-base">
            {en.body}
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              href="/ar"
              hrefLang="ar"
              className="rounded-full bg-brand px-5 py-2.5 text-sm font-semibold text-heading transition-colors hover:bg-brand-hover"
            >
              {ar.cta}
            </Link>
            <Link
              href="/en"
              hrefLang="en"
              lang="en"
              dir="ltr"
              className="rounded-full border border-white/15 px-5 py-2.5 font-[family-name:var(--font-latin)] text-sm font-medium text-white transition-colors hover:bg-white/10"
            >
              {en.cta}
            </Link>
          </div>
        </main>
      </body>
    </html>
  );
}
