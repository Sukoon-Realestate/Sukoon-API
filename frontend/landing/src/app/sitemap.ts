import type { MetadataRoute } from "next";
import { defaultLocale, locales } from "@/i18n/config";
import { absoluteUrl } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["", "/privacy", "/terms"].flatMap((path) => {
    const languages = {
      ...Object.fromEntries(locales.map((lang) => [lang, absoluteUrl(`/${lang}${path}`)])),
      "x-default": absoluteUrl(`/${defaultLocale}${path}`),
    };
    return locales.map((lang) => ({
      url: absoluteUrl(`/${lang}${path}`),
      changeFrequency: "monthly" as const,
      priority: path ? 0.5 : 1,
      alternates: { languages },
    }));
  });
}
