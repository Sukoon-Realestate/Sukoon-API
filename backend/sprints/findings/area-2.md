# Area 2 — properties, viewings and virtual tours

> Audit notes and source evidence. The authoritative cross-domain sequence and finding-to-sprint assignment are in
> [the roadmap](../README.md) and [FINDINGS.md](../FINDINGS.md). Local suggested sprint numbers below describe phases,
> not an alternative implementation schedule. Companion scan manifests are summarized in [SOURCE_INVENTORY.md](../SOURCE_INVENTORY.md).


Read-only static review, 2026-11-08. Paths below are relative to `Sukoon-API/backend/`.

## Coverage and limits

Authoritative scope: all 186 files in `area-2-files.txt`, 19,610 source lines. All files were read by source/AST scans for definitions, decorators, ORM mutations/queries and I/O calls. 84 files additionally received manual full-file or substantial-path review; 102 received static scanning only. See `area-2-reviewed-files.md` for an honest per-file distinction. This is whole-scope static coverage, **not** an assertion that all 19,610 lines received exhaustive manual semantic review. Important property create/update/media/moderation/publication, visit create/decision/context/time, tour authoring/upload/session/storage/processing and capture selection paths were traced manually. Supporting reads included account-closure/new-business guards, chat publication policy, habitability guard, shared image serializer, and corporate portfolio-media storage callers.

No application files changed. No tests, servers, management commands, DB queries, network/provider calls, environment files, databases or private media were accessed. Source was parsed with Python `ast`, not imported. No runtime behavior, deployment setting, database engine, migration state or measured query count is claimed. Existing tests were searched for callers only, never run. Prior `docs/health/area-2.md` was not found in the supplied inventory/search; findings are a fresh static baseline, not claims that earlier findings were resolved.

## Checklist

| Check | Result | Evidence / finding |
|---|---|---|
| Consistent publication predicates | Fail | Canonical `services/public_access.py:4-16` is used on catalog/detail/images, but visit booking, public reviews/places and tours differ; A2-01, A2-02 |
| Current owner/tenant/company/group access | Partial | `services/viewing_access.py:19-70,131-180` checks membership/context; private ownership proof checks current actor; deeper concurrent role revocation across all feature callers not exhaustively reviewed |
| Ownership proof transport | Pass (static path) | `ownership_proof.py:12-45` checks active owner or staff role and streams protected identity bytes; detail hides legacy public references |
| Upload types/content/size | Partial | Tour parts are bounded and checksummed, capture completion decodes JPEG, panorama/GLB validators inspect contents; ordinary listing-media inputs have weaker contracts; A2-04, A2-06 |
| Input schemas and error boundaries | Fail | Rental inventory and image metadata use untyped nested JSON and raw conversions; A2-05, A2-06 |
| Visit duplication / capacity races | Partial | Booking locks users and property, rejects duplicate open visits and checks offer revision/occupants; schedule negotiation locks both users then property then visit. No concurrency execution. Publication gap remains A2-01 |
| Inventory revisions / changes | Partial | `normalize_inventory.py:25,169-175`, update service rechecks revision under listing lock and propagates impacts; malformed input and duplicate update route remain A2-03, A2-05 |
| Immutable attended decisions | Pass (static path) | Model unique/check constraints; `submit_decision.py:24-109` locks visit and checks participant/revision; owner cannot read decline reason (`continuation.py:177-190`) |
| Serializer/query growth | Fail | A2-07, A2-08, A2-09, A2-12, A2-13 |
| Tour viewer credential/scope protection | Partial | `sessions.py:15-83,223-263`, `views.py:378-513`: hashed credentials, locked single exchange, resource membership and current scope checks. Closure publication mismatch A2-02 |
| Processing leases/retries | Pass (static design) | `capture_worker.py:16-54,64-83,160-194`, `processing.py:143-250`, `processing_lease.py`: token fencing, bounded recovery and commit checks. Operational/reconstruction success not checked |
| Private storage retention | Fail (cross-area) | Independently verified portfolio-media cleanup loss; Area 3 owns finding, do not duplicate |
| All API views are CBVs | Fail (agreed architectural target) | 17 property DRF FBVs, 42 virtual-tour DRF FBVs; one additional Django HTML viewer FBV. A2-11 |
| Verified dead/dummy code | Partial | Fabricated rating/acceptance values verified, A2-10. Production-unreferenced helpers identified but dynamic external callers not ruled out; compatibility endpoints explicitly retained |

