import type { NextConfig } from "next";
import { BASE_PATH } from "./src/lib/basePath";

const nextConfig: NextConfig = {
  // ! Served at /admin through the landing app's rewrites (multi-zones).
  // ! Link/router/redirect add this automatically; raw URLs must use BASE_PATH.
  basePath: BASE_PATH,
  // Off by default; pinned so nobody ships source to the browser by accident.
  productionBrowserSourceMaps: false,
  // Drop the "X-Powered-By: Next.js" response header.
  poweredByHeader: false,
};

export default nextConfig;
