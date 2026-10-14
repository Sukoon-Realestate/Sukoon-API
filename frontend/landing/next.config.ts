import type { NextConfig } from "next";

// Where the admin dashboard zone runs. It serves everything under /admin (its basePath).
const ADMIN_URL = process.env.ADMIN_URL ?? "http://localhost:3001";

const nextConfig: NextConfig = {
  // ! This app lives inside the admin app's folder; pin the root so Turbopack
  // ! doesn't resolve against the parent lockfile.
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
    // app/global-not-found.tsx: our root layout lives under [lang], so a plain
    // not-found.tsx can't cover unmatched URLs.
    globalNotFound: true,
  },
  // Multi-zones: this app owns "/", the admin app owns "/admin/*".
  async rewrites() {
    return [
      { source: "/admin", destination: `${ADMIN_URL}/admin` },
      { source: "/admin/:path+", destination: `${ADMIN_URL}/admin/:path+` },
    ];
  },
};

export default nextConfig;