## Verified main findings

<a id="a2-01"></a>
### A2-01 — High — Publication checks are absent from visit creation and some public reads

**Evidence:** `views/visit_parts/property_visit_create_apiview.py:67-76` loads unrestricted `Property`; `services/visit_parts/property_visit_service_operations/visit_booking.py:34-38,40-93,113-115` locks it then checks self-booking, offer/revision, occupancy and habitability, but does not require public/verified/unretired/unblocked state. `PropertyVisit` inherits the new-business guard (`models/visit_parts/property_visit.py:15-16`), which checks account closure, not property publication. `assert_habitable` only checks habitability restrictions (`core_apps/features/services/rental_lifecycle/habitability.py:81-99`). The canonical predicate is `services/public_access.py:4-16`.

**Trigger/impact:** an authenticated unrelated user who retains a hidden, under-review, rejected or retired property's UUID can POST a visit (legacy property without rental inventory is the simplest path; offer-backed inventory also succeeds if the available offer/revision is retained). The visit and owner notifications are created and a property/owner summary is serialized in the creation response. This starts new business on deliberately unavailable inventory. Current account closure/restriction guards do exist and must be retained.

Related publication bypasses: anonymous public review lookup uses `Property.objects.only(...)` (`views/visit_parts/property_review_list_apiview.py:29-33`); `get_available_places` filters only verified/retired (`services/property_operations/property_catalog.py:142-152`) and omits owner restrictions/closure. These are the same policy-consolidation work item, not independent high-severity claims.

**Proposed fix / sprint:** Sprint 1, centralize a public-listing eligibility service and recheck it under the property lock immediately before creating the visit. Use canonical public reads for places/review endpoints while separately preserving explicitly authorized historical participant reads.

**Acceptance:** for every hidden/needs_revision/under_review/retired/blocked/restricted-owner/closure-pending state, creation returns controlled unavailable without a visit/event; an eligible public property still books; state change between lookup and locked create is caught. Anonymous places/reviews match the catalog's publication policy.

**Status:** verified source path; no request executed.

<a id="a2-02"></a>
### A2-02 — High — Published virtual-tour bytes remain public after the owner's closure request

**Evidence:** `virtual_tours/policy.py:127-141` checks account restrictions and property status/retirement, but not active account-closure requests or `owner.closed_at`. Canonical `core_apps/chat/moderation/policy.py:81-90` excludes both. `core_apps/users/services/account_closure.py:139-163` creates an active closure request without changing listing status. `virtual_tours/sessions.py:61-69,86-89,223-231` uses the duplicate tour predicate for public availability, new sessions and existing sessions. `virtual_tours/views.py:482-483` rechecks this predicate even on signed byte grants, so the mismatch reaches actual media serving.

**Trigger/impact:** request closure on an owner with an approved active tour. Ordinary public catalog/detail hide their property through `visible_properties`; tour availability and anonymous session creation can still expose the tour, and existing signed gateways continue serving it. Closure completion also leaves this predicate dependent on the property retaining verified status. This is a concrete cross-endpoint privacy/state inconsistency, not a missing-decorator inference.

**Fix / sprint:** Sprint 1, use the canonical property-publication predicate in tour authorization; define equivalent shared eligibility for building/complex managers. Recheck at session creation, exchange, manifest, credential renewal and byte access.

