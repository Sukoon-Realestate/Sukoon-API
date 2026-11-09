# Area 3 — rentals, company/student/shared housing and planning

> Audit notes and source evidence. The authoritative cross-domain sequence and finding-to-sprint assignment are in
> [the roadmap](../README.md) and [FINDINGS.md](../FINDINGS.md). Local suggested sprint numbers below describe phases,
> not an alternative implementation schedule. Companion scan manifests are summarized in [SOURCE_INVENTORY.md](../SOURCE_INVENTORY.md).


Read-only static review. Paths below are relative to `Sukoon-API/backend/`. No application edits, tests, servers, management commands, databases, secrets or network were used. Priority is proposed sprint priority; architecture items are delivery requirements, not claimed security vulnerabilities.

## Coverage and method

All 469 assigned production Python files (72,122 lines) were read by an AST inventory and structural/text scans: parseability, functions/classes/imports, view decorators, query calls inside loops, dynamic execution and explicit placeholder markers. All parsed successfully. This is **all-file static scanning**, not a claim that every line was manually read. The separate JSON inventory records all assigned paths. 482 syntactic loops/comprehensions contain query-like calls; this is a triage count, not 482 proven N+1 defects.

AST found 78 direct `@api_view` function nodes, 107 `@planning_api`, 76 `@company_api`, 21 `@endpoint` nodes and 43 classes with view-like bases. These are syntax counts, include decorator implementation wrappers, and are not distinct resolved URL counts. No `exec`, `eval` or `compile` calls were found in assigned files.

Detailed traces concentrated on maintenance creation/actions/models/permissions; condition reports; company offers/discovery/visibility/role contexts and routes; portfolio media upload/read/storage/cleanup; signing/private documents; enrollment evidence/reviews; shared housing consent and allocation; transition matching/vacancies; tender computation; scenario computation/recovery; discovery expiry; and public reputation reliability. Some printed output for large grouped reads was truncated; only the visible relevant paths support the findings. Commerce/store ownership was excluded after coordinator clarification. Cross-area files were read only to establish caller/storage/model boundaries.

## Verified findings and sprint tasks

<a id="a3-01"></a>
### A3-01 — P1 — active portfolio images are deleted by the tour-storage cleanup

- Evidence: `core_apps/features/services/company/portfolio_media.py:100` writes a random blob with `virtual_tours.storage.write_blob`; `:103` stores its key in `ResidentialMedia.blob`. `core_apps/features/portfolio_views.py:147` serves that blob. `core_apps/virtual_tours/tasks.py:104` starts the cleanup's reference set with TourAsset keys; `:120`, `:124`, `:133`, `:135` add capture/job/variant/upload references, **no ResidentialMedia keys**. `:139` sets seven-day threshold; `:141` removes unreferenced local files; `:152` passes the same incomplete set to remote orphan sweeping. `core_apps/virtual_tours/storage.py:32` allocates the random storage identity.
- Trigger/impact: upload a valid portfolio building/complex photo and retain it beyond seven days. When cleanup runs, this active media has no recognized storage reference and can be deleted, breaking its authenticated byte endpoint and losing the original stored file. Applies to locally retained keys and remote orphan collection; whether scheduler runs in production was not checked.
- Task: register portfolio media in the shared storage reference graph, define retention for removed versus ready/reviewed media, and centralize reference enumeration so another storage consumer cannot be omitted. Coordinate with properties/tours area; this report owns the portfolio consumer bug.
- Acceptance: a storage cleanup fixture retains a ready ResidentialMedia blob and its remote equivalent after the threshold, removes an actually unreferenced key, and verifies byte retrieval after cleanup. Explicitly decide retention for removed media.
- Related lower-priority verified path: concurrent calls to `portfolio_media.upload` both write blobs before the row lock (`:100` before `:101`); the losing caller sees ready at `:108` and does not attach/delete its new key. A removal during I/O also raises after writing. Add a claimed upload identity or compensate unused writes as part of this lifecycle task; do not solve it by retaining every orphan forever.

