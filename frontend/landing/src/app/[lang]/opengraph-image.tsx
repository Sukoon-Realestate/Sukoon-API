import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";
import { hasLocale, type Locale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { shapeLine } from "@/lib/og/shapeText";
import { SITE_URL } from "@/lib/site";

// Social share card (Open Graph; X falls back to it too). Prerendered per locale at build.

const size = { width: 1200, height: 630 };
const fontsDir = join(process.cwd(), "src/assets/fonts");
const logoPath = join(process.cwd(), "src/assets/brand/logo.png");
const LOGO_SIZE = 112;

const WHITE = "#ffffff";
const BRAND = "#04a417";
const TITLE_SIZE = 76;

const localeOf = async (params: Promise<{ lang: string }>): Promise<Locale> => {
  const { lang } = await params;
  return hasLocale(lang) ? lang : "ar";
};

export async function generateImageMetadata({ params }: { params: Promise<{ lang: string }> }) {
  const lang = await localeOf(params);
  return [{ id: "share", alt: getDictionary(lang).meta.ogAlt, size, contentType: "image/png" }];
}

export default async function OpengraphImage({ params }: { params: Promise<{ lang: string }> }) {
  const lang = await localeOf(params);
  const { hero } = getDictionary(lang);
  const rtl = lang === "ar";
  const [bold, medium, logo] = await Promise.all([
    readFile(join(fontsDir, "IBMPlexSansArabic-Bold.ttf")),
    readFile(join(fontsDir, "IBMPlexSansArabic-Medium.ttf")),
    readFile(logoPath),
  ]);
  const logoSrc = `data:image/png;base64,${logo.toString("base64")}`;

  // Every Arabic string goes through HarfBuzz (see lib/og/shapeText.ts).
  const arabicTitle = rtl
    ? await Promise.all([shapeLine(bold, hero.titleLead, TITLE_SIZE, WHITE), shapeLine(bold, hero.titleHighlight, TITLE_SIZE, BRAND)])
    : [];
  const align = rtl ? "flex-end" : "flex-start";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          alignItems: align,
          padding: "72px 80px",
          backgroundColor: "#060a07",
          backgroundImage:
            "radial-gradient(ellipse 900px 520px at 50% 120%, rgba(4,164,23,0.55), rgba(4,164,23,0) 70%)",
          color: WHITE,
          fontFamily: "Plex Arabic",
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- Satori markup, not a page */}
        <img src={logoSrc} width={LOGO_SIZE} height={LOGO_SIZE} alt="" />

        <div style={{ display: "flex", flexDirection: "column", alignItems: align }}>
          {rtl ? (
            arabicTitle.map((line) => (
              // eslint-disable-next-line @next/next/no-img-element -- Satori markup, not a page
              <img key={line.src} src={line.src} width={line.width} height={line.height} alt="" />
            ))
          ) : (
            // An array, not a fragment: Satori lays a fragment's children out as one row.
            [
              { text: hero.titleLead, color: WHITE },
              { text: hero.titleHighlight, color: BRAND },
            ].map((line) => (
              <span key={line.text} style={{ fontSize: TITLE_SIZE, fontWeight: 700, lineHeight: 1.15, color: line.color }}>
                {line.text}
              </span>
            ))
          )}
        </div>

        <span style={{ fontSize: 26, fontWeight: 500, color: "rgba(255,255,255,0.65)" }}>
          {new URL(SITE_URL).host}
        </span>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: "Plex Arabic", data: bold, weight: 700, style: "normal" },
        { name: "Plex Arabic", data: medium, weight: 500, style: "normal" },
      ],
    },
  );
}
