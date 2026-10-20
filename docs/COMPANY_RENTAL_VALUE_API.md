# Company rental value API

20 October 2026. Additive request metadata, request-linked assistance, CSV preview,
management overview and canonical cost statements. This increment does not enable
company intake, providers, paid workers, legal consent or new financial rules.

All paths below use `/api/v1/features/v1/` and authenticated current authority.
Read responses use `Cache-Control: private, no-store`. The application uses its
existing planning/lifecycle capability checks as well as these server checks.

| Method and route | Contract |
| --- | --- |
| GET `company-requirements/` | `requirements[]` with `value`, existing listing `query_parameter`, localized label. Furnished and existing amenity flags are owner declarations, not inspection or guaranteed inclusion in rent. |
| Existing request create/update | Optional `project_code` max100, paired nullable Decimal(9,6) `worksite_latitude`/`worksite_longitude`, distinct supported `requirements[]` max20. Existing whole-calendar-month validation, full-term rent ceiling, separate deposit, original request key/revision and protected viewing provenance remain. Omitted legacy fields remain compatible. |
| GET `portfolio-offers/` with `company_id`, `request_id` | Current assigned coordinator. Optional `location` max100, `suitable_only=true/false`, `available_only=true/false`, `offer_ids` comma-separated maximum3 UUIDs. Exact-scope filtering precedes pagination. Includes capacity, full-term rent, rental months, current request revision, catalog facts, per-unit straight-line distance, checked time, null listing quote expiry and unestablished other costs. Selection still revalidates canonical inventory and quote. |
| POST `company-housing-requests/{id}/assistance/` | Current assigned coordinator; required reason max4000, `request_key`, `expected_revision`. Returns existing operation receipt plus updated request with `assistance_cases`. One unfinished `company_sourcing` case per request. Concurrent stale command rejected; same original key replays. Existing open case receives additional explanation. No booking, approval, consent or money effect. |
| Existing case action | `recommend_offers` takes `housing_request_revision` and one-to-three `recommended_offer_ids`, plus existing case revision/key/reason. Assigned independent support operator only; source suitability and current coordinator checked. Stores current source revision, enters `waiting_for_company`. Current coordinator can `withdraw_sourcing`. Only `recommendations_delivered` against current recommendations or `no_suitable_offer` resolve through operator action. Closed sourcing cannot reopen or manufacture a financial remedy. |
| POST `companies/{id}/staff-batches/import-preview/` | Current administrator; `csv_text`, UTF-8 maximum200000 bytes, maximum50 rows. Required headers display_name/work_email; optional employee_code/mobile/job_title/department/project_code. Unknown/duplicate headers, privileged role columns and malformed CSV fail. Per-row duplicate/field errors remain editable. Returns row keys/values/messages/valid, `persisted=false`, `activation_sent=false`; roles employee-only. Existing staff-batch confirmation and partial recovery remain authoritative. |
| GET `companies/{id}/rental-summary/` | Current membership; existing tenancy access scopes housing and employee rows. Commercial roles see authorized capacity/project data. Employees see only their own assignments and no company capacity. Active acknowledged arrival address survives recorded physical arrival but is withheld after return. Read-time 30-day/end-overdue attention leaves physical/financial obligations unchanged. |
| GET `companies/{id}/housing-report/` | Current membership and commercial tenancy authorization. Optional project_code/cost_center max100, tenancy_id, civil `from`/exclusive `until`, `export=csv`. Separate budget reservation, billing-period contract rent, invoice, gross capture/allocation, external payment and current deposit custody rows. Null remains unknown; no grand total. Period overlap does not prorate monthly rent. Formula-like CSV text is escaped. Preview/report throttle30/min. |

The case queue, assignment, replies, durable event and existing delivery/worker
infrastructure are reused. An operational response target does not promise a
property, imply approval, or create a contractual deadline. Removed coordinators
lose case access; source edits invalidate recommendation IDs. Django admin shows
current source requirements and original reason and uses the same case command
service as the API.

Normal HTTP summaries/reports use a read-only PostgreSQL repeatable-read
transaction, including authorization and all constituent queries. An explicit
outer transaction owns its isolation. Timestamp dates use Africa/Cairo. Reports
are management statements, not tax invoices, account balances or payment orders.
Payment rows retain mock-provider markers and gross/allocation distinctions.

Migration `features.0061_company_rental_value` adds request metadata, nullable
PROTECT case/request reference and `one_open_company_sourcing` partial uniqueness.
It has no data backfill of consent or money and no worker/provider activation.
Older request bodies remain accepted. Clients must retain current request/case
revisions and reconcile the original operation after an unknown response.

Focused regression sources:

- `backend/core_apps/features/tests/test_company_rental_value.py`
- `backend/core_apps/features/tests/test_company_rental_value_reports.py`
- Existing request-correction, staff-batch and company-service tests.

Fixtures are synthetic and signing/payment prerequisites use the explicitly fake
adapter. Local tests, native Android observations, deployed API source and real
provider operation are separate evidence levels.

## Deployment verification

The 20 October deployment initially served the new source before migration
`features.0061_company_rental_value` had been applied. Platform health remained
green, while authenticated company-request and operational-case admin lists
returned HTTP 500 because the added columns were absent.

The live migration graph was inspected and contained only this forward migration.
Its source hash matched the reviewed migration. It was applied with bounded
database lock/statement timeouts. The two affected tables had zero rows before
and after the update. Both authenticated admin lists then returned HTTP 200.
No contract, financial, consent, provider or worker configuration was changed.

For a schema-changing release, verify the migration plan and apply the reviewed
schema through the authorized deployment process before accepting the release.
Do not treat a healthy container or `/health/` response as evidence that migrations
or private workflows work. The existing web Procfile does not run migrations.
Check an authenticated affected list/action as well as anonymous access denial.
An empty operator list confirms the query path; it does not establish a real
customer case or provider completion.
