import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // These Node test harnesses intentionally execute TypeScript in CommonJS.
    // Keep the browser/application import rules unchanged.
    files: ["tests/**/*.cjs", "scripts/test-*.cjs", "scripts/qa-*.cjs"],
    rules: { "@typescript-eslint/no-require-imports": "off" },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Separate Next.js app with its own lint config.
    "landing/**",
  ]),
]);

export default eslintConfig;
