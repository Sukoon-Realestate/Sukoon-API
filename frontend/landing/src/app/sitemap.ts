import type { MetadataRoute } from "next";
import { defaultLocale, locales } from "@/i18n/config";
import { absoluteUrl } from "@/lib/site";

// TODO: add the privacy / terms pages here once they exist (see SiteFooter).
export default function sitemap(): MetadataRoute.Sitemap {
  const languages = {
    ...Object.fromEntries(locales.map((lang) => [lang, absoluteUrl(`/${lang}`)])),
    "x-default": absoluteUrl(`/${defaultLocale}`),
  };

  return locales.map((lang) => ({
    url: absoluteUrl(`/${lang}`),
    changeFrequency: "monthly",
    priority: 1,
    alternates: { languages },
  }));
}