**Acceptance:** a pending closure immediately denies fresh sessions and all access from existing public sessions/grants; withdrawing closure restores only otherwise eligible publication; reviewer/owner preview permissions remain separately checked.

**Status:** verified source path; not exercised against a deployed tour.

<a id="a2-03"></a>
### A2-03 — Medium — An active alternate listing-update route bypasses the canonical concurrency and retry contract

**Evidence:** `properties/urls.py:143,165` exposes both detail PATCH and `/<id>/update/`. Canonical `views/property_parts/property_detail_apiview.py:203-233,256-264` locks the current listing, checks `If-Unmodified-Since`, validates against the locked instance, and uses `execute_idempotent`. Alternate `views/property_parts/my_property_list_apiview.py:143-149` validates the initially fetched object then calls save, with no header check or idempotency envelope. It also inherits PUT from `UpdateAPIView`. The underlying update service locks (`property_update.py:22-24`) and validates rental revision, but does not revalidate scalar optimistic versions or retry keys.

**Trigger/impact:** two owner editors load the same scalar fields. A newer edit succeeds; the stale client sends its prior `If-Unmodified-Since` to `/update/`, which ignores it and overwrites current content. Retried file-bearing writes can create repeated cover records. Authorization remains owner-only; this is a lost-update/retry bug, not an ownership bypass.

**Fix / sprint:** Sprint 1/2, route both API shapes through one listing command service and serializer validated against the locked row; enforce the same version/idempotency semantics while retaining URLs/method contracts or explicitly deprecating the alias.

**Acceptance:** stale scalar PATCH/PUT to either URL conflicts; same command key replays without creating extra media/revisions; different body with same key conflicts; concurrent rental-inventory revision checks continue to work.

**Status:** verified source path.

<a id="a2-04"></a>
### A2-04 — Medium — Cover replacement bypasses the 25-photo limit

**Evidence:** normal upload reserves/counts `images + pending` and rejects at 25 (`services/image_uploads.py:114-118`). `services/property_operations/property_update.py:135-151` always creates a fresh `PropertyImage` for each `main_image` replacement, with no cap and no pending-reservation count. `retained_image_ids` is optional, so old covers remain. Image signals invalidate approval (`media_signals.py:7-19`) but do not enforce capacity.

**Trigger/impact:** fill a property with 25 images and repeatedly PATCH new covers without a retention list. Each successful save adds another image. A pending normal upload can also be finalized after a cover save has consumed the remaining capacity. This defeats an explicit product/storage limit and expands detail serialization/moderation work.

**Fix / sprint:** Sprint 1, one locked media-reservation/capacity service for cover and gallery writes; account for pending reservations and intended deletions/replacements, avoid provider work while long-lived locks are held.

**Acceptance:** at the cap, replacement either replaces a defined record or returns controlled validation; cover+gallery concurrent writes never exceed 25; retry does not duplicate a cover; pending reservations are included.

**Status:** verified source path, concurrency outcome not executed.

<a id="a2-05"></a>
### A2-05 — Medium — Nested inventory/metadata values bypass typed validation and raise raw exceptions

**Evidence:** `rental_inventory_parts/normalize_inventory.py:18-25` accepts any dict with schema_version 1 then uses `int(value.get('expected_revision',0))`; `:53-67,83-88,140-149` assumes rooms, beds, offers, defaults and terms have expected types. `:149-156` rejects negative/NaN comparisons but positive `Decimal('Infinity')` passes the nonnegative check, without finite/precision/scale bounds. The top-level `PropertySerializer` uses `JSONField` (`property_serializer.py:42-44,62`). `property_validation.py:55-57` tests arbitrary amenity items as dictionary keys; `:88-93` checks metadata objects have id but does not type-check names/descriptions; `property_update.py:125-132` calls `.strip()` on them.

