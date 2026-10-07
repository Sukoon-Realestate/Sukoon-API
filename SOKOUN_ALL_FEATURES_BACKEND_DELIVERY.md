# Sokoun all-features backend delivery

## 1. Delivery identity

- Repository implementation date: 2026-10-08
- API prefix: `/api/v1/`
- Free-feature prefix: `/api/v1/features/v1/`
- Time zone: `Africa/Cairo`; stored instants use Django UTC-aware datetimes.
- Rental inventory contract: schema version 1.
- Deployment status: implemented and tested locally; not deployed to staging by this change.
- Provider status: signing/payment hosted URLs are server-created session placeholders until approved providers and webhooks are configured. AI uses a bounded facts-only local fallback until a provider is selected.

## 2. Implemented feature status

| Area | Status | Important behavior |
|---|---|---|
| Free configuration | Implemented | Owner boost options and tenant alert cadences; no products, credits or entitlements. |
| Promotion | API/persistence implemented | Ownership, verified publication, active-campaign conflict, replay, sponsored projection. Expiry/impression workers remain. |
| Search alerts | API/persistence implemented | Complete JSON filters, scope/range validation, revision conflicts, pause/delete and idempotency. Matching/push worker remains. |
| Analytics | Implemented | Owner-only 7/30/90-day measured views, saves and viewing conversion with null distinct from zero. |
| AI suggestions | Safe fallback implemented | Owner authorization, public-facts whitelist, ar/en, bounded output and replay. External provider/monitoring remains. |
| Lease configuration/eligibility | Implemented | Approved template catalog and explicit `LeaseEligibleTenant` records; no unrestricted user directory. |
| Leases | Core implemented | Owner/tenant isolation, property filter, minor-unit rent, offer snapshots, revisions, cancellation and signing sessions. Provider signature/webhook remains. |
| Rent invoices | Core implemented | Workspace/lease/status/order filtering, overdue transition, exact amounts, offer snapshots and tenant-only checkout. Settlement webhook remains. |
| Rental inventory | Core implemented | Stable IDs, client-key resolution, four scopes, defaults/overrides, overlap checks, revisions, availability/archive fields and full read-back. |
| Discovery/owner collections | Implemented core | Property-grouped summary, sponsored flag and public/owner rental-scope filtering. Mixed-period minimum is omitted. |
| Exact-offer favorites | Implemented | `(user, property, offer)` identity, immutable snapshot, DELETE body and response echo while preserving legacy behavior. |
| Offer visits | Implemented | Fresh offer/revision validation and immutable snapshot. Managed schedules use locked slot validation; legacy properties without any schedule retain compatibility. |
| Availability freshness | Implemented | `POST properties/{id}/confirm-availability/` stores a real owner-confirmed instant. |
| Chat idempotency | Implemented | Shared optional `client_message_id`, sender/conversation uniqueness, content conflict and socket acknowledgement. |

## 3. The 20 requested method/path contracts

All paths below are relative to `/api/v1/`. Collection responses use `results`, `count`, `per_page`, `total_pages`, `next`, and `previous` inside the existing renderer's `data` envelope.

