# Production Readiness Checklist

Use this checklist selectively. Record `Not applicable` with a short reason rather than forcing a check onto a feature that does not have that responsibility.

## 1. Requirements and Journey

- List confirmed requirements and cite their source.
- Label interpretations that are not stated by a requirement as inferences.
- List unresolved questions only when their answers could affect readiness.
- Identify the entry point, intermediate states, and final user-visible or data outcome.
- Identify which users, roles, permissions, flags, platforms, and flavors can enter the journey.
- Trace actual calls and navigation. A registered route is not sufficient evidence of accessibility.
- Investigate dynamic routes, generated registries, callbacks, deep links, and configuration before declaring code unused.
- Distinguish intentionally disabled or future functionality from broken navigation or disconnected code.

## 2. Real Data and Placeholder Data

Search runtime paths for dummy lists, sample identities, mock responses, forced success, temporary hardcoded values, and fallbacks that replace an API failure with fabricated content.

For every candidate:

1. Determine whether it executes in production behavior or is confined to tests, fixtures, previews, examples, or debug-only code.
2. Distinguish legitimate constants—such as enum mappings, validation limits, or static product copy—from business or user data that should come from a real source.
3. Record its location, triggering path, user visibility, and impact.
4. Look for the replacement source in existing clients, repositories, models, contracts, OpenAPI documents, Postman collections, and project documentation.
5. Classify that source as one of:
   - `Available and ready to integrate`.
   - `Available but requires changes`.
   - `Missing`.
   - `Not verified`.

Never infer an endpoint, response field, or business value. If a source is missing, state exactly what the backend team or requirements owner must provide. Test-only mocks are not runtime placeholder defects unless production code imports or executes them.

## 3. Feature Completeness

- Compare the implemented journey with confirmed requirements, not with speculative enhancements.
- Inspect actionable controls, callbacks, menu items, navigation, submission, cancellation, retry, and final confirmation.
- Investigate empty callbacks, `UnimplementedError`, temporary exceptions, commented-out workflow steps, and meaningful TODO/FIXME markers.
- Do not report a TODO merely because it exists; prove its effect on the requested journey.
- Review input validation, calculations, business rules, boundary values, state transitions, idempotency, and duplicate submission risks.
- Check whether success is reported only after the intended operation succeeds.

## 4. Backend and Data Integration

- Compare endpoints, methods, path/query/body parameters, headers, authentication, and content types with available contracts.
- Check request/response models, serialization, nullability, enum evolution, date/time handling, numeric precision, pagination, and backward compatibility where relevant.
- Check timeouts, offline behavior, connectivity changes, expired sessions, cancellation, malformed responses, and server errors.
- Ensure errors are represented accurately rather than becoming false success, fabricated data, or a misleading empty state.
- Identify cache behavior and staleness expectations when the project uses caching.
- If no trustworthy contract or service environment is available, mark the affected comparison `Not verified`; do not guess.

## 5. Actual Application Usage

- Follow call sites and navigation from a real user-accessible surface.
- Verify dependency registration and feature-specific providers, blocs, cubits, controllers, services, or repositories are constructed in the actual journey.
- Check authorization, role gates, feature flags, remote configuration, flavor gates, deep-link registration, and platform-specific setup that demonstrably exist.
- Explain who can access the feature, from where, and under which conditions.
- Confirm the final outcome is reachable, not just the initial screen.
- Treat a missing required entry point as a blocker only when accessibility is a confirmed requirement.

## 6. User Experience and Lifecycle

- Check loading, success, valid empty, error, retry, and offline states as applicable.
- Check repeated taps, overlapping requests, duplicate submissions, and responses arriving out of order.
- Check refresh, returning to the screen, background/foreground transitions, and leaving during asynchronous work.
- Inspect disposal or cancellation of controllers, focus nodes, animation controllers, streams, subscriptions, timers, and in-flight work where relevant.
- Review keyboard behavior, focus, safe areas, text scaling, semantics, contrast, permissions, and accessibility based on the UI and target platform.
- Review localization, Arabic text, RTL layout, pluralization, date/number/currency formatting, and untranslated fallback text when the project supports them.
- Do not invent localization or accessibility requirements that the project or requested platforms do not support; still report clear user-impacting defects.

## 7. Security and Release Configuration

- Inspect feature-related code and configuration for secrets, test tokens, personal data, sensitive logs, nonproduction endpoints, and debug-only bypasses in release behavior.
- Check user-data isolation, local storage, screenshots/clipboard/logging where sensitive data is involved, and permission handling where applicable.
- Verify client-side visibility is not relied upon as the only authorization control; mark server authorization `Not verified` unless evidence confirms it.
- Inspect only platform and flavor configurations that exist in the repository or are explicitly in scope.
- Check signing/environment selection only when it materially affects the feature and can be assessed without exposing secrets.

## 8. Performance and Regression Risk

- Inspect repeated or duplicate requests, rebuild-triggered work, unbounded lists, large synchronous parsing, oversized assets, unnecessary loading, and resource leaks.
- Label an observed or measured problem as confirmed; label a plausible performance concern requiring profiling as a hypothesis and specify the measurement needed.
- Review changes to shared code, schemas, caches, persisted data, localization, navigation, and public APIs for effects on existing users.
- In `Fix & Verify`, add regression coverage when a concrete adjacent behavior is at risk.
- Do not expand a feature assessment into a general performance audit or broad refactor.

## 9. Verification

Use existing project tools and tests before adding anything.

### Review mode

- Run relevant existing unit, widget, integration, analysis, and build checks when available and useful.
- Do not add or modify tests. Identify missing coverage in the report.
- Use non-rewriting format checks if formatting is relevant.

### Fix & Verify mode

- Add focused unit tests for important rules, boundaries, error handling, and state transitions.
- Add widget tests when UI state or interaction needs verification.
- Add an integration or smoke test when only the complete journey can establish the behavior and the project supports it.
- Derive expected results from requirements and contracts rather than duplicating implementation logic.
- Do not impose arbitrary coverage percentages or add superficial assertions.

### In both modes

- Record each exact command, scope, result, and meaningful failure.
- Separate pre-existing failures from failures caused by the scoped changes when evidence allows.
- Distinguish mocked tests from verification against a real service.
- A build or passing tests is supporting evidence, not a readiness verdict.
- If a check cannot run, record `Not verified`, why it could not run, its readiness impact, and what is required to complete it.
- Prepare manual scenarios for checks requiring a device, account, role, permission, hardware, or external service.
- Never perform real payments or production-data mutations without explicit authorization.

## 10. Evidence Quality and Outcome

For each finding, include all fields required by `SKILL.md`. Prefer direct evidence such as a concrete execution path, contract comparison, or test output. File-name patterns and search hits are leads, not conclusions.

Choose the outcome in this order:

1. Any confirmed release blocker: `Not ready`.
2. Otherwise, any critical missing verification: `Verification incomplete`.
3. Otherwise, core confirmed requirements satisfied with no blocker in scope: `Ready within verified scope`.

Important issues and optional improvements may coexist with `Ready within verified scope` only when their practical impact does not block release and the reasoning is explicit.