**Concrete triggers:** `expected_revision:'oops'`, `rooms:[null]`, `shared_defaults:[]`, an amenity object, or an existing-image metadata `name:[]` result in `ValueError`/`TypeError`/`AttributeError` instead of serializer validation. A price `'Infinity'` passes inventory normalization before reaching numeric projection/database conversion. Duplicate persisted room/bed IDs can be overwritten in dictionaries rather than explicitly rejected; this last behavior requires specification review before labeling a separate corruption finding.

**Impact:** malformed owner input produces server errors and accepted nonfinite/unbounded domain values can fail later in writes, search projections or agreement preparation. No DB error text disclosure is asserted.

**Fix / sprint:** Sprint 1 input-hardening, nested serializers/schema with strict shapes, nonboolean revision/capacity ints, finite fixed-precision money, bounded list/name sizes, unique identities, unknown-field policy, and typed image metadata.

**Acceptance:** malformed shapes, invalid revisions, object amenities, nonstring captions, Infinity/NaN/huge prices return field-level 400 before mutation/provider work; valid existing inventory IDs/revisions remain stable; normal monetary strings preserve exact Decimal semantics.

**Status:** source-verified exception/validation paths; no runtime requests.

<a id="a2-06"></a>
### A2-06 — Medium — Listing-media inputs have incompatible reference/file and video validation contracts

**Evidence:** listing image inputs use `CloudinarySerializerField` (`property_serializer.py:25`, `property_list_serializer.py:52-54`). Its shared implementation returns *any* non-data-image string as-is (`core_apps/profiles/serializers_parts/update_profile_serializer.py:12-32`), bypassing ImageField decoding. Recoverable upload then unconditionally executes `data['image'].seek(0)` (`services/image_uploads.py:139-154`), catches every error, persists unknown status and returns `UploadPending` 503. Thus a URL/public-ID string accepted by the serializer deterministically takes the pending-error path rather than a controlled input failure.

`video` uses an ordinary `FileField` subclass that only customizes output (`property_list_serializer.py:12-18`, `property_serializer.py:35-38`). Local validation checks client-supplied duration, not decoded video type/duration/size. `main_image_id`, `retained_image_ids` and `images_metadata` are accepted on creation (`property_serializer.py:26-44,96-105`), but `create_property` never removes these update-only keys before `Property.objects.create(**data)` (`property_creation.py:47-55,96`), so supplying one can produce unexpected-model-argument errors.

**Impact:** clients receive a false temporary provider problem for invalid image strings, potentially consuming pending upload slots until reconciliation. Update-only creation inputs cause server errors. Ordinary video acceptance lacks an application-controlled content/size/duration contract; provider rejection may mitigate invalid bytes, so arbitrary-file serving/execution is **not** claimed.

**Fix / sprint:** Sprint 1, separate uploaded-file fields from read-only/provider-owned references. Reject plain image strings on the upload endpoint or resolve a controlled owned-media reference. Validate video byte limits, container/codec/signature and actual duration through a bounded media service. Separate create/update command inputs so unsupported keys return controlled validation.

**Acceptance:** invalid string image produces 400 and no reservation/provider call; valid multipart/base64 images remain supported within limits; wrong video signature/type, too-large file and over-60-second decoded video fail predictably; update-only keys on create fail 400 or have explicit semantics.

**Status:** incompatible string/seek and unexpected-key paths verified statically; provider acceptance behavior unverified.

<a id="a2-07"></a>
### A2-07 — Medium — Visit list serialization performs repeated per-visit authorization/continuation queries

**Evidence:** tenant request and owner request lists select related basic property/user objects but do not preload decision/invitation/group context (`views/visit_parts/owner_property_visit_list_apiview.py:146-155`, `views/visit_parts/property_review_list_apiview.py:118-123`). `serializers/visit_parts/property_visit_serializer.py:113-119` calls `visit_context` for every row. That function calls participant, decision, invitation, historical agreement, eligibility and context (`services/post_visit_decision_parts/visit_context.py:12-55`). `linked_invitation.py:60-71,75-98,101-119` performs per-row queries, and `viewing_access.py:11-15,188-218` repeatedly looks up group/process/membership/participant decisions. Group attendee serialization adds another query loop.

