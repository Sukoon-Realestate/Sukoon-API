# Sprint 2 continuation — 17 November 2026

Local source verification; no deployment, hosted mutations, or backend rerun.

| Check | Result | Evidence |
|---|---|---|
| Standalone admin regression suite | 88 passed | [log](admin-tests.log) |
| Merged app regression suite | 38 passed | [log](merged-tests.log) |
| Standalone full ESLint | 0 errors, 6 image-element warnings; exit 0 | [details](lint.json) |
| Standalone TypeScript | `npx tsc --noEmit --incremental false`, exit 0 | Source hashes in [sources.json](sources.json) |
| Edited merged configuration/tests ESLint | exit 0 | `npx eslint next.config.ts tests/admin-navigation.test.mjs tests/public-site-contract.test.mjs tests/source-loader.mjs`, from landing |
| Both webpack production builds | passed | [admin](admin-build.log), [merged](merged-build.log) |
| Standalone dev browser | 6 passed | [results](standalone-browser/results.json) |
| Merged production browser | 6 passed | [results](merged-production-browser/results.json) |

The browser script executes the actual app in headless Chrome with synthetic intercepted API responses. It checks audit 503/retry, empty state, pagination, Arabic CSV bytes and formula escaping, hidden old-query rows, a delayed prior response, support role navigation and one-command receipt recovery, property version conflict/recovery, catalog 409/refresh/success, read-only permissions copy, and Chrome blocking even same-origin admin framing. CSVs and screenshots alongside each result are synthetic. No credentials or customer data are captured. These checks establish client behavior; they do not establish actual backend authorization, real concurrent database writes, production MFA, provider outcomes, or deployed headers.

The broader merged suite initially had stale test contracts: direct Node imports could not resolve the extensionless TypeScript bridge; navigation expectations omitted five existing routes and used the old accounts group identifier; the footer harness omitted its required locale and expected pre-publication disabled policies/mail contact. [Before log](merged-tests-before.log). The shared source loader executes the real TypeScript bridge and helpers. The corrected footer assertions require localized privacy, terms, deletion and support destinations, reject invalid external overrides, and retain HTTPS override checks. Product assertions were not removed to accommodate failures.

The framing probe initially injected synthetic localStorage setup into Chrome's blocked opaque subframe, causing a harness exception. Session setup now runs only in top-level documents; application exception checks remain enabled.

## Repeat

From `frontend`, run `node --test tests/*.test.cjs`, `npm run lint`, `npx tsc --noEmit --incremental false`, and `node --test landing/tests/*.test.mjs`. Build with `node node_modules/next/dist/bin/next build --webpack`; from landing use `npm run build -- --webpack`.

Run the app on loopback, then `node scripts/qa-admin-browser.cjs` with `SUKOON_PLAYWRIGHT_MODULE` pointing at an existing `playwright/test` module if it is outside normal Node resolution. Optional `SUKOON_QA_ORIGIN` (default http://127.0.0.1:3022) and `SUKOON_QA_OUTPUT` (default /private/tmp/sprint2-browser) select app/output. This run used an already installed Playwright package; no dependency or lockfile changed.

Remaining acceptance: actual staff sessions against a disposable live backend under competing revisions/faults, and hosted verification after deployment. Sprint 1 mobile/signing/store blockers remain separately open. Six advisory native-image warnings remain; the lint gate passes. The full-document login redirect has one local lint exemption because rejecting a credential must discard private client state; application import/type rules remain enabled.
