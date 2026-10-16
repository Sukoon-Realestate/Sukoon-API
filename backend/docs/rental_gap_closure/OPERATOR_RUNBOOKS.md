# Rental operations: roles and runbooks

Case routes are documented in [API_CONTRACT.md](API_CONTRACT.md). Start with a fresh scoped GET and use a UUID request key plus the current revision for each command. Retain the key after an unknown result. Never edit financial/consent/allocation status directly in Django admin. Audit records preserve actor, target, revision, reason and relevant metadata.

## Roles

| Role | Allowed responsibility | Boundary |
|---|---|---|
| support / dispute_resolver | Support-team case assignment, triage, responses, resolution consistent with actual domain state | No payment/refund/payout execution or finance-case access by role alone |
| psp_reconciliation | Finance-team payment/reference investigation, case assignment and remedy links | Unknown outcome cannot be resolved as success or no-action solely from elapsed time |
| financial_approver / refund_operator | Existing refund approval workflow and finance cases | Case text never executes a refund |
| payout_operator | Existing payout workflow and finance cases | Beneficiary snapshot and eligible reserved balance are checked before dispatch |
| kyc_reviewer | Identity claims tied to approved KYC | Does not grant property authority |
| property_reviewer | Authority/property-fact claims tied to current property review | Does not grant identity or financial permissions |
| participant | Own case and agreement/hold access, replies, owned clean evidence | Cannot assign, triage, resolve or link a financial remedy |

Superuser is an explicit administrative override. Ordinary staff require an active StaffProfile role. Separate Django model-view permissions govern read-only admin history. Production needs named people and coverage; this delivery assigns no real staff.

## Ten procedures

1. **Checkout unknown.** Find the original attempt, session and reference. Assign a finance case and query the provider by that identity. Preserve the attempt/allocation while unknown; never create a replacement charge to test the outcome. Apply only an authenticated provider outcome. Missing live lookup support is a deployment blocker.
2. **Late capture after release.** Record the actual capture and inspect the activation-review case. Confirm that another allocation was not overwritten. Determine the approved refund/remedy; link its existing RefundRequest to the case. Resolve as refund_executed only when that refund is succeeded. No automatic compensation transport is available in production.
3. **Owner cannot provide access.** Open access_failure/move_in_mismatch against the agreement, retain selection/terms baseline and both parties' evidence, assign support and contact the owner. Do not mark possession accepted or payout released from a support reply. An alternative room requires new explicit selection/terms consent.
4. **Tenant no-show or disputed condition.** Record the actual handover/condition status and participant evidence. Use waiting_for_tenant/owner with a next action and due time. Silence is not an explicit inspection or acceptance. Escalate unresolved facts; do not invent a guaranteed refund.
5. **Owner cancellation.** Use the existing cancellation/change command after checking current signature, payment and occupancy state. Unknown payment blocks destructive inventory release. Explain the agreed remedy, link actual financial records, and preserve the original agreement and consent history.
6. **Refund failure/unknown.** Inspect the approved refund allocation and original provider instruction. Reconcile the same reference before retry. Check reserved remaining rent/deposit components and any in-flight payout. A support case may link the refund but cannot substitute for executed financial postings.
7. **Beneficiary/payout failure.** Compare the approved payout's beneficiary/profile revision with the current profile and provider status. Stop on change/restriction; never substitute new account details into an existing instruction. Keep the payable obligation and reconcile unknown payouts. Reapproval/cancellation for a changed beneficiary needs an explicit reviewed domain procedure; direct admin editing is disallowed.
8. **Incomplete group.** Read proposal roster/digest and each participant's own consent/agreement. A coordinator cannot consent for another member. Preserve independent completed agreements when another participant declines. Conditional bundles and automatic cost redistribution are disabled; never promise all-or-nothing completion.
9. **Overstay/inventory conflict.** Review the canonical physical units, all date rows, current possession and any applied renewal. Do not delete legacy conflicts to make a new request pass. Run the report-only inventory command, resolve actual occupancy/mapping through the proper domain workflow, then re-audit. Structural edits remain blocked while allocations exist.
10. **Verification dispute or missed case deadline.** Assign the appropriate reviewer for the actual claim scope; revoke a claim with a reason and current revision when review no longer supports it. The deadline job escalates an overdue unresolved case once, retains the responsible team and next action, and notifies an assignee where configured. Check unassigned escalations actively; the software does not invent staffing coverage.

## Financial case completion

Use actions assign, triage, reply, link_remedy, resolve or reopen as permitted. `refund_executed` requires a linked succeeded refund; `payout_executed` requires a linked paid payout. An unresolved payment, unexecuted remedy or unlinked late-capture remedy prevents resolution. Case status cannot change payment truth. Reply history is visible to authorized participants; private evidence is retrieved only through existing protected evidence endpoints.

## Monitoring and handoff

Track counts/age of unprocessed PlanningEvent and ProviderWebhookEvent records; active unknown attempts; overdue/escalated/unassigned cases; inventory backfill conflicts; provider instructions in unknown/retry states; and held payouts/refunds. Correlate API requests through X-Correlation-ID plus operation receipt/reference and domain UUID. Never export tokens, document bytes, full beneficiary accounts or unrelated application profiles into support logs. This delivery provides domain audit records and runbooks, not a deployed monitoring dashboard or live alert service.
