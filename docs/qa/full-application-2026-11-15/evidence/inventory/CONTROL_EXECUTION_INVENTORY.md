# Control and execution inventory

This is a reproducible discovery and execution-reconciliation checkpoint. A callback binding is not necessarily a reachable button, a unique business action, an enabled feature, or a completed test. No passing result is inferred from filenames, test names, source maps, chapter coverage, or a callback's presence.

Inspection: 2026-11-15T14:28:40.529563+00:00. App commit `ba65fee1bb10f9fa9d8745b0e1207b7245873f52`; API commit `8a8cf7522ce38cb848dc09fe956e576e5125dd3c`. The source tree includes uncommitted work; per-site fingerprints are retained. Regeneration observes the working tree, not only committed source.

## Current counts

| Measure | Count |
| --- | ---: |
| Existing stable feature identities | 79 |
| Existing documented action families | 884 |
| Dart files discovered, including separately excluded generated files | 3490 |
| TypeScript/JavaScript source files parsed | 279 |
| Python application/configuration files parsed | 1378 |
| Dart/web/host callback and control candidates | 4583 |
| Backend URL/dispatch/operator/worker candidates | 1334 |
| URL handlers with a statically reconstructed config.urls path | 671 |
| URL handlers resolved to a local function/class definition | 757 |
| Pending review or explicitly observed case rows | 6449 |
| Case rows with individually attached observations | 0 |
| Parser diagnostics | 6 |

Counts of candidate sites and case rows are deliberately separate. An activation row does not enumerate all roles, inputs, server states, asynchronous outcomes, or failures. Full matrix expansion remains pending where those dimensions have not been assigned and executed.

## Reproduce and inspect

```sh
make -C apps/sokoun_app qaExecutionInventory
```

The command uses the installed Dart analyzer and adjacent admin application's installed TypeScript parser, plus Python's standard AST. It makes no requests, starts no application or worker, imports no Django models, installs no dependencies, and changes only the inventory artifacts. Configure `SOKOUN_API_ROOT` for a differently located API checkout.

- [Raw control candidates](control_candidates.jsonl): exact callback path/line, enclosing declaration, widget/component, labels, local condition/null branches, locally resolvable handler and call names.
- [Backend entry candidates](backend_entry_candidates.jsonl): URL includes/handlers, mounted static paths, handler imports, command branches, task and operator registrations.
- [Execution case ledger](control_execution_cases.jsonl): stable candidate/case identity, source fingerprint, current execution status and explicitly attributed observations.
- [Machine-readable summary and exclusions](control_inventory_summary.json).
- [All-family reconciliation](control_action_reconciliation.json): all existing action IDs, associated controls/server entries and unmapped boundaries.
- [Previous observed cycles](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/verification-2026-10-19/CONNECTED_CYCLES_CONTINUATION.md) remain valid only for their named checkpoints and environment. They are not automatically copied into every related control row.

## Execution status and evidence contract

`pending_reachability_and_case_review` means the control has been discovered, but its actual entry, actor and state still need reconciliation. `pending_dispatch_and_case_review` applies to server/worker/operator entries. Pending is unfinished work, not an external blocker. `blocked` requires an individually recorded missing dependency and evidence. `not_applicable` requires an explanation. A disabled control is a testable negative branch, not proof that its positive journey is complete.

To attribute execution, create or extend `control_execution_observations.json` in this directory. Each entry must identify `case_id`, current `source_fingerprint`, `evidence_path` relative to the app repository, `evidence_case`, `environment`, `build`, `actor`, `starting_state`, `observed_outcome`, and `status`. The generator verifies referenced files and stale fingerprints; the reviewer must verify the evidence actually supports the asserted branch. Do not include tokens, credentials, private documents or unredacted responses.

IDs hash repository-relative path, enclosing declaration, widget/component, callback, label and duplicate ordinal; they do not include line numbers. A source change invalidates matching evidence through the fingerprint. Moving, renaming or inserting an indistinguishable duplicate can require manual identity reconciliation. No generator can establish semantic equivalence automatically.