**Trigger/impact:** raising page size from 10 to 100 increases authorization/context database work per row, and group visits add work per member. Separately `viewing_access.for_user:120-127` iterates *all* company visits before endpoint pagination and calls `can_read` for each. Existing select_related calls do not address these service-issued filter/exists queries.

**Fix / sprint:** Sprint 2 query-projection work, create a request-scoped visit read service that batches decisions, invitations, processes and current memberships, passes explicit maps to serializers, and expresses company visibility in SQL where practical. Keep mutation authority checks fresh and independent.

**Acceptance:** query-budget tests compare 1/10/100 personal and group visits; DB work is bounded by relation types rather than visits×participants. Revoked membership and owner changes still hide private continuation/reason fields. No caching across users/requests.

**Status:** static N+1 verified; no measured query counts.

<a id="a2-08"></a>
### A2-08 — Medium — Availability checks issue a closure query for each candidate slot

**Evidence:** `services/viewing_times.py:27-44` loops through all enabled slots over 180 days; each nonpast/nonbusy slot calls `slot_in_closure`, which executes `.exists()` (`services/availability_closures.py:28-36`). Weekly owner preview repeats the same pattern for up to 56 input slots (`views/owner_availability.py:29-30,48-56`). Appointment availability also loads all confirmed busy pairs without a date window (`viewing_times.py:29-31`).

**Impact:** one negotiation read can issue hundreds of DB closure checks as weekly schedules accumulate, even with zero closures. Historic busy schedules are loaded needlessly. This work repeats on propose/accept when validating revisions.

**Fix / sprint:** Sprint 2, batch relevant closures into ordered intervals once per request/locked command; restrict busy visits to the applicable date range; preserve explicit Cairo DST invalid/ambiguous-time handling.

**Acceptance:** closure query count remains constant for 1/56/1000 candidate slots; accepted/excluded slots and availability revision match existing semantics; DST fold/gap and overlapping closures are checked.

**Status:** static N+1 verified.

<a id="a2-09"></a>
### A2-09 — Medium — Saved-search reads materialize the complete result set and store unbounded JSON while holding the user lock

**Evidence:** `services/saved_search_reads.py:76-90` opens an atomic block and locks the user/search record; `:111-137` builds a dictionary containing every matching listing's ID/revision/timestamp and writes it to `SavedSearchRead`. `:139-159` puts all IDs back into `IN`/`CASE` clauses before normal page slicing. `.iterator(chunk_size=500)` limits fetch batches, not the size of the constructed dictionary/JSON or SQL parameter lists.

**Trigger/impact:** open a broad saved search on a large catalog, or repeatedly create fresh reads without reusing read ID. Even page 1 snapshots the full result set, making CPU/memory/DB JSON size proportional to the catalog and extending per-account lock duration. Multiple large retained snapshots multiply storage until purge. There is no maximum snapshot cardinality in this path.

**Fix / sprint:** Sprint 2, design bounded snapshot storage using an indexed read-item table or version/watermark strategy, enforce read/cardinality budgets and TTL cleanup, and move expensive noncritical projection outside long account locks while retaining consistent acknowledgment semantics.

**Acceptance:** 10/10k/large-catalog searches have explicit cardinality/memory/latency bounds; page reads do not emit unlimited parameter lists; current visibility/hidden preferences still apply; concurrent acknowledgments preserve revision conflict behavior.

**Status:** verified algorithmic growth; capacity thresholds require measurement.

<a id="a2-10"></a>
### A2-10 — Medium — Owner screens return fabricated acceptance and rating statistics

**Evidence:** `services/owner_dashboard_operations/owner_profile.py:65-75` returns 96% for owners with properties and no handled visits, otherwise 100% for no-property/no-history owners. `services/owner_dashboard_operations/owner_dashboard_overview.py:38-44` always returns `overall_rating:0.0`; `OwnerDashboardSerializer` forwards it (`serializers/owner_dashboard_parts/owner_dashboard_pending_visit_serializer.py:97-103`). The owner-profile path separately uses actual reputation summary (`owner_profile.py:58-62`), so the dashboard zero can contradict it.

