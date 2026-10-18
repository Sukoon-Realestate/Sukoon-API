// Single source for the public URL and brand facts used by metadata, sitemap,
// robots, llms.txt and structured data.

export const SITE_URL = "https://sukoon.rent";

export const SITE_NAME = "Sukoon";
export const SITE_NAME_AR = "سكون";

// Organization-level blurb for structured data; the per-locale page description lives in i18n/dictionaries.
export const SITE_DESCRIPTION =
  "Sukoon connects owners and tenants directly. Identity review and listing review are separate steps. Supported rental terms charge the owner 10% of first-period base rent, with 0% renewal commission and no tenant service fee.";

export const THEME_COLOR = "#f6f2e9";

export const absoluteUrl = (path = "/") => new URL(path, SITE_URL).toString();

// Shared by the footer and Organization structured data.
export const SOCIAL_LINKS = [
  { label: "Instagram", href: "https://www.instagram.com/suk_oon272/" },
  { label: "TikTok", href: "https://www.tiktok.com/@sukoon5026" },
];

export const SOCIAL_PROFILES: string[] = SOCIAL_LINKS.map((link) => link.href);

// TODO: fill in the registered business details. The LocalBusiness schema stays off
// until name, telephone and the street address + city are all set, so placeholder
// values never reach search engines.
export const BUSINESS = {
  // TODO: registered legal / trading name.
  legalName: "",
  // TODO: public phone in international format, e.g. "+20 2 1234 5678".
  telephone: "",
  // TODO: public contact email (also wire it into the footer "Contact us" link).
  email: "",
  address: {
    // TODO: street and building.
    streetAddress: "",
    // TODO: city, e.g. "Cairo".
    addressLocality: "",
    // TODO: governorate / region.
    addressRegion: "",
    // TODO: postal code.
    postalCode: "",
    // TODO: ISO 3166-1 alpha-2 country code, e.g. "EG".
    addressCountry: "",
  },
  // TODO: opening hours in schema.org format, e.g. ["Su-Th 09:00-17:00"].
  openingHours: [] as string[],
};

export const hasBusinessDetails = () =>
  Boolean(
    BUSINESS.legalName &&
      BUSINESS.telephone &&
      BUSINESS.address.streetAddress &&
      BUSINESS.address.addressLocality,
  );
