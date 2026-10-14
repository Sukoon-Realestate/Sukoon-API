import { IBM_Plex_Sans_Arabic, Lexend } from "next/font/google";

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
