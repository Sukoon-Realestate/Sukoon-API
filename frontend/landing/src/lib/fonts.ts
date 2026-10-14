import { IBM_Plex_Sans_Arabic, Lexend, Readex_Pro } from "next/font/google";

// Shared by the locale layout and global-not-found, which renders outside it.
export const plexArabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-arabic",
  display: "swap",
});

export const lexend = Lexend({
  subsets: ["latin"],
  variable: "--font-latin",
  display: "swap",
});

// Display face for headings; a Lexend sibling that covers Arabic and Latin.
export const readex = Readex_Pro({
  subsets: ["arabic", "latin"],
  variable: "--font-readex",
  display: "swap",
});
