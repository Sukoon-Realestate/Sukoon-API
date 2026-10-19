import { NextResponse, type NextRequest } from "next/server";
import { defaultLocale, hasLocale, type Locale } from "@/i18n/config";

function preferredLocale(request: NextRequest): Locale {
  const header = request.headers.get("accept-language") ?? "";
  const first = header.split(",")[0]?.trim().slice(0, 2).toLowerCase() ?? "";
  return hasLocale(first) ? first : defaultLocale;
}

// Sends locale-less paths (e.g. "/") to "/ar" or "/en" based on the browser language.
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  // Admin routes are not localized; the (admin) route group serves them directly.
  if (pathname === "/admin" || pathname.startsWith("/admin/")) return;
  // Preserve API methods and bodies; API paths must never enter locale routing.
  if (pathname === "/api" || pathname.startsWith("/api/")) return;

  const segment = pathname.split("/")[1] ?? "";
  if (hasLocale(segment)) return;

  request.nextUrl.pathname = `/${preferredLocale(request)}${pathname === "/" ? "" : pathname}`;
  return NextResponse.redirect(request.nextUrl);
}

export const config = {
  // Skip Next internals and any file with an extension (favicon, images, ...).
  matcher: ["/((?!_next|.*\\..*).*)"],
};
