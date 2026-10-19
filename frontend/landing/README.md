# Sokoun merged public and administrative application

This Next.js application serves public Arabic/English pages and the administrative interface in the same build. `src/app/(landing)/[lang]` owns public routes; `src/app/(admin)/admin` owns `/admin`. There is no admin rewrite or required second zone.

The older standalone dashboard in `frontend/src/app` still builds separately with `basePath: /admin`. It is a compatibility build, not the process serving `/admin` when the merged application runs. Shared security fixes must cover both until that compatibility build is retired.

## Commands

- From `frontend`: `npm run dev` launches the merged application on port 3000. `-p` selects a different port.
- From `frontend/landing`: `npm run dev`, `npm run build`, `npm run start`, or `npm run lint` operate on this merged application.
- To run the compatibility dashboard explicitly, invoke `next dev --port 3001` from `frontend`; its routes include `/admin`.
- `ADMIN_URL` does not control routing in the merged application.

Live API mode is the default. Demo mode requires explicit `NEXT_PUBLIC_ENABLE_BACKEND=false` or `NEXT_PUBLIC_USE_MOCK_DATA=true`, and displays a demo banner. Live failures never fall back to demo records.

Public footer destinations use `NEXT_PUBLIC_PRIVACY_URL`, `NEXT_PUBLIC_TERMS_URL`, and `NEXT_PUBLIC_CONTACT_URL`. Only approved HTTPS URLs should be configured; absent destinations are visibly unavailable. No legal text or contact address is inferred.

## Structure

```
src/
  proxy.ts                 # "/" → "/ar" or "/en" based on Accept-Language
  i18n/
    config.ts              # locales, default (ar), direction helpers
    dictionaries.ts        # all copy (ar + en); en is typed against ar
  app/[lang]/              # root layout (html lang/dir, fonts) + page
  components/
    layout/                # SiteHeader, SiteFooter
    sections/              # Hero, HowItWorks, WhySukoon, Faq, FinalCta
    phone/                 # hero phone mockup + property illustrations
    ui/                    # Container, Logo, StoreButtons, GradientPill, SectionHeading, Decor
```

- Arabic is the default and renders RTL. Layout uses logical utilities (`start`/`end`, `ms`/`me`) so one markup mirrors correctly.
- To edit copy, change `dictionaries.ts`. Adding a key to `ar` without adding it to `en` is a type error.
- The FAQ uses native `<details name="faq">`, so the accordion needs no client JS.

## Open items

- `components/ui/Logo.tsx` is a text placeholder. Replace it with the official SVG wordmark.
- The store buttons are non-interactive ("coming soon"). Turn them into links once the store listings are live.
- Approved legal/contact destinations remain deployment configuration requirements; unavailable entries do not pretend to navigate.
- `lib/site.ts`: `SOCIAL_LINKS` supplies the footer's Instagram and TikTok links and the Organization schema's `sameAs` profiles. The `BUSINESS` details remain empty `TODO`s; the LocalBusiness schema switches on by itself once name, phone, street and city are filled in.

Run `rg -n "TODO" src` to list them all.

## SEO & metadata

The domain is `SITE_URL` in `src/lib/site.ts` (`https://sukoon.rent`). Canonicals, hreflang, the sitemap, robots, llms.txt, OG URLs and the JSON-LD are all built from it.

| URL | Source |
| --- | --- |
| `/sitemap.xml` | `app/sitemap.ts` (both locales + hreflang alternates) |
| `/robots.txt` | `app/robots.ts` (disallows `/admin`) |
| `/llms.txt` | `app/llms.txt/route.ts`, generated from the EN dictionary |
| `/[lang]/opengraph-image/share` | `app/[lang]/opengraph-image.tsx`, a 1200×630 share card rendered at build |
| `/favicon.ico`, `/icon.png`, `/apple-icon.png` | static files in `app/`, generated from `docs/brand/logo.png` |
| any unknown URL | `app/global-not-found.tsx` (bilingual, 404 + `noindex`) |

- The JSON-LD (`lib/structuredData.ts`) includes Organization, WebSite, WebPage and FAQPage, all built from the visible copy.
- The share card renders Arabic through HarfBuzz (`lib/og/shapeText.ts`). Satori, which `next/og` uses, can't order or measure Arabic text correctly. The fonts are in `src/assets/fonts/` (IBM Plex Sans Arabic, OFL).
- To regenerate the icons after a logo change, replace the three files in `app/` (the admin app keeps its own copy in `frontend/src/app/`).

## API connection

Use same-origin `/api/v1/*` calls with server-only `SOKOUN_API_PROXY_URL` set to the Django origin and an empty `NEXT_PUBLIC_API_URL`. Locale routing deliberately excludes API paths so POST bodies are forwarded without a redirect. The optional direct browser URL requires correctly configured backend CORS; the inspected deployment did not allow a localhost frontend. Real failures never fall back to demo records. Both frontend variants support the same proxy configuration.
