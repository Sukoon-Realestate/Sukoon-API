# Company review and handover recovery

`POST /api/v1/features/v1/company-tenancies/{id}/resolve-operation/`
accepts the original `request_key` and `action` (`review` or `handover`).
A review also requires its original `role` (`owner` or `signer`). The current
company context and exact resource assignment are checked again. The owner uses
their independent authority. Other actions, including signing and payments, are
not supported by this endpoint.

This is an explicit recovery command. It never submits the original intention.
It acquires the actor lock before the company, inventory and lease locks, in the
same order as the original company command. If the original committed first, it
returns its minimal receipt. If no original receipt exists, it records
`absent_final` under that actor, operation and key. A delayed original request is
then rejected by the existing command replay fence. A lost recovery response can
be inspected through `GET rental-operations/{request_key}/?subject_id={id}`.

The response contains `request_key`, `request_subject_id`, `status` and
`operation_receipt`, with no historical contract or financial projection. Keys
already used for a different subject or action are rejected. Lease revisions,
reviews, handovers and payment state are not changed by closing an unexecuted
reference. Expired drafts remain eligible for recovery under current authority;
expiry never authorizes another review on stale terms.

The app reads only the relevant protected review/handover draft identities on
the authorized tenancy detail. Legacy drafts contribute only an unresolved
request reference. A lookup returning `unknown` keeps the reference protected.
Closing it requires the explicit recovery control, and local cleanup requires
an exact confirmed or permanently absent receipt. Account/role changes discard
late results. No automatic retry of the original business action is performed.
