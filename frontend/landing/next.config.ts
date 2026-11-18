import type { NextConfig } from "next";
import { resolve } from "node:path";

const nextConfig: NextConfig = {
  // Django API routes retain their canonical trailing slash across the proxy.
  skipTrailingSlashRedirect: true,
  async headers() {
    return [{
      source: '/admin/:path*',
      headers: [
        { key: 'Content-Security-Policy', value: "frame-ancestors 'none'" },
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      ],
    }];
  },
  async rewrites() {
    const backend = process.env.SOKOUN_API_PROXY_URL?.replace(/\/$/, "");
    if (!backend) return [];
    const target = new URL(backend);
    if (!['http:', 'https:'].includes(target.protocol) || target.username || target.password || target.search || target.hash || target.pathname !== '/') {
      throw new Error('SOKOUN_API_PROXY_URL must be an HTTP(S) origin without credentials, path, query or fragment.');
    }
    return [
      { source: '/api/v1/:path*', destination: `${target.origin}/api/v1/:path*/` },
      // Verification happens on the mobile link host, not only the API host.
      { source: '/.well-known/assetlinks.json', destination: `${target.origin}/.well-known/assetlinks.json` },
      { source: '/.well-known/apple-app-site-association', destination: `${target.origin}/.well-known/apple-app-site-association` },
    ];
  },
  // Pin the app root so Turbopack resolves this merged app against its own lockfile.
  turbopack: {
    root: resolve(__dirname, ".."),
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
