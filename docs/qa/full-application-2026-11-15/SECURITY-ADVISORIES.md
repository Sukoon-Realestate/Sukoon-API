# Dependency advisory ledger

Registry scanner results on 2026-11-15. Affected version detection does not prove exploitability. Confirm deployed versions, reachable features and advisory prerequisites before assigning application risk. No exploit payloads were sent to the hosted app.

## 17 November npm follow-up

Both JavaScript trees now audit with **zero known vulnerabilities of every severity**. Fresh pre-change audits reproduced seven moderate findings each. A compatible TypeScript ESLint 8.73.0 update declares patched minimatch `^11.0.1`; the lockfiles resolve 11.0.9 without a forced major override. Application manifests and Next.js 16.4.6 remain unchanged. Sixty-two admin tests, three merged build-configuration tests, both webpack builds and scoped lint pass. Full admin lint has no newly introduced findings; its existing baseline remains later-sprint work. [Exact lock deltas](evidence/sprint-1-2026-11-17/followup/toolchain-delta.json), [admin audit](evidence/sprint-1-2026-11-17/followup/admin-audit-after.json), [merged audit](evidence/sprint-1-2026-11-17/followup/landing-audit-after.json). Deployed versions have not changed or been certified.

The 16 November paragraph below is the historical intermediate result, superseded by this follow-up.

## 16 November local remediation

Both manifests and lockfiles now use Next.js and eslint-config-next 16.4.6. Compatible transitive patches also update sharp, source-map-js and zod. Fresh full-tree audits report **0 critical, 0 high, 7 moderate** per tree. Remaining findings are minimatch 10.2.6 and the six dependent TypeScript ESLint packages in the development toolchain. They remain tracked; no unsafe forced minimatch major override was applied. Both production webpack builds and the admin/merged regression suites passed. Default Turbopack verification hit a local worker port-binding restriction. See [Sprint 1](SPRINT-1.md) and [retained audit deltas](evidence/sprint-1-2026-11-16/).

## 17 November Python remediation

A fresh pinned-package audit reproduced **124 advisory entries across 13 packages** before changes. The locally resolved lockfile now reports **zero known advisories**. The shared Python environment and deployment were not upgraded. This is advisory remediation, not proof against unknown vulnerabilities or production release acceptance.

Python remains 3.11. Runtime pins now include Django 5.2.17, DRF 3.18.2, Djoser 2.3.5, social-auth-app-django 7.1.0, social-auth-core 6.2.0, OAuthlib 4.0.1, certifi 2026.10.23, pyasn1 0.6.5, pypdf 6.21.4, python-dotenv 1.2.2 and setuptools 84.1.0. Tooling uses black 26.10.1 and pytest 9.0.3 with pytest-asyncio 1.3.0. The resolver retained unrelated direct pins; [dependency deltas](evidence/sprint-1-2026-11-17/dependency-delta.json) enumerate necessary transitive changes.

