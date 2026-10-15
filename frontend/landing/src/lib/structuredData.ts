import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import {
  BUSINESS,
  SITE_DESCRIPTION,
  SITE_NAME,
  SITE_NAME_AR,
  SITE_URL,
  SOCIAL_PROFILES,
  absoluteUrl,
  hasBusinessDetails,
} from "@/lib/site";

const ORGANIZATION_ID = `${SITE_URL}/#organization`;
const WEBSITE_ID = `${SITE_URL}/#website`;

function organization() {
  return {
    "@type": "Organization",
    "@id": ORGANIZATION_ID,
    name: SITE_NAME,
    alternateName: SITE_NAME_AR,
    url: SITE_URL,
    logo: absoluteUrl("/apple-icon.png"),
    description: SITE_DESCRIPTION,
    ...(SOCIAL_PROFILES.length > 0 && { sameAs: SOCIAL_PROFILES }),
  };
}

// Only emitted once BUSINESS in lib/site.ts is filled in (see the TODOs there).
function localBusiness() {
  const { address } = BUSINESS;
  return {
    "@type": "LocalBusiness",
    "@id": `${SITE_URL}/#localbusiness`,
    name: BUSINESS.legalName,
    url: SITE_URL,
    image: absoluteUrl("/apple-icon.png"),
    telephone: BUSINESS.telephone,
    ...(BUSINESS.email && { email: BUSINESS.email }),
    address: {
      "@type": "PostalAddress",
      streetAddress: address.streetAddress,
      addressLocality: address.addressLocality,
      ...(address.addressRegion && { addressRegion: address.addressRegion }),
      ...(address.postalCode && { postalCode: address.postalCode }),
      ...(address.addressCountry && { addressCountry: address.addressCountry }),
    },
    ...(BUSINESS.openingHours.length > 0 && { openingHours: BUSINESS.openingHours }),
    parentOrganization: { "@id": ORGANIZATION_ID },
  };
}

export function landingPageGraph(lang: Locale, dict: Dictionary) {
  const pageUrl = absoluteUrl(`/${lang}`);

  return {
    "@context": "https://schema.org",
    "@graph": [
      organization(),
      ...(hasBusinessDetails() ? [localBusiness()] : []),
      {
        "@type": "WebSite",
        "@id": WEBSITE_ID,
        url: SITE_URL,
        name: SITE_NAME,
        alternateName: SITE_NAME_AR,
        inLanguage: ["ar", "en"],
        publisher: { "@id": ORGANIZATION_ID },
      },
      {
        "@type": "WebPage",
        "@id": `${pageUrl}#webpage`,
        url: pageUrl,
        name: dict.meta.title,
        description: dict.meta.description,
        inLanguage: lang,
        isPartOf: { "@id": WEBSITE_ID },
        about: { "@id": ORGANIZATION_ID },
      },
      {
        "@type": "FAQPage",
        "@id": `${pageUrl}#faq`,
        url: pageUrl,
        inLanguage: lang,
        isPartOf: { "@id": `${pageUrl}#webpage` },
        mainEntity: dict.faq.items.map((item) => ({
          "@type": "Question",
          name: item.question,
          acceptedAnswer: { "@type": "Answer", text: item.answer },
        })),
      },
    ],
  };
}

// Escapes "<" so the payload can't close the <script> tag (per the Next.js JSON-LD guide).
export const serializeJsonLd = (data: unknown) => JSON.stringify(data).replace(/</g, "\\u003c");