**Impact:** new owners are presented with a success statistic unsupported by events; rated owners can see a false zero on another screen. This is verified dummy data, not an inferred dead-code finding.

**Fix / sprint:** Sprint 2/3, define no-history states (null/unavailable plus denominator), compute both screens from the canonical reputation/visit aggregate service, and remove hardcoded performance numbers from response examples where misleading.

**Acceptance:** zero-handled history shows no invented percentage; known accepted/rejected events compute the documented ratio; actual approved reputation is consistent across owner screens.

**Status:** verified constants reachable through active owner endpoints.

<a id="a2-11"></a>
### A2-11 — Medium architectural backlog — 59 DRF function endpoints remain, with mixed HTTP and domain logic

**Evidence:** AST inventory finds 17 property `@api_view` endpoints and 42 virtual-tour `@endpoint` endpoints. An additional HTML viewer uses `@require_safe`; it is separate from the API conversion requirement. Examples include property availability/closures, image order, post-visit decision and viewing commands; virtually all tour/capture/review routes are function endpoints. `virtual_tours/views.py:35-60` dynamically wraps API functions with auth/render/security-header policies. `capture_views.py:26-89` owns output selection ORM/state transitions; `views/image_order.py:17-94` owns locking, media rules and writes; `views/availability_closures.py:27-77` owns preview/commit mutations.

**Impact:** the agreed all-CBV target is unmet. Endpoint-local state machines and mutable response logic make the same security/concurrency policies easy to diverge (A2-01/A2-03). Existing `_parts` mixin/import facades alone do not establish domain separation.

**Fix / sprint:** Sprint 3, migrate by domain route groups to explicit APIView/generic classes with shared owner/public/viewer base policies; extract listing/media, appointment, capture-output and tour-lifecycle command/read services. Keep validators in typed serializers and retain small serializers for response formatting. Prefer cohesive domain modules over further mechanical one-method file splitting.

**Acceptance:** route-method-auth inventory confirms zero remaining DRF FBVs; preserve URL names, status/body envelopes, custom errors, locale, raw streaming PUT parsers, public-vs-account-vs-tour credential authentication, cache/referrer/nosniff headers, idempotency and version checks. The HTML viewer is either deliberately retained or converted separately to Django View without changing its CSP/template behavior.

**Status:** endpoint inventory verified statically, no security flaw inferred from FBVs themselves.

<a id="a2-12"></a>
### A2-12 — Medium — Capture-session payloads have multiplicative query and response growth

**Evidence:** `virtual_tours/capture_views.py:133-141` returns up to 20 sessions by calling `session_payload` per session with no prefetch. `capture_services.py:139-159` loads each latest manifest, rooms and up to 20 jobs. Every `job_payload` calls `retry_status` (`:22-55`, a child-job query at `:56`) and loads up to 2 selected revisions (`:49-50`). Each `revision_payload` loads assets/variants and sometimes rejection reason/capture-job/tour relations (`virtual_tours/services.py:10-47`).

**Impact:** an owner session list can expand into 400 nested jobs with per-job/revision DB work and complete nested authoring/report payloads. Output caps on individual lists do not make this a cheap list endpoint. The owner-only checks are present; this is performance/readability work.

**Fix / sprint:** Sprint 2, lightweight paginated session summaries with latest job state; detail endpoints for complete immutable jobs/revisions; query service uses prefetch/annotated latest relations and explicit response DTOs.

**Acceptance:** list query budget stays bounded as sessions/jobs/revisions increase, and list response has a documented maximum size; detail retains all necessary provenance/recovery fields; current ownership/deletion controls remain.

**Status:** static nested query/cardinality growth verified; no measured timings.