The patched DRF requires Django 5.2; patched social-auth core requires an adapter major supported by Djoser 2.3.5. Metadata was checked directly from PyPI, including [DRF](https://pypi.org/project/djangorestframework/3.18.2/), [Djoser](https://pypi.org/project/djoser/2.3.5/) and [the adapter](https://pypi.org/project/social-auth-app-django/7.1.0/). A disposable lockfile installation passes `pip check`. Compatibility work preserves WhiteNoise storage and inherited OAuth errors; see [Sprint 1](SPRINT-1.md) for regression outcomes and limitations. The adapter adds upstream migrations 0017–0020; synthetic existing Google/Apple/Facebook association IDs, users, UIDs and JSON survived a 0016→0020 upgrade, with expected `id_key` backfills. Actual release data must still be checked for invalid/empty UIDs before applying the new constraint.

[Before audit](evidence/sprint-1-2026-11-17/audit-before.json), [after audit](evidence/sprint-1-2026-11-17/audit-after.json), [synthetic migration drill](evidence/sprint-1-2026-11-17/social-upgrade.log).

The following tables preserve the original vulnerable-version ledger.

## frontend-audit.json

| Package | Severity | Advisory | Affected versions |
|---|---|---|---|
| minimatch | moderate | [minimatch has potential denial of service via globparts amplification](https://github.com/advisories/GHSA-g3hv-75wg-m249) | `>=7.0.0 <11.0.1` |
| next | critical | [Next.js: Remote Code Execution in next/og ImageResponse](https://github.com/advisories/GHSA-vcvr-r3jv-pc5j) | `>=16.2.0 <16.3.6` |
| next | moderate | [Next.js: Pending `use cache` fill can leak Draft Mode content into regular responses and persisted pages](https://github.com/advisories/GHSA-3w37-wq28-93x7) | `>=16.3.0 <16.3.8` |
| next | moderate | [Next.js has cache poisoning of SSG and ISR pages in self-hosted applications](https://github.com/advisories/GHSA-4jqv-mc3x-m676) | `>=16.0.0 <16.3.8` |
| next | low | [Next.js has information disclosure in development server's Model Context Protocol endpoint](https://github.com/advisories/GHSA-39w2-rjm5-chcv) | `>=16.0.0 <16.3.8` |
| next | moderate | [Next.js has information disclosure in App Router metadata image routes via dynamicParams bypass](https://github.com/advisories/GHSA-f87g-xv8r-7p7x) | `>=16.0.0 <16.3.8` |
| next | moderate | [Next.js has cache poisoning in SSG/ISR rendering that leads to cross-user content substitution and persistent denial of service](https://github.com/advisories/GHSA-mcj8-r9mp-w47p) | `>=16.0.0 <16.3.8` |
| next | high | [Next.js has Server-Side Request Forgery in Image Optimization](https://github.com/advisories/GHSA-cjq9-62q9-8jv4) | `>=16.0.0 <16.3.8` |
| next | critical | [Next.js: Unauthenticated Remote Code Execution in Image Optimization API when SVG files are used](https://github.com/advisories/GHSA-2464-fhr4-w9xw) | `>=16.0.0 <=16.4.0` |
| next | high | [Next.js: Denial of Service in App Router using Server Actions](https://github.com/advisories/GHSA-p3m5-59mp-jv5r) | `>=16.0.0 <=16.4.0` |
| next | moderate | [next.js cache leak across root param values in nested 'use cache' functions](https://github.com/advisories/GHSA-h694-7cp9-m8p3) | `>=16.3.0 <16.3.8` |
| next | critical | [Next.js: Unauthenticated Remote Code Execution in `use cache` functions returning typed arrays](https://github.com/advisories/GHSA-673q-mjm6-r5xr) | `>=16.0.0 <=16.4.0` |
| sharp | high | [sharp : Vulnerability in librsvg dependency CVE-2026-96889](https://github.com/advisories/GHSA-wq5f-xc86-pv6w) | `<0.35.5` |
| source-map-js | high | [source-map-js allows event-loop denial of service through indexed source-map section offsets](https://github.com/advisories/GHSA-68fv-2mgg-jv7q) | `>=1.0.0 <1.2.2` |
| zod | high | [Zod can exhaust memory while validating oversized constrained collections](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5) | `<4.6.6` |

## landing-audit.json

| Package | Severity | Advisory | Affected versions |
|---|---|---|---|
| minimatch | moderate | [minimatch has potential denial of service via globparts amplification](https://github.com/advisories/GHSA-g3hv-75wg-m249) | `>=7.0.0 <11.0.1` |
| next | critical | [Next.js: Unauthenticated Remote Code Execution in Image Optimization API when SVG files are used](https://github.com/advisories/GHSA-2464-fhr4-w9xw) | `>=16.0.0 <=16.4.0` |
| next | high | [Next.js: Denial of Service in App Router using Server Actions](https://github.com/advisories/GHSA-p3m5-59mp-jv5r) | `>=16.0.0 <=16.4.0` |
| next | critical | [Next.js: Unauthenticated Remote Code Execution in `use cache` functions returning typed arrays](https://github.com/advisories/GHSA-673q-mjm6-r5xr) | `>=16.0.0 <=16.4.0` |

## Backend lockfile

Runtime and developer tools share this lockfile. `black` and `pytest` entries are tooling findings. The scanner used pinned versions without resolving/installing application dependencies.

| Package | Locked version | Advisory | Fixed versions |
|---|---|---|---|
| black | 24.3.0 | [PYSEC-2026-2121](https://osv.dev/vulnerability/PYSEC-2026-2121) | 26.3.1 |
| black | 24.3.0 | [PYSEC-2026-2121](https://osv.dev/vulnerability/PYSEC-2026-2121) | 26.3.1 |
| black | 24.3.0 | [PYSEC-2026-2120](https://osv.dev/vulnerability/PYSEC-2026-2120) | 26.3.0 |
| black | 24.3.0 | [CVE-2026-114134](https://osv.dev/vulnerability/CVE-2026-114134) | 26.10.1 |
| certifi | 2026.7.22 | [PYSEC-2026-4320](https://osv.dev/vulnerability/PYSEC-2026-4320) | 2026.10.18 |
| certifi | 2026.7.22 | [PYSEC-2026-4320](https://osv.dev/vulnerability/PYSEC-2026-4320) | 2026.10.18 |
| django | 4.2.11 | [PYSEC-2024-58](https://osv.dev/vulnerability/PYSEC-2024-58) | 4.2.14, 5.0.7 |
| django | 4.2.11 | [PYSEC-2024-57](https://osv.dev/vulnerability/PYSEC-2024-57) | 4.2.14, 5.0.7 |
| django | 4.2.11 | [PYSEC-2024-56](https://osv.dev/vulnerability/PYSEC-2024-56) | 4.2.14, 5.0.7 |
| django | 4.2.11 | [PYSEC-2024-59](https://osv.dev/vulnerability/PYSEC-2024-59) | 4.2.14, 5.0.7 |
| django | 4.2.11 | [PYSEC-2024-69](https://osv.dev/vulnerability/PYSEC-2024-69) | 4.2.15, 5.0.8 |
| django | 4.2.11 | [PYSEC-2024-70](https://osv.dev/vulnerability/PYSEC-2024-70) | 4.2.15, 5.0.8 |
| django | 4.2.11 | [PYSEC-2024-68](https://osv.dev/vulnerability/PYSEC-2024-68) | 4.2.15, 5.0.8 |
| django | 4.2.11 | [PYSEC-2024-67](https://osv.dev/vulnerability/PYSEC-2024-67) | 4.2.15, 5.0.8 |
| django | 4.2.11 | [PYSEC-2024-102](https://osv.dev/vulnerability/PYSEC-2024-102) | 4.2.16, 5.0.9, 5.1.1 |
| django | 4.2.11 | [PYSEC-2026-1297](https://osv.dev/vulnerability/PYSEC-2026-1297) | 4.2.16, 5.0.9, 5.1.1 |
| django | 4.2.11 | [PYSEC-2024-102](https://osv.dev/vulnerability/PYSEC-2024-102) | 4.2.16, 5.0.9, 5.1.1 |
| django | 4.2.11 | [PYSEC-2025-37](https://osv.dev/vulnerability/PYSEC-2025-37) | 4.2.21, 5.1.9, 5.2.1 |
| django | 4.2.11 | [PYSEC-2025-37](https://osv.dev/vulnerability/PYSEC-2025-37) | 4.2.21, 5.1.9, 5.2.1 |
| django | 4.2.11 | [PYSEC-2024-156](https://osv.dev/vulnerability/PYSEC-2024-156) | 4.2.17, 4.2.17, 5.0.10, 5.0.10, 5.1.4, 5.1.4 |
| django | 4.2.11 | [PYSEC-2024-157](https://osv.dev/vulnerability/PYSEC-2024-157) | 4.2.17, 4.2.17, 5.0.10, 5.0.10, 5.1.4, 5.1.4 |
| django | 4.2.11 | [PYSEC-2024-157](https://osv.dev/vulnerability/PYSEC-2024-157) | 4.2.17, 5.0.10, 5.1.4 |
| django | 4.2.11 | [PYSEC-2024-156](https://osv.dev/vulnerability/PYSEC-2024-156) | 4.2.17, 5.0.10, 5.1.4 |
| django | 4.2.11 | [PYSEC-2025-1](https://osv.dev/vulnerability/PYSEC-2025-1) | 4.2.18, 5.0.11, 5.1.5 |
| django | 4.2.11 | [PYSEC-2025-1](https://osv.dev/vulnerability/PYSEC-2025-1) | 4.2.18, 4.2.18, 5.0.11, 5.0.11, 5.1.5, 5.1.5 |
| django | 4.2.11 | [PYSEC-2025-13](https://osv.dev/vulnerability/PYSEC-2025-13) | 4.2.20, 5.0.13, 5.1.7 |
| django | 4.2.11 | [PYSEC-2025-13](https://osv.dev/vulnerability/PYSEC-2025-13) | 4.2.20, 5.0.13, 5.1.7 |
| django | 4.2.11 | [PYSEC-2025-47](https://osv.dev/vulnerability/PYSEC-2025-47) | 4.2.22, 5.1.10, 5.2.2 |
| django | 4.2.11 | [PYSEC-2025-47](https://osv.dev/vulnerability/PYSEC-2025-47) | 4.2.22, 5.1.10, 5.2.2 |
| django | 4.2.11 | [PYSEC-2025-105](https://osv.dev/vulnerability/PYSEC-2025-105) | 4.2.24, 5.1.12, 5.2.6 |
| django | 4.2.11 | [PYSEC-2025-106](https://osv.dev/vulnerability/PYSEC-2025-106) | 4.2.25, 5.1.13, 5.2.7 |
| django | 4.2.11 | [PYSEC-2026-1296](https://osv.dev/vulnerability/PYSEC-2026-1296) | 4.2.25, 5.1.13, 5.2.7 |
| django | 4.2.11 | [PYSEC-2024-56](https://osv.dev/vulnerability/PYSEC-2024-56) | 4.2.14, 5.0.7 |
| django | 4.2.11 | [PYSEC-2024-59](https://osv.dev/vulnerability/PYSEC-2024-59) | 4.2.14, 5.0.7 |
| django | 4.2.11 | [PYSEC-2024-57](https://osv.dev/vulnerability/PYSEC-2024-57) | 4.2.14, 5.0.7 |
| django | 4.2.11 | [PYSEC-2024-58](https://osv.dev/vulnerability/PYSEC-2024-58) | 4.2.14, 5.0.7 |
| django | 4.2.11 | [PYSEC-2024-69](https://osv.dev/vulnerability/PYSEC-2024-69) | 4.2.15, 5.0.8 |
| django | 4.2.11 | [PYSEC-2024-68](https://osv.dev/vulnerability/PYSEC-2024-68) | 4.2.15, 5.0.8 |
| django | 4.2.11 | [PYSEC-2024-70](https://osv.dev/vulnerability/PYSEC-2024-70) | 4.2.15, 5.0.8 |
| django | 4.2.11 | [PYSEC-2024-67](https://osv.dev/vulnerability/PYSEC-2024-67) | 4.2.15, 5.0.8 |
| django | 4.2.11 | [PYSEC-2025-107](https://osv.dev/vulnerability/PYSEC-2025-107) | 4.2.26, 5.1.14, 5.2.8 |
| django | 4.2.11 | [PYSEC-2025-108](https://osv.dev/vulnerability/PYSEC-2025-108) | 4.2.26, 5.1.14, 5.2.8 |
| django | 4.2.11 | [PYSEC-2025-104](https://osv.dev/vulnerability/PYSEC-2025-104) | 4.2.27, 5.1.15, 5.2.9 |
| django | 4.2.11 | [PYSEC-2025-109](https://osv.dev/vulnerability/PYSEC-2025-109) | 4.2.27, 5.1.15, 5.2.9 |
| django | 4.2.11 | [PYSEC-2026-42](https://osv.dev/vulnerability/PYSEC-2026-42) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2026-44](https://osv.dev/vulnerability/PYSEC-2026-44) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2026-47](https://osv.dev/vulnerability/PYSEC-2026-47) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2026-46](https://osv.dev/vulnerability/PYSEC-2026-46) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2026-45](https://osv.dev/vulnerability/PYSEC-2026-45) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2026-43](https://osv.dev/vulnerability/PYSEC-2026-43) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2026-2449](https://osv.dev/vulnerability/PYSEC-2026-2449) | 4.2.29, 5.2.12, 6.0.3 |
| django | 4.2.11 | [PYSEC-2026-2448](https://osv.dev/vulnerability/PYSEC-2026-2448) | 4.2.29, 5.2.12, 6.0.3 |
| django | 4.2.11 | [PYSEC-2026-48](https://osv.dev/vulnerability/PYSEC-2026-48) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-49](https://osv.dev/vulnerability/PYSEC-2026-49) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-53](https://osv.dev/vulnerability/PYSEC-2026-53) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-52](https://osv.dev/vulnerability/PYSEC-2026-52) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-51](https://osv.dev/vulnerability/PYSEC-2026-51) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-43](https://osv.dev/vulnerability/PYSEC-2026-43) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2026-42](https://osv.dev/vulnerability/PYSEC-2026-42) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2025-107](https://osv.dev/vulnerability/PYSEC-2025-107) | 4.2.26, 5.1.14, 5.2.8 |
| django | 4.2.11 | [PYSEC-2025-109](https://osv.dev/vulnerability/PYSEC-2025-109) | 4.2.27, 5.1.15, 5.2.9 |
| django | 4.2.11 | [PYSEC-2026-44](https://osv.dev/vulnerability/PYSEC-2026-44) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2025-106](https://osv.dev/vulnerability/PYSEC-2025-106) | 4.2.25, 5.1.13, 5.2.7 |
| django | 4.2.11 | [PYSEC-2025-108](https://osv.dev/vulnerability/PYSEC-2025-108) | 4.2.26, 5.1.14, 5.2.8 |
| django | 4.2.11 | [PYSEC-2026-46](https://osv.dev/vulnerability/PYSEC-2026-46) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2026-45](https://osv.dev/vulnerability/PYSEC-2026-45) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2025-104](https://osv.dev/vulnerability/PYSEC-2025-104) | 4.2.27, 5.1.15, 5.2.9 |
| django | 4.2.11 | [PYSEC-2026-53](https://osv.dev/vulnerability/PYSEC-2026-53) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-48](https://osv.dev/vulnerability/PYSEC-2026-48) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-49](https://osv.dev/vulnerability/PYSEC-2026-49) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-51](https://osv.dev/vulnerability/PYSEC-2026-51) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-52](https://osv.dev/vulnerability/PYSEC-2026-52) | 4.2.30, 5.2.13, 6.0.4 |
| django | 4.2.11 | [PYSEC-2026-47](https://osv.dev/vulnerability/PYSEC-2026-47) | 4.2.28, 5.2.11, 6.0.2 |
| django | 4.2.11 | [PYSEC-2025-105](https://osv.dev/vulnerability/PYSEC-2025-105) | 4.2.24, 5.1.12, 5.2.6 |
| django | 4.2.11 | [PYSEC-2026-1297](https://osv.dev/vulnerability/PYSEC-2026-1297) | 4.2.16, 5.0.9, 5.1.1 |
| django | 4.2.11 | [PYSEC-2026-1296](https://osv.dev/vulnerability/PYSEC-2026-1296) | 4.2.25, 5.1.13, 5.2.7 |
| django | 4.2.11 | [PYSEC-2026-2449](https://osv.dev/vulnerability/PYSEC-2026-2449) | 4.2.29, 5.2.12, 6.0.3 |
| django | 4.2.11 | [PYSEC-2026-2448](https://osv.dev/vulnerability/PYSEC-2026-2448) | 4.2.29, 5.2.12, 6.0.3 |
| django | 4.2.11 | [PYSEC-2026-3717](https://osv.dev/vulnerability/PYSEC-2026-3717) | 5.2.17, 6.0.8, 6.1.1 |
| django | 4.2.11 | [PYSEC-2026-198](https://osv.dev/vulnerability/PYSEC-2026-198) | 5.2.15, 6.0.6 |
| django | 4.2.11 | [PYSEC-2026-199](https://osv.dev/vulnerability/PYSEC-2026-199) | 5.2.15, 6.0.6 |
| django | 4.2.11 | [PYSEC-2026-201](https://osv.dev/vulnerability/PYSEC-2026-201) | 5.2.15, 6.0.6 |
| django | 4.2.11 | [PYSEC-2026-2090](https://osv.dev/vulnerability/PYSEC-2026-2090) | 5.2.16, 6.0.7 |
| django | 4.2.11 | [PYSEC-2026-2091](https://osv.dev/vulnerability/PYSEC-2026-2091) | 5.2.16, 6.0.7 |
| django | 4.2.11 | [PYSEC-2026-2092](https://osv.dev/vulnerability/PYSEC-2026-2092) | 5.2.16, 6.0.7 |
| django | 4.2.11 | [PYSEC-2026-3717](https://osv.dev/vulnerability/PYSEC-2026-3717) | 5.2.17, 6.0.8 |
| django | 4.2.11 | [PYSEC-2026-4035](https://osv.dev/vulnerability/PYSEC-2026-4035) | 5.2.17, 6.0.8 |
| djangorestframework | 3.15.0 | [PYSEC-2026-1304](https://osv.dev/vulnerability/PYSEC-2026-1304) | 3.15.2 |
| djangorestframework | 3.15.0 | [PYSEC-2026-1304](https://osv.dev/vulnerability/PYSEC-2026-1304) | 3.15.2 |
| djangorestframework | 3.15.0 | [PYSEC-2026-3827](https://osv.dev/vulnerability/PYSEC-2026-3827) | 3.17.2 |
| djangorestframework | 3.15.0 | [PYSEC-2026-3828](https://osv.dev/vulnerability/PYSEC-2026-3828) | 3.17.2 |
| djangorestframework | 3.15.0 | [CVE-2026-114138](https://osv.dev/vulnerability/CVE-2026-114138) | 3.18.2 |
| djangorestframework | 3.15.0 | [CVE-2026-114136](https://osv.dev/vulnerability/CVE-2026-114136) | 3.18.2 |
| djangorestframework | 3.15.0 | [CVE-2026-114137](https://osv.dev/vulnerability/CVE-2026-114137) | 3.18.2 |
| djoser | 2.2.2 | [PYSEC-2024-158](https://osv.dev/vulnerability/PYSEC-2024-158) | 2.3.0 |
| djoser | 2.2.2 | [PYSEC-2024-158](https://osv.dev/vulnerability/PYSEC-2024-158) | 2.3.0 |
| oauthlib | 4.0.0 | [CVE-2026-49272](https://osv.dev/vulnerability/CVE-2026-49272) | 4.0.1 |
| pyasn1 | 0.6.4 | [CVE-2026-119196](https://osv.dev/vulnerability/CVE-2026-119196) | 0.6.5 |
| pyasn1 | 0.6.4 | [CVE-2026-119194](https://osv.dev/vulnerability/CVE-2026-119194) | 0.6.5 |
| pyasn1 | 0.6.4 | [CVE-2026-119197](https://osv.dev/vulnerability/CVE-2026-119197) | 0.6.5 |
| pyasn1 | 0.6.4 | [CVE-2026-119195](https://osv.dev/vulnerability/CVE-2026-119195) | 0.6.5 |
| pypdf | 6.21.2 | [CVE-2026-119208](https://osv.dev/vulnerability/CVE-2026-119208) | 6.21.3 |
| pypdf | 6.21.2 | [CVE-2026-119206](https://osv.dev/vulnerability/CVE-2026-119206) | 6.21.3 |
| pypdf | 6.21.2 | [CVE-2026-119209](https://osv.dev/vulnerability/CVE-2026-119209) | 6.21.3 |
| pypdf | 6.21.2 | [CVE-2026-119207](https://osv.dev/vulnerability/CVE-2026-119207) | 6.21.3 |
| pypdf | 6.21.2 | [CVE-2026-119203](https://osv.dev/vulnerability/CVE-2026-119203) | 6.21.4 |
| pypdf | 6.21.2 | [CVE-2026-119205](https://osv.dev/vulnerability/CVE-2026-119205) | 6.21.4 |
| pypdf | 6.21.2 | [CVE-2026-119204](https://osv.dev/vulnerability/CVE-2026-119204) | 6.21.4 |
| pytest | 8.3.5 | [PYSEC-2026-1845](https://osv.dev/vulnerability/PYSEC-2026-1845) | 9.0.3 |
| pytest | 8.3.5 | [PYSEC-2026-1845](https://osv.dev/vulnerability/PYSEC-2026-1845) | 9.0.3 |
| python-dotenv | 1.0.1 | [PYSEC-2026-2270](https://osv.dev/vulnerability/PYSEC-2026-2270) | 1.2.2 |
| python-dotenv | 1.0.1 | [PYSEC-2026-2270](https://osv.dev/vulnerability/PYSEC-2026-2270) | 1.2.2 |
| setuptools | 81.0.0 | [PYSEC-2026-3447](https://osv.dev/vulnerability/PYSEC-2026-3447) | 83.0.0 |
| setuptools | 81.0.0 | [PYSEC-2026-3447](https://osv.dev/vulnerability/PYSEC-2026-3447) | 83.0.0 |
| setuptools | 81.0.0 | [GHSA-xmj3-9gf7-h52w](https://osv.dev/vulnerability/GHSA-xmj3-9gf7-h52w) | 84.1.0 |
| social-auth-app-django | 5.4.3 | [PYSEC-2026-1932](https://osv.dev/vulnerability/PYSEC-2026-1932) | 5.6.0 |
| social-auth-app-django | 5.4.3 | [PYSEC-2026-1932](https://osv.dev/vulnerability/PYSEC-2026-1932) | 5.6.0 |
| social-auth-core | 4.9.1 | [PYSEC-2026-4167](https://osv.dev/vulnerability/PYSEC-2026-4167) | 5.0.0 |
| social-auth-core | 4.9.1 | [PYSEC-2026-4169](https://osv.dev/vulnerability/PYSEC-2026-4169) | 5.0.0 |
| social-auth-core | 4.9.1 | [PYSEC-2026-4165](https://osv.dev/vulnerability/PYSEC-2026-4165) | 5.0.0 |
| social-auth-core | 4.9.1 | [PYSEC-2026-4166](https://osv.dev/vulnerability/PYSEC-2026-4166) | 5.0.0 |
| social-auth-core | 4.9.1 | [PYSEC-2026-4168](https://osv.dev/vulnerability/PYSEC-2026-4168) | 5.0.0 |
| social-auth-core | 4.9.1 | [CVE-2026-62322](https://osv.dev/vulnerability/CVE-2026-62322) | 5.0.2 |
| social-auth-core | 4.9.1 | [CVE-2026-115910](https://osv.dev/vulnerability/CVE-2026-115910) | 6.2.0 |
