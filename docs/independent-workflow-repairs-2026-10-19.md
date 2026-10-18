# Independent workflow repairs: 19 October 2026

This release carries the previously locally verified repairs that do not require
the pending identity-assurance or document-schema migrations. It does not run
historical reconciliation, change approved fees, enable a provider, or open a
recovery scope.

The included changes:

- Retire the legacy cross-user identity directory and reject sensitive identity
  edits through its old profile editor.
- Recheck current administrative and private servicing authority; preserve
  independent decisions and reject access after explicit revocation.
- Serialize recoverable property/support writes with their original operation
  identities. A fenced absent operation cannot execute later.
- Clear stale listing approval after edits and preserve hidden publication state.
- Validate amendment/renewal terms before consent and signing; preserve signed
  invalid history for operational review; carry exact signing provenance into
  renewed leases.
- Enforce supported deposit custody, billing anniversaries and settlement
  prerequisites without inventing a new financial remedy.
- Return actual rental next steps, timeline, billing periods and original
  payment-attempt information.
- Classify legacy leases by their real stage. The reconciliation command remains
  a dry run unless explicitly applied; this release does not execute it.

Validation used an isolated snapshot of `ef88311` plus the 43 explicitly selected
source/test files: 129 PostgreSQL tests passed. Coverage includes changed terms,
private changes, disputes, rental contracts, legacy classification, connected
HTTP flow, planning completion, phase-five servicing, profile privacy, property
visibility, owner property screens, support recovery, and both upstream Paymob
callback and sandbox-checkout suites. Provider calls in those local tests remain
mocked; this is not evidence of real money movement or signature-provider use.

Deferred work remains in the working tree: identity cutover, document schema and
private artifact generation, direct-chat uniqueness migration, and the broader
administrative UI/authority cohort. Deploying this release does not establish
that those separate changes are deployed. No database migration is introduced
by this release, and unrelated work is preserved.
