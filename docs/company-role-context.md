# Company role context

Company HTTP reads and commands use one current role per request. Membership,
mandates and resource assignments remain authoritative; headers never grant a
role or permit self-approval.

1. `GET /api/v1/features/v1/companies/` returns discovery identities only.
2. `GET /api/v1/features/v1/companies/{id}/role-contexts/` returns currently
   available roles for the authenticated member.
3. Protected requests send both `X-Sukoon-Company-Id: {id}` and
   `X-Sukoon-Company-Role: admin|coordinator|approver|signer|payer|employee`.

The middleware establishes a context even when no headers are present. Missing,
revoked or mismatched contexts cannot restore the historical broad company
payload. Owner and platform authority remain independent outside a company role.

| Role | Scope |
| --- | --- |
| admin | Members, mandates, approval configuration and responsibility assignments |
| coordinator | Assigned requests, visits, required commercial terms and housing operations |
| approver | Assigned decisions and their necessary budget context |
| signer | Assigned original agreements, signatures and contractual changes |
| payer | Invoices, settlements and explicitly identified payment-basis summaries |
| employee | Own housing, consent, arrival, departure and maintenance |

`role_projections.py` restricts response fields as well as commands. Shared lease,
invoice, private-document, evidence, case and recovery endpoints apply the same
boundary. Mixed historical discussions are unavailable without a verified role
audience. A PDF original is never modified to produce a role summary.

Role work is exposed by `companies/{id}/role-work/?section=...` over the existing
canonical records. Administrative delegation uses
`companies/{id}/responsibility-assignments/` and its item actions. Its projection
contains people and responsibility metadata, never the contract or ledger. New
delegates and an independent reviewer retain their existing consent duties.

Notification destinations bind company, role and resource. Device copy is
generic; opening the destination revalidates authority. Counters and inboxes
exclude other roles and unbound legacy content. Internal event discovery uses
an explicit system context without changing HTTP permissions.

Mutation receipts confirm identity and revision. Replaying an older company
receipt never returns its historical broad projection. Unknown operations remain
unknown until reconciled; this change does not retry or mark them successful.

Focused regression coverage is in `test_company_role_contexts.py`,
`test_company_responsibility_management.py`, `test_request_counts.py` and the
existing company tenancy, preparation, continuation and recovery tests. Run
concurrency checks on PostgreSQL. Local tests do not certify deployment, provider
delivery or device behavior.
