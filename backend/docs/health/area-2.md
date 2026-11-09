# Area 2 — Properties and Tours
**Last reviewed:** 2026-11-09, commit 0becde88, full scope (`core_apps/properties/`, `core_apps/virtual_tours/`)

## Findings
| ID | Severity | Category | Problem | Evidence | Proposed fix | Status |
|---|---|---|---|---|---|---|
| S2-N1 | low | performance | Tenant ratings view `TenantMyRatesListAPIView` does not prefetch property owner avatar, triggering potential 1-query overhead if displayed in UI | `core_apps/profiles/views_parts/user_settings_apiview.py:133` | Add `select_related("visit__property__owner")` to queryset | verified |
| S2-N2 | medium | correctness | Viewing proposal alternative changes in `viewing_times.py` can receive concurrent proposal submissions within the same second before db constraint locks | `core_apps/properties/views/viewing_times.py:145` | Wrap alternative proposals in `select_for_update` on visit record | verified |

## Security checks
| Check | Result | Evidence | Finding |
|---|---|---|---|
| Public publication & moderation predicates | pass | `core_apps/properties/views/property_parts/property_list_apiview.py:48` (`status=VERIFIED`, `retired_at__isnull=True`, `moderation_blocked=False`) | None |
| Private ownership proofs and title deed access | pass | `core_apps/properties/ownership_proof.py:15` (enforces owner ID or staff reviewer check; raises 404 on unauthenticated/unauthorized) | None |
| Visit capacity & cancellation concurrency | pass | `core_apps/properties/views/viewing_commands.py:82` (atomic transaction with optimistic revision locking) | None |
| Virtual tour capture & upload validation | pass | `core_apps/virtual_tours/capture_validation.py:22` (validates dimension, EXIF, format, manifest integrity) | None |
| Tour processing leases & superseding | pass | `core_apps/virtual_tours/processing_lease.py:14` (`ProcessingLease` heartbeats and supersedes stale workers) | None |
| Tour viewer storage isolation | pass | `core_apps/virtual_tours/viewer_views.py:35` (rejects path traversal, restricts static assets to approved bundle) | None |
| Dual-identity review prevention | pass | `core_apps/virtual_tours/review_access.py:29` (prohibits self-review across linked accounts) | None |

