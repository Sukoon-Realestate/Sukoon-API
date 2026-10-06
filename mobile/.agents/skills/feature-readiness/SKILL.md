---
name: feature-readiness
description: Assess whether a Flutter/Dart feature is ready for production by checking requirements, real in-app access, runtime data, integrations, lifecycle risks, and verification evidence. Use for an explicit production-readiness review or a scoped fix-and-verify request for a named feature or directory; do not use as a substitute for an ordinary code review or to promise defect-free software.
---

# Feature Readiness

Assess the requested feature against evidence from the repository, available contracts, and executed verification. Adapt to the project's architecture and conventions. A successful build or passing unit tests alone never establishes production readiness, and no outcome guarantees that the feature is free of defects.

## Interpret the Request

Extract:

- Feature name or directory.
- Mode: `Review` or `Fix & Verify`. Default to `Review` when omitted.
- Optional target platform and flavor.

Treat `review` as `Review` and `fix` as `Fix & Verify`. Treat invocations such as `$feature-readiness review create-order` or `$feature-readiness fix lib/src/features/checkout` as natural-language requests, not CLI syntax. If scope is clear from context, proceed without asking. Inspect only platforms and flavors shown to exist in the project. Write the final report in Arabic unless the user requests another language.

## Establish the Scope

Before assessing readiness:

1. Read applicable `AGENTS.md` files and project documentation.
2. Learn the existing architecture, state management, routing, dependency injection, API/data conventions, test setup, and release configuration relevant to the feature. Follow local patterns; do not prescribe a generic Flutter architecture.
3. Locate the feature files, direct dependencies, shared components, contracts, and call sites.
4. Establish requirements from the user's description and available documentation or contracts. Separate them into confirmed requirements, reasonable inferences, and unresolved questions.
5. Trace the user journey from a real entry point to its final outcome, including roles, permissions, feature flags, deep links, platforms, and flavors where applicable.

Do not invent requirements. Do not turn every possible improvement into a release blocker.

## Apply the Review

Read [references/readiness-checklist.md](references/readiness-checklist.md) and apply only sections relevant to the feature's responsibilities and risks. Mark irrelevant sections `Not applicable`; mark unavailable evidence `Not verified` with the reason and what is needed.

For every finding, record:

- Description.
- Evidence: file location, execution path, contract, or test result.
- User or data impact.
- Priority: `Release blocker`, `Important issue`, or `Optional improvement`.
- Evidence status: `Confirmed` or `Requires verification`.
- Proposed fix.
- Responsible team or required dependency.
- How to verify the fix.

Do not present an assumption as a confirmed defect. Do not make style differences blockers without practical release impact.

## Respect the Mode

### Review

- Inspect implementation and run relevant existing checks and tests.
- Do not edit application code, tests, or configuration, and do not apply formatting that rewrites files.
- Identify missing tests and required fixes, then produce the readiness report.

### Fix & Verify

- Complete the inspection before editing.
- Fix feature-related issues inside the requested scope, preserve existing correct behavior and project architecture, and avoid broad refactors.
- Add focused tests needed for business rules, boundaries, failures, state transitions, UI behavior, or the complete journey according to actual risk.
- Execute relevant verification and reassess readiness.
- Distinguish resolved findings from remaining gaps and pre-existing failures from failures introduced by the changes.
- Never fabricate a backend contract, endpoint, field, or business value to make the feature appear complete.

## Decide the Outcome

Use exactly one outcome:

- `Ready within verified scope`: Core confirmed requirements are satisfied, with no release blockers or critical verification gaps in the assessed scope.
- `Not ready`: At least one confirmed issue prevents release, even when some other checks remain incomplete.
- `Verification incomplete`: No confirmed release blocker has been established, but evidence is insufficient to establish readiness. Name the critical checks that remain.

A suspected blocker that still requires verification can justify `Verification incomplete`, not `Not ready`, until confirmed. Do not use a readiness percentage.

Read [references/report-template.md](references/report-template.md) before reporting. Include exact commands and results, distinguish mocked verification from real-service verification, and add a manual test sheet when a device, account, permission, or external service is required.

## Safety and Boundaries

- A route definition or feature file does not prove that users can reach it. Conversely, a missing textual reference alone does not prove code is unused; trace generated routes, dynamic registration, callbacks, and configuration.
- Do not treat hidden UI as proof of server-side authorization.
- Do not silently reinterpret failures as success or fabricated empty data.
- Do not execute real payments, mutate production data, or use live destructive operations during automated verification without explicit authorization.
- Keep the work feature-scoped. Mention related risks without expanding into a project-wide audit.

For maintaining or revalidating this skill, use [references/validation-scenarios.md](references/validation-scenarios.md); it is not required during an ordinary feature assessment.