<a id="a3-02"></a>
### A3-02 — P2 — personal maintenance mutations do not validate their complete command body

- Evidence: `core_apps/features/rental_phase5_views_parts/maintenance_requests.py:36` enumerates required keys but `:48` calls `int(request.data["expected_revision"])` directly. `:63` validates only MaintenanceAccessTimesSerializer; `:75` creates title/description/category/priority directly from request data. The serializer in `rental_serializers_parts/maintenance_cost_decision_serializer.py:10` contains only access_times; its array/text values have no count/text limits. Model title/category/priority are bounded strings at `model_parts/maintenance_changes.py:34`. `rental_phase5_views_parts/maintenance_action.py:57` similarly converts revision directly; `:134` passes appointment_at directly into parse_datetime. Shared exception handler `core_apps/common/renderers.py:34` returns 500 for unhandled exceptions.
- Trigger/impact: an otherwise authorized participant sends expected_revision=`"abc"`, null or an object: ValueError/TypeError becomes a 500 instead of a structured 400. Excess-length title/category/priority reach database constraints rather than serializer errors; dict/list values and unbounded access text can be persisted/coerced inconsistently. Mutation authorization itself was traced through `_lease`, `_maintenance` and `cycle_actions`; this finding is input validation, not an authorization bypass.
- Task: introduce complete MaintenanceCreateBody and action-specific command serializers (UUID key, strict nonnegative integer revisions, bounded strings/lists, controlled categories/priorities, timezone-aware datetimes); use validated_data throughout the service boundary. Preserve the documented legacy access_times string contract deliberately.
- Acceptance: malformed revisions (bool/null/string/list), invalid request keys, non-string/oversize text, malformed appointment types and oversized access arrays consistently return 400 with zero domain writes. Valid stale revisions remain 409. Existing legacy access_times replay remains stable.

<a id="a3-03"></a>
### A3-03 — P2 — transition matching rejects all near-metro requirements

- Evidence: `core_apps/features/services/transition_network/solver.py:97` builds property_amenities; its list includes `near_metro` at `:107` but `:112` reads every name through `getattr(prop, "has_" + name, False)`. The actual field is `core_apps/properties/models/property.py:184` (`near_metro`); there is no has_near_metro field. `solver.py:163` rejects requirements not contained in this generated amenities list. Both outgoing sources (`:83`) and vacant endpoints (`services/transition_network/vacancies.py:74`) use this function. The other housing matcher handles the exception correctly at `services/housing_offer_matching.py:11` and `:37`.
- Trigger/impact: a move intent requiring near_metro cannot match even a property with near_metro=True; output becomes unknown/infeasible under the bounded search despite eligible inventory.
- Task: use the canonical amenity-to-model-field registry across all planners instead of locally synthesizing names.
- Acceptance: source and vacant-endpoint matching include metro-positive supply, exclude metro-negative supply, and preserve all other amenity mappings.

<a id="a3-04"></a>
### A3-04 — P2 — company offer discovery does full-market work before pagination and resolves each scope twice

- Evidence: `core_apps/features/company_views.py:558` calls `page(request, results(...), ...)`; `services/company/discovery.py:153` creates a Python list and `:155` traverses every matching offer before returning it at `:167`. Per offer `suitability` invokes offer_payload at `:34`, which resolves scope and availability (`services/company/offers.py:303`, `:313`); it invokes resolve_scope a second time at `discovery.py:55`. resolve_scope loads descendants/containers and owner authority; its Property query selects building/complex but not city (`offers.py:111`), while discovery dereferences each property city at `discovery.py:71`.
- Trigger/impact: requesting a small page with request_id processes the full eligible offer market, repeats scope/authority queries and causes additional city queries per included property. Work and response preparation memory grow with market size, not requested page size. `iterator(chunk_size=100)` bounds cursor fetches, not the accumulated results list.
- Task: build a bulk-loaded offer-scope/read snapshot, reuse it for price/authority/location/availability, and design database predicates or a bounded/materialized search result before paginating. Preserve correct suitable_only filtering before count/pagination.
- Acceptance: query-count and row/heap budgets on 1/25/250 offers and multi-building scopes; first-page cost bounded or explicitly moved to a bounded background search. Results/counts unchanged for date availability, capacity, requirements and selected offer IDs.

