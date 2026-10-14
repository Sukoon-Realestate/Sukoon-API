import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
