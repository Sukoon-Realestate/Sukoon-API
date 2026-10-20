# Platform-only rent collection and reminders

Current source contract, 20 October 2026. This increment does not enable a
payment provider, create hosted workers, or approve new financial consequences.

## Collection and historical records

New or explicitly reviewed agreement terms include
`payment_collection: {"mode": "platform_only", "version": "sokoun-collection-v1"}`.
Executed agreement snapshots are not rewritten. Invoice amounts, payment
allocation, custody, refunds and payout authority retain their existing rules.

New `external_payment` commands, including
`POST /api/v1/features/v1/rent-invoices/{id}/external-payment-claims/`, return
HTTP 409 with `code=external_payment_not_supported` for an authorized reader,
or HTTP 404 for an unauthorized/revoked reader. The response provides a typed
`support_context`. Historical claims retain their authorized read and review
path; acceptance does not create platform payment allocation.

## Private payment reports

The existing support creation endpoint accepts `rental_context.issue_code`
only for category `payment`:

- `off_platform_request`: someone requested payment outside Sokoun.
- `off_platform_payment`: the reporter says such payment already occurred.

`lease_id`, `invoice_id`, and `payment_attempt_id`, when present, must identify
their declared record types, be accessible to this user, and belong to one
lease. `case_id` is server-owned and is rejected in input. Existing support
request identity/recovery remains authoritative after an unknown response.

Creation atomically links a finance `off_platform_payment_report` case.
Narrative and attachment URLs remain in the private ticket. Other contract
parties and employees do not inherit report access. An independent assigned
finance operator can open that ticket through the case's admin link and read
its private evidence; this does not grant general support editing rights.

Case review can be assigned, triaged, replied to, resolved and reopened using
the existing versioned case commands. `link_remedy` is rejected. Resolution
uses `no_action_required` with an explanation of the **report review** outcome,
never a certification of payment or refund. Closing/reopening synchronizes
the ticket and creates a private update event. No ledger, invoice balance,
custody or payout mutation follows from a report.

## Reminder contract

- Eligible unpaid rent invoice, positive canonical balance, nonlegacy lease,
  future effective deadline: `max(due_at, deferred_until)`.
- Recurring invoice: opens at **09:00 Africa/Cairo**, **three civil days**
  before that deadline. A delayed job catches up only before the deadline.
- First billing period (`sequence=1`): invoice-issued event, preserving the
  existing 48-hour initial-payment window.
- Ordinary/student recipient: current active verified tenant without private
  revocation. Company recipients: current execution-authorized payer and the
  assigned active coordinator. One event per person if those roles overlap.
  Missing payer authority produces a responsibility follow-up to the
  coordinator or, when neither recipient is available, active company admins.
  It does not make an employee liable.
- Durable event identity: recipient + invoice + kind + normalized effective
  due timestamp. Approved extensions invalidate stale dispatch and allow one
  event for the changed deadline.
- Current balance, deadline and recipient authority are rechecked at dispatch.
  A pending original payment gets reconciliation guidance, not a new-charge
  instruction. Notification previews omit amounts, address and report content.
- `rent_payments` is an inbox category, not a dedicated preference toggle.
  The existing preference service permits these operational types by default;
  unrelated visit/marketing toggles do not suppress them. Active authenticated
  device binding and OS notification permission still govern push delivery.
  Inbox persistence and external push success are different evidence.

## Operations and rollout

Read-only preview (default; contains private recipient IDs, retain privately):

```sh
python manage.py rent_payment_notifications --dry-run
```

`--execute` deliberately records and dispatches the bounded reminder job. Do
not run it against live users as a diagnostic.

Beat registration uses:

| Schedule | Registered task | Interval |
| --- | --- | --- |
| `rent-payment-notifications` | `core_apps.features.tasks.process_rent_payment_notifications` | 300 seconds |
| `run-rental-billing-cycle` | `core_apps.features.tasks_parts.expire_rental_sources_and_holds.run_rental_billing_cycle` | 300 seconds |

The billing schedule previously used an import alias that did not match
Celery's registered task name. This increment corrects that schedule.
**Before activating hosted beat/workers**, inspect scheduled periods whose
`issue_at` is past: the billing task will issue eligible existing obligations
and mark eligible overdue invoices. It does not capture money. Inspect
reminder candidates and notification preferences before enabling delivery.
Use a dedicated reviewed queue/schedule when older queue contents are unknown.

Other existing split-module schedule names require their own registration
review; this payment increment does not drain or activate those jobs.
Migration `notifications.0010_rent_payment_reminders` adds notification choices;
it does not modify invoice amounts or signed terms.

## Executed local evidence

The payment/report regression selection passed 33 PostgreSQL test cases;
the connected regression run passed 102 cases before the additional admin
reader and anonymous-login tests were added (104 distinct cases across the
final selections).
Tests cover Cairo calendar boundaries, approved extension, paid/revoked
suppression, company roles, concurrent event generation, retries, historical
claim review, private evidence, report recovery and a rendered Django admin
view. The admin test uses ordinary static storage instead of a production
`collectstatic` manifest.

The first deployment smoke check exposed an anonymous-admin-login regression:
the scoped report reader attempted to use `AnonymousUser` in an assignment
query. A new test reproduced that failure. The reader now returns an empty
queryset before any identity query for anonymous/inactive users, and both
anonymous login and assigned-finance admin rendering pass.

Actual isolated Redis/Celery/beat execution created durable inbox reminders.
Actual billing worker execution issued one synthetic period, and its repeat
issued zero; no payment attempt was created. These are local observations,
not hosted worker or provider-delivery evidence. The adjacent app's
`docs/sokoun-business-flows/PLATFORM_RENT_PAYMENTS_AND_REMINDERS.md` records
Flutter, physical-device and deployment evidence separately.