<a id="a3-05"></a>
### A3-05 — P2 — company visibility scans every candidate before company/lease filters and pagination

- Evidence: `core_apps/features/company_tenancy_views.py:61` calls access.visible before applying company_id (`:66`) and lease_id (`:71`). `services/company/tenancy_access.py:279` evaluates all candidates in a list comprehension and calls roles per candidate at `:281`; roles (`:103`) queries revocations, membership, mandates, assignments, open changes and role context. Incoming-owner checks also materialize candidates at `:264`. `company_contract_views.py:81` similarly obtains visible before company filtering at `:86`; `services/company/contract_access.py:135` calls can_read for every candidate; page projection fetches each preparation again at `company_contract_views.py:91`.
- Trigger/impact: a user with many historical/multi-company records causes full candidate authorization/query fan-out even requesting one company's first page or a single lease. The current checks are important and must not be removed to improve speed.
- Task: accept validated scope constraints in visibility selectors, apply those before evaluation, bulk-fetch roles/authority facts and express eligible IDs with joins/Exists where possible; retain current membership/mandate/revocation rules before counts and disclosure.
- Acceptance: first page/specific company/specific lease query growth budgets; revoked membership, wrong active role, prior signers, incoming owners and private employee rows still match detail authorization. No hidden rows in counts.

<a id="a3-06"></a>
### A3-06 — P2 — anonymous public reputation requests issue at least four extra queries per invoice

- Evidence: `core_apps/features/reputation_views.py:725` declares AllowAny and calls public_summary. `services/reputation/public_summary.py:137` computes payment_reliability synchronously. Its year-window invoice loop (`:43`) issues payment_attempts.filter(...).exists at `:47`, operational-case exists at `:50`, dispute exists at `:58`, refund exists at `:64`. Prefetching payment_attempts at `:40` does not satisfy the filtered related-manager query. Allocation loading is already prefetched and should be retained. The review aggregation also loads all matching approved rows (`:127`).
- Trigger/impact: repeatedly viewing a company/tenant public summary recomputes history with query cost O(invoice count), at least 4N checks plus initial/prefetch/review eligibility work. Public no-store response at reputation_views.py:731 does not provide a server-side computation cache. No live request timing was measured.
- Task: annotate exclusion predicates with Exists or bulk-build maps, consume prefetched payment attempts without filtered-manager queries, and evaluate a policy-aware precomputed aggregate/invalidation design.
- Acceptance: 1/10/100 invoice query budgets with dispute/refund/uncertain-payment exclusions; preserve sample thresholds, effective due dates, captured allocation timing and private-field exclusion. Verify revoked/changed review sources invalidate any cache.

<a id="a3-07"></a>
### A3-07 — P2 — maintenance collection is unbounded and still performs a query per maintenance row

- Evidence: `core_apps/features/rental_phase5_views_parts/maintenance_requests.py:29` materializes every lease maintenance request; `:34` synthesizes count/next=None rather than using FeaturePagination. `maintenance_payload.py:103` calls source_invoices for each request; that helper issues BillingSourceLink.filter at `services/billing_sources.py:16`. The lease reverse manager already associates each child with its parent; no additional lease-query claim is needed. Those source modules are commerce-owned; the root issue here is per-item projection invocation from the area-3 collection.
- Trigger/impact: long-lived leases with many requests/events return all history and cause additional per-request invoice queries. Event/evidence prefetching mitigates two relations but does not bound response size or the other lookups.
- Task: paginate collection using existing API pagination conventions and batch invoice linkage/read context; keep detail history behavior explicit or paginate history separately without silently truncating it.
- Acceptance: 1/25/250 maintenance rows with events/evidence have bounded page payloads and constant or bounded query growth; verify links/count/order and both participant roles.

