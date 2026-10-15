# Sukoon Landing Page

Marketing site for the Sukoon app. It's a standalone Next.js app that lives under `frontend/` and is fully separate from the admin dashboard: it has its own `package.json`, its own build and its own deploy.

Frontend only: no API calls, no auth. Both locales are statically prerendered.

## Routing: landing at `/`, admin at `/admin`

The landing page and the admin dashboard are two separate Next.js apps served under one origin, using Next.js [multi-zones](https://nextjs.org/docs/app/guides/multi-zones):

| URL | Served by |
|---|---|
| `/`, `/ar`, `/en` | this app (port 3000) |
| `/admin`, `/admin/*` | admin app (`frontend/`, `basePath: '/admin'`, port 3001), proxied by the rewrites in `next.config.ts` |

- `ADMIN_URL` (default `http://localhost:3001`) tells this app where the admin app runs. Set it to the admin deployment's URL in production. It's read when the server starts, so changing it needs a restart or rebuild.
- Links from this app to the admin must be plain `<a href="/admin">`, not `<Link>`, because moving between zones needs a full page load.

## Commands

Local development uses Webpack to work around Turbopack's `No link element found for chunk ...css` hot reload error. Both `npm run dev` here and the parent frontend launcher apply this option; production builds keep their existing bundler. After switching an already-open browser session, reload the page to discard the old Turbopack runtime.

```bash
# From frontend/ — runs both zones; open http://localhost:3000 and /admin
npm run dev

# This app only (/admin will fail without the admin server running)
cd landing && npm run dev
npm run build
npm run lint
```

From the repo root: `make frontend-dev` (both zones), plus `make landing-install`, `make landing-dev` and `make landing-build`.

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
- The footer links (Privacy / Terms / Contact) point to `#`. Each one has a `TODO` in `SiteFooter.tsx`.
- `lib/site.ts`: the `BUSINESS` details and `SOCIAL_PROFILES` are empty `TODO`s. The LocalBusiness schema switches on by itself once name, phone, street and city are filled in.

Run `grep -rn "TODO" src` to list them all.

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
