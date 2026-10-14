import type { MetadataRoute } from "next";
import { absoluteUrl } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // The admin dashboard zone is private.
      disallow: "/admin",
    },
    sitemap: absoluteUrl("/sitemap.xml"),
  };
}