<a id="a3-08"></a>
### A3-08 — P2 — discovery expiry maintenance repeatedly scans and updates all expired history

- Evidence: `core_apps/features/services/planning_parts/validate_payload_types.py:84` purge_expired_discovery filters every CommuteSearch/TenantAssistantTurn whose expires_at<=now at `:89` without a pending-purge predicate or batch. `:91` materializes both complete ID sets; `:94` builds an id__in update; `:101`/`:102` update all expired rows, including previously scrubbed ones. `tasks_parts/process_rental_closure.py:98` calls it from the periodic closure worker.
- Trigger/impact: each recurring sweep reprocesses all historical expired discoveries indefinitely. Memory, IN-list size and writes grow with lifetime history and can delay unrelated closure work. This is not a claim that expired private inputs remain readable; scrubbing exists.
- Task: add an explicit durable scrub marker or filter for rows still holding private data, process keyset batches, and update related operation receipts in bounded batches. Define retention of already-redacted tombstones separately.
- Acceptance: first sweep clears due private payloads/receipts; repeated sweep touches zero completed rows; dataset beyond batch limit resumes safely and stays within memory/query budgets; expired read paths remain denied.

<a id="a3-09"></a>
### A3-09 — P2 — tender calculation holds property/domain locks during combinatorial work

- Evidence: `core_apps/features/services/housing_tenders/jobs.py:13` opens transaction.atomic, locks run at `:15`, calls get_tender(...lock=True) at `:32`, then invokes calculate at `:37` before transaction exit. `services/housing_tenders/construction.py:121` locks every candidate Property; `:128` starts per-line/per-person availability and enrollment queries; `:170` initializes the three-second search deadline only after that preparation. Recursive visit at `:172` runs before final package revalidation/persistence (`:250`). The bounded search limits are positive controls, but the entire preparation plus search runs under inventory locks.
- Trigger/impact: a package computation contends with leases/listing updates for all up-to-48 candidate lines, including lines never selected. Preparation can exceed the nominal search deadline because it is outside that timer. No live lock-duration measurement was made.
- Task: capture versioned immutable inputs in a short transaction, compute outside locks, then reacquire affected roots in stable order to revalidate and commit exact packages; retain source digest and explicit bounded/unknown outcomes.
- Acceptance: concurrent computation and normal reservation/listing changes preserve no-stale-publication/no-double-hold behavior, while lock duration excludes solver time. Keep node/time limits, cancellation and source-changed outcomes reviewable.

<a id="a3-10"></a>
### A3-10 — P1 delivery prerequisite — CBV migration must replace function-name-dependent company route policies explicitly

- Evidence: `core_apps/features/company_views.py:57` defines company_api; its wrapped function is passed to role_routes.authorize at `:69`. `services/company/role_routes.py:8` derives module from function.__module__ and `:9` derives function.__name__; the policy table keyed by concrete module/function names starts at `:35`. Endpoint-method sets/decorators are distributed across custom wrappers; `services/planning_parts/validate_payload_types.py:188` planning_api adds verified-account/capability checks, payload type validation and private no-store behavior; `rental_lifecycle_views/common.py:10` endpoint adds auth/rendering. These are existing behavior dependencies, not a currently proven bypass.
- Task: make each CBV method's capability/role policy explicit metadata or permission classes, with reusable validation/rendering/response policies; convert route families with contract fixtures. Exact FBV examples: maintenance_requests (`rental_phase5_views_parts/maintenance_requests.py:26`, GET/POST); companies (`company_views.py:138`, GET/POST); condition_reports (`planning_condition_views_parts/condition_report_action.py:29`, GET/POST); summary_grants (`rental_summary_views.py:127`, GET/POST); lifecycle application_profile (`rental_lifecycle_views/applications.py:24`, GET/PATCH).
- Acceptance: URL names, method/OPTIONS behavior, parsers, auth, capability gates, role headers, per-method permissions, throttles, response renderer/status/envelope/cache policy and error codes remain stable. Replay authorization still runs before replay; actor/domain lock ordering and on_commit dispatch remain intact. Explicitly exercise GET/POST/PATCH differences and role names after class conversion. A blind change from function names to generic post/get cannot preserve the current role policy by itself.