| Requested method/path | Actual path | Status/notes |
|---|---|---|
| GET `features/v1/configuration/` | unchanged | Implemented; validates owner/tenant workspace and ar/en titles. |
| GET `features/v1/boost-campaigns/` | unchanged | Implemented, owner-scoped. |
| POST `features/v1/boost-campaigns/` | unchanged | Implemented; free option lookup, ownership/publication/conflict/idempotency. |
| GET `features/v1/search-alerts/` | unchanged | Implemented, tenant-account scoped. |
| POST `features/v1/search-alerts/` | unchanged | Implemented with canonical JSON filter persistence. |
| GET `features/v1/search-alerts/{id}/` | unchanged | Implemented; invisible cross-account IDs return not found. |
| PATCH `features/v1/search-alerts/{id}/` | unchanged | Implemented; revision + request key required. |
| DELETE `features/v1/search-alerts/{id}/` | unchanged | Implemented; JSON body supported and returns cancellation receipt. |
| GET `features/v1/owner-analytics/{property_id}/` | unchanged | Implemented for 7/30/90 days. |
| POST `features/v1/listing-suggestions/` | unchanged | Implemented with safe local generator/provider boundary. |
| GET `features/v1/lease-configuration/` | unchanged | Implemented. |
| GET `features/v1/lease-tenants/` | unchanged | Implemented; property ownership + explicit eligibility. |
| GET `features/v1/leases/` | unchanged | Implemented; workspace and optional property filter before paging. |
| POST `features/v1/leases/` | unchanged | Implemented; template, eligibility, dates, money and optional offer validation. |
| GET `features/v1/leases/{id}/` | unchanged | Implemented for participants only. |
| POST `features/v1/leases/{id}/signing-session/` | unchanged | Session/revision/replay implemented; provider completion remains. |
| POST `features/v1/leases/{id}/cancel/` | unchanged | Draft-only owner cancellation implemented. |
| GET `features/v1/rent-invoices/` | unchanged | Implemented; workspace, lease, OR-status and deterministic ordering. |
| GET `features/v1/rent-invoices/{id}/` | unchanged | Implemented for lease participants. |
| POST `features/v1/rent-invoices/{id}/checkout/` | unchanged | Server-authorized quote/session implemented; provider settlement remains. |

## 4. Rental/property contract mapping

- `POST properties/create/`: accepts multipart `rental_inventory`, requires `X-Rental-Offers-Version: 1` and `Idempotency-Key` for versioned creates, and returns the full saved property.
- `GET/PATCH properties/{id}/`: reads/writes inventory schema 1 and enforces `expected_revision`; owner reads include actions while public reads omit archived/unavailable offers.
- `GET properties/` and `GET homepage/`: return `rental_schema_version` and `rental_summary`; `rental_scope` filters physical properties before pagination.
- `GET properties/owned/`: supports `rental_scope` and returns property counts, scopes and manageable-offer count.
- `POST/DELETE properties/{id}/save|unsave/`: optional `offer_id`, exact snapshot and offer-specific identity. Legacy empty-body unsave remains `204`; offer-specific delete returns an acknowledgement body.
- `POST properties/{id}/visits/`: accepts `offer_id` and `expected_offer_revision`, stores an immutable snapshot and never mutates rental availability.
- `POST properties/{id}/confirm-availability/`: owner-only timestamp confirmation.

Detailed accommodation fields not interpreted by overlap rules are preserved in the versioned room/bed/offer/shared JSON and returned unchanged. Media IDs remain references to property media; production should add explicit foreign-image validation before enabling the media-association mobile flag.

## 5. Concurrency and security

- Feature mutations persist `(account, operation, request_key)` plus a request fingerprint; changed-key reuse returns `409`.
- Alert and lease changes reject stale revisions.
- Property inventory writes run transactionally and reject stale revisions/overlap without partial persistence.
- Managed visit schedules lock and recheck slots; a viewing transition does not modify rental inventory.
- Chat message identity is unique by conversation, sender and `client_message_id` across REST and WebSocket.
- Property ownership proof is still owner/staff-only and is not included in public offer data.
- Lease and invoice cross-account lookups are concealed as not found; payment amount comes only from the stored invoice.

## 6. Remaining work before production capability flags

- Configure actual signing, payment and AI providers; authenticate and deduplicate webhooks; reconcile delayed events.
- Build scheduled campaign, alert-matching, notification and invoice-generation workers.
- Add signed analytics/document/receipt exports and production URL expiry.
- Add normalized media-association validation and database-level PostgreSQL concurrency tests for simultaneous inventory writes.
- Decide/migrate legacy properties without owner availability slots, then remove the compatibility path.
- Deploy to staging and attach sanitized success/error/provider/concurrency fixtures. No staging deployment is claimed here.
