import type { NextConfig } from "next";
import { BASE_PATH } from "./src/lib/basePath";

const nextConfig: NextConfig = {
  // Django API routes retain their canonical trailing slash across the proxy.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    const backend = process.env.SOKOUN_API_PROXY_URL?.replace(/\/$/, "");
    if (!backend) return [];
    const target = new URL(backend);
    if (!['http:', 'https:'].includes(target.protocol) || target.username || target.password || target.search || target.hash || target.pathname !== '/') {
      throw new Error('SOKOUN_API_PROXY_URL must be an HTTP(S) origin without credentials, path, query or fragment.');
    }
    return [{ source: '/api/v1/:path*', destination: `${target.origin}/api/v1/:path*/`, basePath: false }];
  },
  // ! Served at /admin through the landing app's rewrites (multi-zones).
  // ! Link/router/redirect add this automatically; raw URLs must use BASE_PATH.
  basePath: BASE_PATH,
  // Off by default; pinned so nobody ships source to the browser by accident.
  productionBrowserSourceMaps: false,
  // Drop the "X-Powered-By: Next.js" response header.
  poweredByHeader: false,
};

export default nextConfig;