<a id="a2-13"></a>
### A2-13 — Medium — Public reviews and owner dashboard paginate after unbounded work, or not at all

**Evidence:** public property reviews build every legacy payload (`views/visit_parts/property_review_list_apiview.py:52-53`), build every new review payload (`:55`), sort/merge all rows (`:57`) and only then call paginate (`:60`). This is reachable anonymously. Owner dashboard returns the entire pending-visits queryset (`services/owner_dashboard_operations/owner_dashboard_overview.py:30-44`), and the serializer serializes `many=True` without paging (`owner_dashboard_pending_visit_serializer.py:103`).

**Impact:** page_size 10 still loads/sorts the full review history; accounts with many requests return arbitrarily large dashboard bodies. Neither behavior needs an N+1 to become a bottleneck.

**Fix / sprint:** Sprint 2, paginate at the database layer using a unified review projection or stable two-source cursor merge; return a bounded pending-visit preview and dedicated paginated link/count on the dashboard.

**Acceptance:** first-page work remains bounded for large review/request histories, sort order and total counts remain correct across old/new reviews, and dashboard preview count never exceeds its declared limit.

**Status:** verified algorithmic growth; no runtime benchmarks.

## Cross-area verified finding owned elsewhere

Area 3 owns **corporate portfolio-media data loss by virtual-tour cleanup**. Independently verified: `core_apps/features/services/company/portfolio_media.py:100-104` writes and stores a UUID blob from `virtual_tours.storage.write_blob`; the latter uses the same private root and provider prefix (`storage.py:32-60`). `virtual_tours/tasks.py:104-138` builds references without `ResidentialMedia`, then `:141-152` deletes old unreferenced local/provider objects. `remote_storage.py:136-152` accepts those same 32-hex keys and prefix; `cloudinary_storage.py:236-262` similarly removes unreferenced keys in `VIRTUAL_TOUR_CLOUDINARY_PREFIX`. Portfolio byte endpoint reads the same key (`core_apps/features/portfolio_views.py:147-148`). This is not a hypothetical namespace collision. Coordinate a complete storage-owner reference registry and retention test across areas. Do not count it again under an A2 main ID.

## Dead/dummy code decisions and unverified candidates

- **Verified production-unreferenced helper candidates:** `PropertyMediaMixin.upload_property_image/upload_property_images/update_property_image` (`services/property_operations/property_media.py:10,37,49`) have no production callers in repository-wide source reference searches. Bulk upload calls single upload internally; tests call bulk upload and metadata update. The active upload API calls `services.image_uploads.upload`, and active metadata API uses DRF directly. These are removal candidates, not proven unreachable external/dynamic API methods. Check supported integrations and test purpose before removing the facade. Do not delete solely from the text-reference count.
- **Intentionally active compatibility:** `home_visit_reminder` returns `{'banner':None}` by design and is routed at `urls.py:75`; `_get_upcoming_visit_banner` always returns None (`property_list_apiview.py:96-98`) and remains called at :111/:125. These are compatibility placeholders with stale docstrings, not dead code. Retain/retire through an explicit client contract decision.
- **Intentionally blocked legacy write:** `VisitReviewMixin.create_review` raises `ReviewError('client_update_required')`; the routed old review API remains useful as an explicit upgrade response. Do not label its lack of a review create implementation as an accidental dummy.
- **Unverified:** stronger ordinary-video file validation may exist in Cloudinary/provider behavior, but the app contract is absent (A2-06); no arbitrary-file execution or SSRF claim is made.
- **Unverified:** concurrency across every corporate/group/academic caller, reviewer profile revocation during publication, storage sweep racing a just-committed artifact, processor CPU/memory budgets for all reconstruction inputs, and exact production query plans. Source barriers were inspected on main paths; these require focused integration/load/concurrency checks.
- Static scans were performed for all models, serializations, wrappers, helpers and schema files, but 102 files did not receive deep manual review. No assurance is given that the remaining scope has no bugs.
