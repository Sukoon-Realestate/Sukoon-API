export const locales = ["ar", "en"] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "ar";

export const hasLocale = (value: string): value is Locale =>
  (locales as readonly string[]).includes(value);

export const directionOf = (locale: Locale) => (locale === "ar" ? "rtl" : "ltr");

export const otherLocale = (locale: Locale): Locale => (locale === "ar" ? "en" : "ar");