<a id="a3-11"></a>
### A3-11 — P2 architecture — large mixed projections/handlers still hide domain responsibilities after file splitting

- Evidence: AST lengths: `services/company/tenancy_projection.py:27` payload is 535 lines (roles, assignment loading, capabilities, provider status, changes, billing/closure projections); `planning_group_views_parts/housing_group_action.py:31` handler is 259 lines including nested mutation closure; `rental_phase5_views_parts/maintenance_action.py:38` is 184 lines coordinating validation, state changes, cost/access consent, invoice creation, audit and receipt; `services/company/tenancy_maintenance.py:126` act is 205 lines. Stable facade modules re-export public APIs, but moving a large function into *_parts has not removed these mixed responsibilities.
- Task: define named bounded services/selectors for maintenance commands and role-aware company read models, then make CBVs request/response adapters. Centralize shared policy facts and canonical amenity field mappings; use small named projections receiving preloaded read context. Organize by domain/use case, not arbitrary line count or one function per file. Preserve model/import identities where migrations/callers depend on them.
- Acceptance: each converted view delegates validation/authorization/command/query responsibilities clearly; projections do not silently execute unbounded relation queries; repeated policy calculations use one request-scoped snapshot. Review representative complete workflows, rather than treating a lower maximum filename length as acceptance.

## Security/validation checks that were traced without finding a new bypass

- Private student evidence upload validates MIME/size/digest through private_media_policy and persists pending inspection; read requires uploader or scoped KYC reviewer and safe malware state (`student_verification_views.py:81`, `:178`). evidence_storage performs PNG decode/pixel checks, checksum checks, scanner gating and bounded reads. No arbitrary file-extension-only upload acceptance was inferred.
- Portfolio uploads enforce intent size/digest, decoded PNG/JPEG/pixel limits and re-encode to strip EXIF/GPS (`services/company/portfolio_media.py:76` onward). The verified defect is storage lifecycle integration (A3-01), not missing content inspection.
- Company roles are narrowed by HTTP company context, current membership/mandates and private revocations (`services/company/role_context.py`, `tenancy_access.py`, `contract_access.py`). This review's performance tasks must preserve those checks.
- Signing document rendering escapes values and recipient names, and signed/private rental downloads bind user/security epoch/session/current role and private revocation (`services/signing_documents.py`; `services/private_rental_documents.py`). No general signing or private URL authorization bypass is asserted from these traces.
- Shared housing uses root locks, explicit participants, exact selection/term consents and later revalidation (`services/shared_housing/commands.py`, `validation.py`); condition creation validates tenancy status, signed selection, bounded items/evidence and baseline revisions in `_report_values` even though the public view itself delegates those checks. Missing view-local checks were not reported as vulnerabilities.

## Cleanup and unverified candidates

No production deletion candidate is proven safe from this area review. The mock commute function is actively referenced by commute_searches and gated by fake_provider_available plus PLANNING_MOCK_DISCOVERY; its existence is not trash. Evidence fake scanning also has explicit runtime gates. Existing stable facade exports can be public import contracts; large import lists alone do not prove dead code.

Cleanup sprint tasks: inventory mock/provider/demo call sites and runtime gates; classify test fixtures versus reachable production adapters; verify imports/URL registrations/task registries/management commands/migrations before deleting a symbol; remove only confirmed unused imports/exports with import-contract checks. Centralize duplicate policy/field mappings shown by A3-03 and retire facades only after reference migration. No fake runtime path should be removed simply to satisfy a code-count target.

Unverified: broader policy/permission regressions in CBV conversion; production data sizes/latencies; deployed scheduling and storage backends; complete DB-index execution plans; all signing/provider failure races outside detailed traces. Existing tests were not run and no pass status is implied.
