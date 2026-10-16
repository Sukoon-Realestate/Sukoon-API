# Rental gap closure backend delivery

This backend extends the existing rental domain. Production money/signing adapters remain unavailable; all recorded provider tests used the deterministic fake provider in an isolated local environment.

- [API and recovery contract](API_CONTRACT.md), [generated OpenAPI slice](openapi.json), [actual synthetic HTTP responses](django_contract.json).
- [Migration, policy, workers and provider setup](SETUP.md).
- [Physical allocation decision](ADR_PHYSICAL_ALLOCATION.md).
- [Roles and ten operator runbooks](OPERATOR_RUNBOOKS.md).
- [Cross-repository implementation report](../../../../darak-app/docs/verification/rental_gap_closure/README.md), [verification](../../../../darak-app/docs/verification/rental_gap_closure/VERIFICATION.md), and [T01–T90 matrix](../../../../darak-app/docs/verification/rental_gap_closure/ACCEPTANCE_MATRIX.md).

Migrations: features 0021, 0022, 0023. New commands: configure_rental_lifecycle_policy and reconcile_rental_inventory, both dry-run by default. No remote migration or deployment was performed.
