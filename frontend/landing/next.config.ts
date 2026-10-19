import type { NextConfig } from "next";

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
    return [{ source: '/api/v1/:path*', destination: `${target.origin}/api/v1/:path*/` }];
  },
  // Pin the app root so Turbopack resolves this merged app against its own lockfile.
  turbopack: {
    root: __dirname,
  },
  // harfbuzzjs loads its .wasm from its own folder; keep it out of the bundle.
  serverExternalPackages: ["harfbuzzjs"],
  // Off by default; pinned so nobody ships source to the browser by accident.
  productionBrowserSourceMaps: false,
  // Drop the "X-Powered-By: Next.js" response header.
  poweredByHeader: false,
  experimental: {
    // global-not-found.tsx handles unmatched URLs across both route groups.
    globalNotFound: true,
  },
};

export default nextConfig;