## Feature reconciliation

Feature and action associations below come from existing source maps or, when stated in raw rows, directory fallback. They are overlapping candidates. They do not independently establish that a particular callback implements every associated family. Local handlers are resolved syntactically only; inherited methods, closures passed through wrappers, dynamic dispatch, server-driven menus and feature gates require follow-up tracing.

| Feature | Families | Control sites associated | Server/system/operator sites associated | Cases executed by this inventory |
| --- | ---: | ---: | ---: | ---: |
| [F01 — Startup, splash, and guest access](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F01.md) | 5 | 33 | 0 | 0 |
| [F02 — Tenant and owner workspaces](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F02.md) | 6 | 68 | 0 | 0 |
| [F03 — Registration, login, email verification, and password recovery](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F03.md) | 7 | 126 | 0 | 0 |
| [F04 — Identity verification and protected-action gates](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F04.md) | 7 | 156 | 0 | 0 |
| [F05 — Profiles, account summaries, and profile editing](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F05.md) | 9 | 136 | 0 | 0 |
| [F06 — Settings, privacy, passwords, logout, and account deletion](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F06.md) | 8 | 126 | 0 | 0 |
| [F07 — Arabic/English, appearance, responsive UI, and accessibility](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F07.md) | 6 | 4 | 0 | 0 |
| [F08 — Tenant Home and accommodation discovery](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F08.md) | 8 | 236 | 0 | 0 |
| [F09 — Search, filters, recent searches, and map results](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F09.md) | 10 | 273 | 0 | 0 |
| [F10 — Property details, selected accommodation, and availability](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F10.md) | 10 | 331 | 0 | 0 |
| [F11 — Property photos, video, and tour entry points](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F11.md) | 5 | 237 | 0 | 0 |
| [F12 — Saved properties and group-shortlist access](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F12.md) | 6 | 40 | 0 | 0 |
| [F13 — Private decision notebook, comparisons, and saved searches](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F13.md) | 9 | 86 | 0 | 0 |
| [F14 — Server search alerts](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F14.md) | 7 | 51 | 0 | 0 |
| [F15 — Tenant viewing bookings and visit management](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F15.md) | 14 | 612 | 0 | 0 |
| [F16 — Post-visit decisions and viewing reviews](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F16.md) | 8 | 245 | 0 | 0 |
| [F17 — Direct messaging and permission-based phone contact](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F17.md) | 8 | 305 | 0 | 0 |
| [F18 — Lifestyle profiles and roommate matching](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F18.md) | 9 | 0 | 0 | 0 |
| [F19 — Housing groups, invitations, and membership](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F19.md) | 13 | 74 | 0 | 0 |
| [F20 — Group shortlists, votes, costs, visits, and applications](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F20.md) | 13 | 169 | 0 | 0 |
| [F21 — Private group chat, images, and voice notes](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F21.md) | 12 | 378 | 0 | 0 |
| [F22 — Tenant housing requests and owner housing offers](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F22.md) | 11 | 76 | 0 | 0 |
| [F23 — Commute-based housing search](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F23.md) | 9 | 21 | 0 | 0 |
| [F24 — Tenant housing assistant and dictation](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F24.md) | 8 | 15 | 0 | 0 |
| [F25 — Owner dashboard, property inventory, and moderation](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F25.md) | 9 | 465 | 0 | 0 |
| [F26 — Guided property creation and editing](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F26.md) | 12 | 442 | 0 | 0 |
| [F27 — Rooms, beds, room groups, and rental offers](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F27.md) | 10 | 419 | 0 | 0 |
| [F28 — Listing media, upload recovery, and ownership evidence](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F28.md) | 9 | 412 | 0 | 0 |
| [F29 — 360° and 3D virtual tours](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F29.md) | 12 | 128 | 0 | 0 |
| [F30 — Owner viewing decisions, availability, and calendar](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F30.md) | 10 | 435 | 0 | 0 |
| [F31 — Property analytics, advanced metrics, and owner revenue](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F31.md) | 6 | 72 | 0 | 0 |
| [F32 — Listing promotion campaigns](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F32.md) | 5 | 29 | 0 | 0 |
| [F33 — Owner listing assistant](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F33.md) | 6 | 20 | 0 | 0 |
| [F34 — Owner banner advertising and tenant placements](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F34.md) | 7 | 52 | 0 | 0 |
| [F35 — Rental interests and negotiated terms](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F35.md) | 14 | 162 | 0 | 0 |
| [F36 — Tenancy invitations and consent](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F36.md) | 8 | 30 | 0 | 0 |
| [F37 — Template-based lease drafts and legacy records](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F37.md) | 7 | 68 | 0 | 0 |
| [F38 — Structured rental agreements and commercial terms](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F38.md) | 8 | 106 | 0 | 0 |
| [F39 — Agreement documents, signing, and activation](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F39.md) | 8 | 69 | 0 | 0 |
| [F40 — My Rentals, Rental Center, and timeline](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F40.md) | 10 | 116 | 0 | 0 |
| [F41 — Rent invoices, billing periods, and schedules](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F41.md) | 8 | 25 | 0 | 0 |
| [F42 — Rent checkout, payment records, and uncertain-outcome recovery](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F42.md) | 10 | 30 | 0 | 0 |
| [F43 — Move-in and move-out handovers](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F43.md) | 8 | 141 | 0 | 0 |
| [F44 — Condition reports and private rental evidence](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F44.md) | 8 | 53 | 0 | 0 |
| [F45 — Security-deposit tracking](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F45.md) | 5 | 5 | 0 | 0 |
| [F46 — Maintenance requests, appointments, and cost approval](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F46.md) | 15 | 14 | 0 | 0 |
| [F47 — Formal tenancy changes and external-payment claims](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F47.md) | 9 | 41 | 0 | 0 |
| [F48 — Move-out notices and departure planning](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F48.md) | 7 | 41 | 0 | 0 |
| [F49 — Replacement tenants and candidate consent](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F49.md) | 9 | 45 | 0 | 0 |
| [F50 — Final settlement and financial closure](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F50.md) | 7 | 46 | 0 | 0 |
| [F51 — Rental disputes and participant responses](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F51.md) | 6 | 9 | 0 | 0 |
| [F52 — Refund requests and refund status](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F52.md) | 7 | 46 | 0 | 0 |
| [F53 — Owner beneficiary onboarding, payables, and payouts](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F53.md) | 8 | 110 | 0 | 0 |
| [F54 — Rental documents, statements, and contract history](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F54.md) | 7 | 188 | 0 | 0 |
| [F55 — Reviews of the tenancy](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F55.md) | 5 | 173 | 0 | 0 |
| [F56 — Tenant and owner subscriptions](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F56.md) | 7 | 51 | 0 | 0 |
| [F57 — My Invoices and invoice-first purchases](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F57.md) | 10 | 51 | 0 | 0 |
| [F58 — Notifications, unread counts, and deep links](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F58.md) | 9 | 83 | 0 | 0 |
| [F59 — Help center and support tickets](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F59.md) | 12 | 140 | 0 | 0 |
| [F60 — Public information pages and What's New](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F60.md) | 9 | 20 | 0 | 0 |
| [F61 — Cached reads, drafts, consistency, and recovery](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F61.md) | 12 | 82 | 0 | 0 |
| [F62 — Capabilities, device permissions, and provider integrations](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F62.md) | 9 | 40 | 0 | 0 |
| [F63 — Sokoun for Students](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F63.md) | 20 | 205 | 0 | 0 |
| [F64 — Company accounts and residential portfolios](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F64.md) | 104 | 538 | 0 | 0 |
| [F65 — Contextual feature guides](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F65.md) | 7 | 13 | 0 | 0 |
| [F66 — Confirmed experiences, reviews, and reputation](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F66.md) | 30 | 887 | 0 | 0 |
| [F67 — Collective housing tenders and exact packages](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F67.md) | 15 | 645 | 0 | 0 |
| [F68 — Shared-living lab, costs, and household arrangements](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F68.md) | 14 | 179 | 0 | 0 |
| [F69 — Company housing simulation and independent package decisions](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F69.md) | 11 | 599 | 0 | 0 |
| [F70 — Asset lifetime passport, observations, and assisted investigation](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F70.md) | 15 | 172 | 0 | 0 |
| [F71 — Transition network, moving cycles, and vacant-ended chains](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F71.md) | 12 | 170 | 0 | 0 |
| [F72 — My execution decisions, consent, mock provider steps, and partial recovery](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F72.md) | 17 | 586 | 0 | 0 |
| [F73 — Account sessions, compromise reporting and sensitive actions](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F73.md) | 13 | 406 | 0 | 0 |
| [F74 — Habitability reports, physical restrictions and inspected reopening](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F74.md) | 16 | 123 | 0 | 0 |
| [F75 — Operational cases, recovery quarantine and policy-controlled continuation](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F75.md) | 20 | 230 | 0 | 0 |
| [F76 — Administration, operator web interface and administrative API](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F76.md) | 27 | 0 | 0 | 0 |
| [F77 — Public marketing sites and installation boundaries](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F77.md) | 10 | 58 | 0 | 0 |
| [F78 — Standalone tour viewer and host protocol](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F78.md) | 11 | 13 | 0 | 0 |
| [F79 — Published business policies and accepted versions](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/features/F79.md) | 6 | 5 | 0 | 0 |

## Meaningful prerequisite boundaries

| Scope | Executable work still pending | Specific positive-completion dependency |
| --- | --- | --- |
| Authentication, navigation, settings, search, lists and private drafts | Traverse actual menus, protected continuation, field constraints, empty/error states, restart/account switching and denied access with owned test identities. | Mail/social delivery and verified-identity positive outcomes need their configured services and actual reviewer evidence; ordinary local/read/error branches do not. |
| Student solo/group/future planning and family sharing (F63) | Native profile, plans, member consent/withdrawal, exact changes, grants/revocation and historical access can be exercised against isolated actual HTTP state. | Live student rollout/enrollment assurance is not established; downstream legal signing/payment inherits F39/F42 dependencies. A synthetic academic record is not real enrollment. |
| Company administration/planning/approvals/holds (F64/F69) | Native accepted-role menus, employee denials, request correction, approval/reassignment, bounded holds and releases; distinguish seeded approver authority from actual onboarding. | D21 corporate contracting and D26 authority assurance remain unresolved; `contract_progression_available=false` is an intentional current server boundary. Native success tests must not invent signer/payer authority. |
| Owner publication, exact inventory and rental servicing | Owned unpublished supply can exercise drafting, uploads, validation and conflict/revision branches. Isolated approved fixtures permit service/authorization testing without claiming authentic signing or occupancy. | Actual publication requires moderation/evidence and live media services. Positive active-tenancy operations require a legitimate eligible signed contract; handover cannot be inferred from a fixture. |
| Signing, checkout, refunds, payouts, paid promotion and subscriptions (F32/F34/F39/F42/F52/F53/F56/F57) | Rejections, pending/unknown operation recovery, validation, replay and concurrency remain testable locally with their exact evidence category. | Deployed fake/disabled providers or unconfigured store receipts cannot establish real capture, settlement, refund, payout, signature or restored entitlement. Approved cancellation/refund rules remain prerequisites where absent. |
| Reputation, advanced execution and tours (F29/F66/F67–F72/F78) | Discover native controls, disabled explanations, planning/consent and invalidation paths; host/viewer protocol tests remain distinct. | Live capability/recovery gates are closed for several flows; planning-only or mock execution cannot prove provider fulfillment. |
| Worker/system/operator behavior (F58/F74/F75/F76) | Isolated job invocation, queue/retry/recovery tests and reviewer authority cases are executable; actual admin forms/actions require separate interaction coverage. | Production worker activation requires backlog/effect review; full recovery requires media, independent journal/control, provider reconciliation and approved reopening. Assessor absence must not be converted into clearance. |
| Android release/device behavior | Execute the current native test matrix and record actual menu/deep-link access, failure injection and participant views. | Physical devices, signed release configuration, OS permissions, notification delivery and store integration are separate from emulator/debug evidence. |

These are scenario-specific dependencies, not blanket reasons to stop testing a feature. Refer to [open decisions](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/OPEN_BUSINESS_DECISIONS.md) and the [background rollout review](/Users/demo23home/code/sukoon/sokoun/docs/sokoun-business-flows/verification-2026-10-19/BACKGROUND_ROLLOUT_REVIEW.md); this inventory does not change policy, activate providers or approve production jobs.

## Unmapped and derived-control boundaries

2134 sites have no existing exact feature association or directory fallback. They remain visible in the raw ledgers; shared infrastructure may serve many features. This is a mapping task, not evidence of a missing feature or a vulnerability.

| Example requiring explicit review | Kind |
| --- | --- |
| [apps/sokoun_app/lib/features/shared/app_lock/presentation/cubits/app_lock_cubit.dart:139](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/app_lock/presentation/cubits/app_lock_cubit.dart#L139) | `command_validation_or_continuation` |
| [apps/sokoun_app/lib/features/shared/app_lock/presentation/widgets/app_lock_cover.dart:56](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/app_lock/presentation/widgets/app_lock_cover.dart#L56) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/app_lock/presentation/widgets/app_lock_cover.dart:60](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/app_lock/presentation/widgets/app_lock_cover.dart#L60) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/app_lock/presentation/widgets/app_lock_settings.dart:32](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/app_lock/presentation/widgets/app_lock_settings.dart#L32) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/app_lock/presentation/widgets/app_lock_settings.dart:42](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/app_lock/presentation/widgets/app_lock_settings.dart#L42) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/disclosure/presentation/widgets/disclosure_section.dart:79](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/disclosure/presentation/widgets/disclosure_section.dart#L79) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/experience/data/data_saving.dart:30](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/data/data_saving.dart#L30) | `command_validation_or_continuation` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/cubits/preparation_cubit.dart:31](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/cubits/preparation_cubit.dart#L31) | `command_validation_or_continuation` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/cubits/preparation_cubit.dart:57](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/cubits/preparation_cubit.dart#L57) | `command_validation_or_continuation` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_alternatives_screen.dart:38](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_alternatives_screen.dart#L38) | `event_callback_requires_classification` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_alternatives_screen.dart:39](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_alternatives_screen.dart#L39) | `event_callback_requires_classification` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_alternatives_screen.dart:60](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_alternatives_screen.dart#L60) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_alternatives_screen.dart:67](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_alternatives_screen.dart#L67) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_settings_screen.dart:48](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_settings_screen.dart#L48) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_suggestions_screen.dart:53](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_suggestions_screen.dart#L53) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_suggestions_screen.dart:73](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_suggestions_screen.dart#L73) | `command_validation_or_continuation` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_suggestions_screen.dart:99](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_suggestions_screen.dart#L99) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_suggestions_screen.dart:121](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/experience_suggestions_screen.dart#L121) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/screens/preparation_board_screen.dart:51](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/screens/preparation_board_screen.dart#L51) | `user_event_candidate` |
| [apps/sokoun_app/lib/features/shared/experience/presentation/widgets/action_center_body.dart:70](../../../../../../sokoun/apps/sokoun_app/lib/features/shared/experience/presentation/widgets/action_center_body.dart#L70) | `user_event_candidate` |

Django model registrations imply generated forms and permission-sensitive actions. Static Python inventory cannot enumerate every rendered field/button/validation combination; browser model-form/action review remains required. Both React admin source trees are inventoried separately; duplicated code is not two independent confirmations. The historical API `mobile/` mirror, Figma prototype, tests, migrations, build outputs and generated Dart files are excluded from production control discovery and explained in the summary.

## Checks executed for this artifact

The generator parses every included source file, checks unique candidate/case IDs, reconciles every existing family, verifies source paths, and records parser diagnostics. Parser success and coverage bookkeeping do not prove runtime correctness, authorization, financial consistency, or the absence of additional paths. No application test is claimed by this command.
